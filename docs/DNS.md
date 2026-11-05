# DNS: agenticstack.cl y theagenticstack.cl

Ambos dominios están registrados en **NIC Chile**, que no guarda registros DNS: solo delega en los **servidores DNS** que le indiques. Usamos **Cloudflare (plan gratuito)** como DNS de los dos dominios:

- `agenticstack.cl` → GitHub Pages (registros en modo _DNS only_, para que GitHub emita el certificado HTTPS).
- `theagenticstack.cl` → redirección 301 a `https://agenticstack.cl` con una regla de Cloudflare (registros _proxied_).

El script `scripts/dns/setup.py` hace todo lo de Cloudflare y de GitHub Pages por API. Los pasos en NIC Chile y la verificación del dominio en la organización de GitHub son manuales (no tienen API).

## Paso a paso

### 1. GitHub: pedir el TXT de verificación (manual, 2 min)

Evita que otra cuenta de GitHub tome el dominio ([docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages)).

1. https://github.com/organizations/agentic-stack-cl/settings/pages → **Add a domain** → `agenticstack.cl`.
2. Copia el **valor** del TXT que muestra GitHub (el nombre es `_github-pages-challenge-agentic-stack-cl.agenticstack.cl`). **No** presiones _Verify_ todavía.

### 2. Cloudflare: crear las zonas y un token limitado a ellas (manual, 5 min)

Recomendado: creas tú las dos zonas y el token solo puede tocar esas dos (mínimo privilegio).

1. https://dash.cloudflare.com → **Add a domain** → `agenticstack.cl` → plan **Free**. Si ofrece importar registros, no hace falta (el dominio no tiene ninguno). Repite con `theagenticstack.cl`. Las zonas quedan en estado _pending_ hasta el paso 4.
2. https://dash.cloudflare.com/profile/api-tokens → **Create Token** → **Create Custom Token**.
3. Nombre: `agenticstack-dns`. Permisos:

   | Tipo | Recurso         | Permiso |
   | ---- | --------------- | ------- |
   | Zone | Zone            | Read    |
   | Zone | DNS             | Edit    |
   | Zone | Single Redirect | Edit    |

4. **Zone Resources**: _Include → Specific zone → `agenticstack.cl`_ y agrega otra fila _Include → Specific zone → `theagenticstack.cl`_.
5. **TTL**: una fecha de término cercana (p. ej. en 7 días). Crea el token y cópialo.

> Alternativa: que el script cree las zonas. Entonces el token necesita **Zone · Zone · Edit** con _Zone Resources → All zones from an account_, y debes definir `CLOUDFLARE_ACCOUNT_ID` (Dashboard → inicio de la cuenta → columna derecha). Da acceso a todas las zonas de la cuenta; úsalo solo si la cuenta es exclusiva de la comunidad.

### 3. Cloudflare: crear zonas, registros y redirección (script)

En la raíz del repo, en tu terminal (el token no queda en el historial ni se imprime):

```bash
read -rs CLOUDFLARE_API_TOKEN && export CLOUDFLARE_API_TOKEN
```

Revisa qué hará (solo lectura) y luego aplícalo:

```bash
python3 scripts/dns/setup.py plan --github-txt <valor-del-paso-1>
```

```bash
python3 scripts/dns/setup.py apply --github-txt <valor-del-paso-1>
```

Al terminar imprime los **dos servidores DNS** asignados por Cloudflare para cada dominio (normalmente el mismo par para ambos). Es idempotente: puedes volver a ejecutarlo sin duplicar nada. Si algún registro antiguo choca en `@` o `www`, lo muestra con `!` y se borra solo si agregas `--prune`.

### 4. NIC Chile: delegar en Cloudflare (manual, 5 min)

Para **cada** dominio: https://clientes.nic.cl → _Mis dominios_ → el dominio → _Configuración técnica_ → **Servidores DNS** → reemplaza por los dos servidores que imprimió el script → guardar.

> Si el dominio tuviera DNSSEC activo en NIC Chile (registro DS), hay que quitarlo antes de cambiar los servidores. El script lo revisa y avisa; al momento de escribir esto, ninguno de los dos tiene DS ni servidores configurados.

### 5. Esperar la propagación (minutos a algunas horas)

```bash
python3 scripts/dns/setup.py status --activation-check
```

Repite hasta que `A agenticstack.cl` aparezca con ✅ y las zonas digan `active`. Con el token de solo lectura de zona, `--activation-check` puede no tener permiso; no importa: Cloudflare revisa solo cada cierto tiempo. `status` funciona también sin token (solo DNS público y Pages).

### 6. GitHub: verificar el dominio (manual, 1 min)

Cuando `status` muestre el TXT, vuelve a la página del paso 1 y presiona **Verify**.

### 7. GitHub Pages: activar dominio y HTTPS (script)

```bash
python3 scripts/dns/setup.py github
```

Configura `agenticstack.cl` como dominio del repo, espera el certificado (hasta 20 minutos; `--wait` cambia el límite) y fuerza HTTPS. Si el certificado tarda más, vuelve a ejecutarlo más tarde.

### 8. Comprobar y cerrar

```bash
curl -sI https://agenticstack.cl | head -1
```

```bash
curl -sI https://theagenticstack.cl/radar | grep -i location
```

El primero debe responder `HTTP/2 200` y el segundo `location: https://agenticstack.cl/radar`. Después **revoca el token** en Cloudflare (o deja que expire).

## Referencia: registros que crea el script

`agenticstack.cl` (todos _DNS only_):

| Tipo  | Nombre                                     | Valor                        |
| ----- | ------------------------------------------ | ---------------------------- |
| A     | `@`                                        | `185.199.108.153`            |
| A     | `@`                                        | `185.199.109.153`            |
| A     | `@`                                        | `185.199.110.153`            |
| A     | `@`                                        | `185.199.111.153`            |
| AAAA  | `@`                                        | `2606:50c0:8000::153`        |
| AAAA  | `@`                                        | `2606:50c0:8001::153`        |
| AAAA  | `@`                                        | `2606:50c0:8002::153`        |
| AAAA  | `@`                                        | `2606:50c0:8003::153`        |
| CNAME | `www`                                      | `agentic-stack-cl.github.io` |
| TXT   | `_github-pages-challenge-agentic-stack-cl` | valor entregado por GitHub   |

Valores oficiales de [GitHub Pages](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site). No uses registros comodín (`*`).

`theagenticstack.cl` (_proxied_):

| Tipo | Nombre | Valor       | Para qué                                                      |
| ---- | ------ | ----------- | ------------------------------------------------------------- |
| A    | `@`    | `192.0.2.1` | IP de documentación: Cloudflare responde antes de llegar ahí. |
| A    | `www`  | `192.0.2.1` | Ídem.                                                         |

Regla de redirección (fase `http_request_dynamic_redirect`): si el host es `theagenticstack.cl` o `www.theagenticstack.cl`, responde **301** a `concat("https://agenticstack.cl", http.request.uri.path)` conservando la query string.

## Notas

- Los registros de `agenticstack.cl` deben quedar en _DNS only_ (nube gris). Si se proxifican, GitHub no puede emitir el certificado.
- El archivo `public/CNAME` contiene `agenticstack.cl`; con despliegue por Actions GitHub usa el dominio configurado en Settings (lo hace el paso 7).
- Las zonas quedan en la cuenta de Cloudflare de quien ejecute el script. Si más adelante la comunidad tiene su propia cuenta, se puede mover: se agrega la zona en la cuenta nueva y se cambian los servidores en NIC Chile.
- Sin Cloudflare: los mismos registros sirven en cualquier DNS; la redirección de `theagenticstack.cl` puede hacerse con la redirección web gratuita de NIC Chile (verifica que soporte `https://`).

# Pipeline radar ↔ Discord

El radar se actualiza solo a partir del foro **#radar** de Discord. No hay bot residente: un job programado de GitHub Actions lee el foro una vez al día y abre un pull request.

```
Foro #radar (Discord)
  └─ hilo = blip · tag = cuadrante · reacciones del 1er mensaje = votos
        │  (API REST, token de bot, solo lectura)
        ▼
.github/workflows/radar-sync.yml  (cron diario 08:00 CLT + manual)
  └─ scripts/radar/sync.py → src/data/radar.json
        │
        ├─ PR "radar: sincronización con el foro de Discord" (rama radar/sync)
        │     └─ CI (build) + revisión humana (radar-curator) → merge → deploy
        └─ scripts/radar/notify.py → webhook de Discord (si hubo cambios de anillo)
```

## Reglas de votación

| Elemento                  | Significado                                                                                                                                          |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hilo del foro             | Un blip. El título del hilo es el nombre.                                                                                                            |
| Tag del hilo              | Cuadrante: `Técnicas y patrones`, `Frameworks y SDKs`, `Herramientas y protocolos`, `Modelos y plataformas`. Hilos sin uno de estos tags se ignoran. |
| Reacciones al 1er mensaje | 🟢 Adoptar · 🔵 Probar · 🟡 Evaluar · 🔴 Esperar. Otras reacciones no cuentan.                                                                       |
| Quórum                    | Mínimo de votos para que el hilo cuente (variable `RADAR_QUORUM`, por defecto 5).                                                                    |
| Mayoría                   | Gana el anillo con más votos. Empate → el más conservador (externo).                                                                                 |

Qué hace el sync con cada hilo con quórum:

- **Hilo nuevo** → blip nuevo con `moved: 2`, `status: "votado"`, descripción = primer párrafo del mensaje (el curador puede mejorarla en el PR).
- **Hilo conocido** (por `threadId`) o **blip sembrado con el mismo nombre** → se vincula al hilo, se marca `votado` y, si el anillo cambió, `moved: ±1` y `date` = hoy.
- Los indicadores `moved` vuelven a `0` a los 90 días.
- Nunca borra blips: sacar un ítem del radar es una decisión humana en un PR.

## Activar la conexión real

1. **Crear la app/bot** en el [Discord Developer Portal](https://discord.com/developers/applications):
   - Bot → _Reset Token_ y guárdalo.
   - Bot → _Privileged Gateway Intents_ → activa **Message Content Intent** (para leer el texto del primer mensaje; sin esto las descripciones de blips nuevos quedan genéricas).
2. **Invitar el bot** al servidor con OAuth2 → URL Generator: scope `bot`, permisos **View Channels** y **Read Message History**. No necesita escribir.
3. **Crear el foro** `#radar` con los cuatro tags de cuadrante (nombres de la tabla de arriba).
4. **Copiar el id del foro**: Discord → Ajustes → Avanzado → Modo desarrollador; clic derecho en el canal → _Copiar ID_.
5. **Crear un webhook** (opcional) en el canal donde se anuncian los cambios: Editar canal → Integraciones → Webhooks.
6. **Cargar los secrets** en GitHub (`Settings → Secrets and variables → Actions`):

   ```bash
   gh secret set DISCORD_TOKEN -R agentic-stack-cl/web
   gh secret set FORUM_CHANNEL_ID -R agentic-stack-cl/web
   gh secret set DISCORD_WEBHOOK_URL -R agentic-stack-cl/web
   gh variable set RADAR_QUORUM -R agentic-stack-cl/web --body 5   # opcional
   ```

7. **Probar**: Actions → _Radar ↔ Discord_ → _Run workflow_ con `dry_run` activado. El resumen del job muestra qué cambiaría.

Mientras falten los secrets, el workflow termina en verde con un aviso y no hace nada.

## Requisitos del repositorio

- `Settings → Actions → General → Workflow permissions` → **Allow GitHub Actions to create and approve pull requests** (necesario para que el job abra el PR).
- Los PR abiertos con `GITHUB_TOKEN` no disparan workflows `pull_request`. Por eso el job lanza `ci.yml` con `workflow_dispatch` sobre la rama `radar/sync`: el check `build` queda asociado al commit del PR y el ruleset de `main` lo reconoce. Si algún día se prefiere, se puede reemplazar por un token de GitHub App.

## Desarrollo local

```bash
# simular contra el fixture (sin red, sin escribir)
python3 scripts/radar/sync.py --fixture scripts/radar/fixtures/forum.json --dry-run

# ver el mensaje que se publicaría en Discord
python3 scripts/radar/sync.py --fixture scripts/radar/fixtures/forum.json --dry-run --changes-out /tmp/c.json
python3 scripts/radar/notify.py --changes /tmp/c.json --dry-run

# resumen semanal a partir del historial de git
python3 scripts/radar/digest.py --since "7 days ago" --format discord

npm run test:py   # tests (pytest vía uvx)
```

El fixture `scripts/radar/fixtures/forum.json` tiene la misma forma que las respuestas de la API de Discord v10 y cubre: adopción de un blip sembrado, subida, bajada por empate, hilo nuevo, hilo bajo quórum, hilo sin tag de cuadrante y un hilo de otro canal. Los tests lo aplican sobre `scripts/radar/fixtures/radar-base.json`, una copia fija del radar que no cambia con los votos.

## Archivos

| Archivo                     | Qué hace                                                   |
| --------------------------- | ---------------------------------------------------------- |
| `scripts/radar/radar.py`    | Constantes, validación, diff y formato de mensajes         |
| `scripts/radar/sync.py`     | Lee el foro (API o fixture), calcula anillos, escribe JSON |
| `scripts/radar/notify.py`   | Publica el resumen por webhook                             |
| `scripts/radar/digest.py`   | Cambios desde una fecha según git (skill `/weekly-digest`) |
| `scripts/radar/validate.py` | Valida `radar.json` (hooks, CI, `npm run radar:validate`)  |

# Definition of Ready: issues preparados para desarrollar

Un issue está **ready** (preparado) cuando una persona **o un agente** puede desarrollarlo de principio a fin sin preguntar nada más. Esta guía define la información mínima que eso requiere y cómo se marca.

> Resumen: 8 secciones obligatorias, sin decisiones abiertas, un label de área, que quepa en un PR → label `ready`.

## Por qué

- **Para agentes**: un issue asignado a un agente funciona como su prompt. La guía de GitHub para agentes de código recomienda tareas acotadas, con el problema bien descrito y pistas de dónde está el código.
- **Para personas**: es la práctica de _Definition of Ready_ de los equipos ágiles, basada en INVEST (independiente, negociable, valiosa, estimable, pequeña, testeable): criterios de aceptación verificables, dependencias identificadas y tamaño acotado antes de empezar.

## Estructura mínima

Usa la plantilla **Tarea de desarrollo** (`.github/ISSUE_TEMPLATE/tarea.yml`), que ya trae estas secciones. Se aceptan títulos `##` o `###`.

| Sección                     | Qué debe decir                                                                                    | Pregunta que responde   |
| --------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------- |
| **Contexto**                | El problema actual, a quién afecta y por qué vale la pena.                                        | ¿Por qué?               |
| **Objetivo**                | Qué cambia cuando esté hecho, en 1–2 frases, desde quien usa el sitio o repo.                     | ¿Qué?                   |
| **Alcance**                 | Lista de lo que incluye.                                                                          | ¿Hasta dónde?           |
| **Fuera de alcance**        | Lo que **no** se hace aquí. "Nada en particular" si no aplica.                                    | ¿Dónde parar?           |
| **Criterios de aceptación** | Casillas `- [ ]` verificables: resultados observables, casos borde, lo que no debe romperse.      | ¿Cuándo está terminado? |
| **Cómo verificar**          | Comandos, páginas y pasos manuales para comprobar cada criterio.                                  | ¿Cómo lo compruebo?     |
| **Pistas técnicas**         | Archivos, componentes o scripts relevantes; patrones a seguir; librerías sugeridas o descartadas. | ¿Por dónde empiezo?     |
| **Dependencias**            | Issues, PRs, secrets o decisiones previas (con `#número`). "Ninguna" si no hay.                   | ¿Qué me puede bloquear? |

Opcional pero vigilada:

| Sección                 | Regla                                                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Decisiones abiertas** | Si existe, todas deben estar resueltas: `- [x] pregunta → respuesta`, tachadas (`~~...~~`) o "Ninguna". Una sola pendiente = no está ready. |

Además:

- **Un label de área**: `web`, `radar`, `post`, `infra` o `agentic`.
- **Sin el label `idea`**: las ideas primero se aceptan y pasan a Backlog (ver [CONTRIBUTING](../CONTRIBUTING.md)).
- **Cabe en un PR**: si los criterios de aceptación pasan de ~8 o tocan áreas sin relación, divídelo.

Equivalencias aceptadas en títulos (para issues antiguos): "Por qué" = Contexto, "Qué" = Objetivo, "Alcance propuesto" = Alcance, "Notas técnicas" = Pistas técnicas, "Bloqueos" = Dependencias.

### Buenos criterios de aceptación

| ❌ Vago             | ✅ Verificable                                                                |
| ------------------- | ----------------------------------------------------------------------------- |
| "Que funcione bien" | `- [ ] /eventos lista los eventos futuros ordenados por fecha ascendente`     |
| "Que sea accesible" | `- [ ] El buscador se usa solo con teclado y anuncia el número de resultados` |
| "Tests"             | `- [ ] Tests en scripts/radar/tests/ para --changes-out con y sin cambios`    |
| —                   | `- [ ] npm run check, npm run build y npm run links pasan`                    |

## El label `ready`

| Etapa del tablero | Label       | Significado                                       |
| ----------------- | ----------- | ------------------------------------------------- |
| Ideas             | `idea`      | Propuesta sin compromiso. Puede estar incompleta. |
| Backlog           | —           | Aceptado, pero quizás le falta información.       |
| Backlog/Siguiente | **`ready`** | Cumple esta guía: se puede tomar y desarrollar.   |

- Lo pone quien completa el issue (persona o agente con la skill `/issue-ready`, siempre con confirmación humana).
- El workflow `.github/workflows/issue-ready.yml` valida cada vez que se pone el label o se edita un issue con él. Si falta algo, **quita el label y comenta qué falta**.
- Solo se toman para desarrollo issues con `ready`.

## Cómo se aplica en el flujo agéntico

| Pieza                                             | Qué hace                                                                                                                                               |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `scripts/issues/check_ready.py`                   | Validador único de esta guía. `python3 scripts/issues/check_ready.py --issue 42`                                                                       |
| Hook `UserPromptSubmit` (`.claude/settings.json`) | Si mencionas un issue (`#42`, "issue 42" o su URL) y no está ready, Claude recibe la lista de lo que falta y tú ves un aviso. No bloquea.              |
| `CLAUDE.md`                                       | Regla: no implementar issues sin `ready`; explicar qué falta y ofrecer `/issue-ready`.                                                                 |
| Skill `/issue-ready <n>`                          | Revisa el issue, investiga el repo para completar las pistas técnicas, redacta lo que falta y, con tu confirmación, actualiza el issue y pone `ready`. |
| Skill `/implement-issue <n>`                      | Desarrolla un issue `ready`: rama, plan desde los criterios, implementación, verificación y PR con `Closes #n`. Se detiene si el issue no está ready.  |
| Workflow `issue-ready.yml`                        | Garantiza en GitHub que el label `ready` siempre signifique lo mismo.                                                                                  |

## Ejemplo mínimo

```markdown
### Contexto

Los enlaces a posts compartidos en LinkedIn y Discord se ven sin imagen.

### Objetivo

Cada post tiene una imagen Open Graph con su título y el logo.

### Alcance

- Generar al compilar una imagen 1200×630 por post
- Usarla en las meta etiquetas og:image y twitter:image

### Fuera de alcance

- Imágenes para ítems del radar (#25)

### Criterios de aceptación

- [ ] Cada post publicado tiene /og/blog/<slug>.png
- [ ] El HTML del post apunta a esa imagen en og:image
- [ ] Los borradores no generan imagen
- [ ] npm run check, build y links pasan

### Cómo verificar

npm run build && ls dist/og/blog/ ; abrir el HTML de un post y revisar og:image.

### Pistas técnicas

src/layouts/BaseLayout.astro (prop image), src/pages/blog/[...slug].astro.
Generar con un endpoint estático src/pages/og/blog/[slug].png.ts. Fuente: @fontsource-variable/inter.

### Dependencias

Logo en public/brand/ (#15). Sin logo, usar solo el nombre en texto.

### Decisiones abiertas

- [x] ¿satori o astro-og-canvas? → satori
```

## Referencias

- GitHub Docs, [Best practices for using Copilot to work on tasks](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks).
- Bill Wake (2003), criterios INVEST; checklist de ejemplo en [Rework: Definition of Ready](https://resources.rework.com/libraries/project-management/definition-of-ready).
- Ejemplo de DoR de equipo: [Altinn Studio](https://docs.altinn.studio/en/community/devops/definition-of-ready/).

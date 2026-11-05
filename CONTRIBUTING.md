# Cómo contribuir

¡Gracias por sumarte! Este repo es el sitio de **The Agentic Stack** (https://agenticstack.cl). Puedes contribuir con posts, ítems del radar o mejoras al sitio. Todo entra por pull request a `main` y lo revisa al menos una persona.

Antes de empezar, lee el [código de conducta](CODE_OF_CONDUCT.md).

## Preparar tu entorno

Necesitas Node 22.12+ (recomendado 24) y, si tocas el pipeline del radar, [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:agentic-stack-cl/web.git
cd web
npm install        # también instala los git hooks
npm run dev        # http://localhost:4321
```

Si trabajas con Claude Code, lee [docs/AGENTIC.md](docs/AGENTIC.md): el repo trae agentes, skills y hooks listos.

## Proponer un post

1. (Opcional) Abre un issue con la plantilla **Post nuevo** para conversar la idea.
2. Crea una rama `post/<slug>` y el archivo `src/content/blog/<slug>.md` (con Claude Code: `/new-post <título>`). El nombre del archivo es la URL: kebab-case, sin tildes.
3. Front-matter:

   ```yaml
   ---
   title: "Título (≤ 80 caracteres)"
   description: "Resumen de una frase (≤ 160 caracteres)"
   pubDate: 2026-11-05
   authors: [tu-usuario-de-github]
   tags: [mcp, claude-code]
   draft: true
   ---
   ```

4. Si es tu primer post, agrega `src/content/authors/<tu-usuario>.json`:

   ```json
   { "name": "Tu Nombre", "github": "tu-usuario" }
   ```

5. Escribe en español neutro, tuteando. Detalles en [.claude/rules/content.md](.claude/rules/content.md).
6. Cambia a `draft: false`, ejecuta `npm run check && npm run build` y abre el PR.

Al publicar, tu post queda bajo licencia [CC BY-SA 4.0](LICENSE-content).

## Proponer un ítem del radar (blip)

El radar se vota en el foro **#radar** de nuestro Discord: un hilo por ítem, la etiqueta del hilo es el cuadrante y las reacciones 🟢 🔵 🟡 🔴 son los votos. Un proceso diario lleva los resultados al sitio. Detalles en https://agenticstack.cl/radar/como-funciona.

- **Si estás en Discord**: abre el hilo. No hace falta tocar este repo.
- **Si no**: abre un issue con la plantilla **Blip nuevo**, o un PR que agregue el ítem a `src/data/radar.json` con `"status": "propuesta"` (con Claude Code: `/radar-blip <nombre>`). Explica en el PR por qué ese anillo.

Valida con `npm run radar:validate`. El esquema está en [.claude/rules/radar.md](.claude/rules/radar.md).

## Mejorar el sitio

- Busca issues con la etiqueta [`good first issue`](https://github.com/agentic-stack-cl/web/labels/good%20first%20issue) o mira el [tablero](https://github.com/orgs/agentic-stack-cl/projects/1).
- Rama `feat/<tema>` o `fix/<tema>`.
- Usa los tokens de color del brand (`brand-*`, `accent-*`), revisa modo claro y oscuro, móvil y contraste AA.

## Ideas, backlog y tablero

El trabajo se organiza en el [tablero "Web pública"](https://github.com/orgs/agentic-stack-cl/projects/1):

| Etapa         | Qué significa                                                                           |
| ------------- | --------------------------------------------------------------------------------------- |
| **Ideas**     | Propuesta fuera del alcance actual. Sin compromiso ni prioridad. Lleva el label `idea`. |
| **Backlog**   | Aceptada: se hará, todavía sin fecha.                                                   |
| **Siguiente** | Lo próximo a tomar.                                                                     |
| **En curso**  | Alguien la está trabajando (asígnate el issue).                                         |
| **Revisión**  | Hay un PR abierto.                                                                      |
| **Hecho**     | Mergeado y desplegado.                                                                  |

La vista **Trabajo actual** oculta las ideas; la vista **Ideas** sirve para revisarlas.

**Para proponer una idea**: abre un issue con el label `idea` (o comenta en una existente con 👍 y tu caso de uso).

**Para pasar de Ideas a Backlog** una idea necesita:

1. Alcance claro y criterios de aceptación en el issue.
2. Al menos una persona interesada en hacerla.
3. El visto bueno de un owner, que quita el label `idea`, la mueve a Backlog y le asigna prioridad.

Los owners revisan las ideas una vez al mes: las aceptan, piden más detalle o las cierran explicando por qué.

## Commits y PRs

- [Conventional Commits](https://www.conventionalcommits.org/es/) en español: `feat(blog): agrega post sobre evals`, `fix(radar): corrige cuadrante de MCP`.
- Un PR = un tema; enlaza el issue (`Closes #N`).
- La CI debe pasar (`build`) y se necesita 1 aprobación. Se mergea con squash.
- Si usaste un agente, revisa tú el resultado antes de pedir revisión: la responsabilidad del cambio es de quien abre el PR.

## Comandos

| Comando                  | Qué hace                                   |
| ------------------------ | ------------------------------------------ |
| `npm run dev`            | servidor local                             |
| `npm run check`          | tipos, ESLint y Prettier                   |
| `npm run format`         | formatea todo                              |
| `npm run build`          | build de producción                        |
| `npm run links`          | enlaces internos rotos (después del build) |
| `npm run radar:validate` | valida el radar                            |
| `npm run test:py`        | tests del pipeline del radar               |

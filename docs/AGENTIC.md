# Trabajar con Claude Code en este repo

Este repo nace **agéntico**: además del código del sitio, trae la configuración para que [Claude Code](https://code.claude.com/docs) trabaje con las mismas reglas que una persona del equipo. Sirve también de ejemplo para la comunidad: copia lo que te sirva.

> Todo lo de aquí es opcional para contribuir. Puedes trabajar a mano y los git hooks y la CI te van a cuidar igual.

## Para empezar (5 minutos)

1. Clona e instala: `git clone git@github.com:agentic-stack-cl/web.git && cd web && npm install`. El `npm install` también instala los git hooks (lefthook).
2. Instala [uv](https://docs.astral.sh/uv/) si vas a tocar el pipeline del radar (`brew install uv`).
3. Abre Claude Code en la carpeta (`claude`, la app de escritorio o tu IDE) y **confía en la carpeta** cuando te lo pregunte. Sin ese paso no se activan los permisos, hooks ni plugins del proyecto.
4. Acepta la instalación de los plugins recomendados cuando aparezca el aviso (o ejecútalos con `/plugin`).
5. Pídele algo: _"crea un post sobre cómo usamos MCP en el trabajo"_ o escribe `/new-post Cómo usamos MCP`.

## Qué hay en `.claude/` y alrededores

| Ruta                                             | Qué es                                                                      | Se carga                                              |
| ------------------------------------------------ | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| `CLAUDE.md`                                      | Memoria del proyecto: stack, comandos, convenciones, límites. < 200 líneas. | Siempre, al iniciar la sesión                         |
| `.claude/rules/*.md`                             | Reglas con `paths:`: solo entran al contexto cuando se tocan esos archivos. | Al leer/editar `src/content/**` o el radar            |
| `.claude/agents/*.md`                            | Subagentes especializados con sus propias herramientas y modelo.            | Cuando Claude (o tú) los invoca                       |
| `.claude/skills/*/`                              | Procedimientos de varios pasos. Cada uno es también un comando `/nombre`.   | Cuando la tarea calza con la descripción, o `/nombre` |
| `.claude/hooks/*.sh`                             | Scripts que Claude Code ejecuta automáticamente tras editar archivos.       | En cada `Edit`/`Write`                                |
| `.claude/settings.json`                          | Permisos, hooks y plugins del equipo. Versionado.                           | Siempre (tras confiar en la carpeta)                  |
| `.claude/settings.local.json`, `CLAUDE.local.md` | Tus ajustes personales. **No se versionan** (`.gitignore`).                 | Solo en tu máquina                                    |
| `lefthook.yml`                                   | Git hooks para todos (personas y agentes).                                  | En `git commit` y `git push`                          |

## Subagentes: cuándo usar cada uno

Claude los usa solo cuando corresponde, pero puedes pedirlos explícitamente: _"usa el content-editor para revisar mi post"_.

| Agente            | Úsalo cuando…                                                                            | Hace                                                                                        | Modelo |
| ----------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------ |
| `content-editor`  | Escribiste o editaste un post o una ficha de autor                                       | Ortografía, tono, front-matter, etiquetas, enlaces. Corrige lo objetivo y sugiere el resto. | sonnet |
| `radar-curator`   | Cambia `src/data/radar.json`, alguien propone un blip, o llega el PR del sync de Discord | Valida esquema, cuadrante, anillo, `moved`, coherencia y votación.                          | sonnet |
| `web-reviewer`    | Tocaste páginas, componentes o estilos                                                   | Accesibilidad AA, modo oscuro, SEO, rendimiento, responsive. Solo reporta.                  | sonnet |
| `release-checker` | Antes de abrir o aprobar un PR                                                           | `check`, validación del radar, build, enlaces rotos, tests. Veredicto final.                | haiku  |

## Skills (comandos)

| Comando                  | Para qué                                                                                                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/new-post <título>`     | Crea rama, ficha de autor si falta y el archivo del post con front-matter válido y `draft: true`.                                                                        |
| `/radar-blip <nombre>`   | Agrega o mueve un blip con justificación, valida y prepara el texto del PR.                                                                                              |
| `/weekly-digest [desde]` | Redacta el resumen de cambios del radar para Discord (no lo publica). Solo se invoca a mano.                                                                             |
| `/issue-ready <n>`       | Revisa un issue contra la Definition of Ready, completa lo que falta investigando el repo y, con tu OK, actualiza el issue y le pone `ready`.                            |
| `/implement-issue <n>`   | Desarrolla un issue `ready` de principio a fin: rama, plan desde los criterios, implementación, verificación y PR con `Closes #n`. Se detiene si el issue no está ready. |

## Hooks: dos capas

- **Hook `UserPromptSubmit`** (`issue-ready.sh`): si tu mensaje menciona un issue (`#42`, "issue 42" o su URL) que no cumple la [Definition of Ready](ISSUES.md), Claude recibe qué falta y tú ves un aviso. No bloquea; la regla en `CLAUDE.md` le dice que no implemente y ofrezca `/issue-ready`.
- **Hooks de Claude Code** (`.claude/settings.json` → `PostToolUse` en `Edit|Write`):
  - `format.sh` formatea el archivo recién editado (Prettier o Ruff). Nunca bloquea.
  - `validate-radar.sh` valida `radar.json` si cambió; si falla sale con código 2 y Claude ve el error y lo corrige.
- **Git hooks con lefthook** (`lefthook.yml`), para personas y agentes por igual:
  - `pre-commit`: Prettier y ESLint sobre los archivos en stage, Ruff para Python, validación del radar.
  - `pre-push`: `npm run check`, `npm run build` y, si cambió el pipeline, `pytest`.
- **CI** repite `check` + `build` + tests en cada PR; es el status check obligatorio del ruleset de `main`.

Por qué así: la documentación de Claude Code cubre sus propios hooks, no los de git. Los chequeos que deben valer para todo el mundo van en git y CI; los hooks de Claude solo aceleran el ciclo del agente (formatear en el momento, avisar temprano).

## Permisos del proyecto

`.claude/settings.json` permite sin preguntar los comandos seguros (`npm run *`, `git diff`, `gh pr view`…), **pregunta** antes de `git push`, `gh pr create`/`merge` y de editar `public/brand/`, y **niega** leer `.env*`, el force-push y el push directo a `main`. Las reglas `deny` ganan siempre. Si necesitas más permisos para ti, ponlos en `.claude/settings.local.json`.

## Plugins

Del marketplace oficial `claude-plugins-official` ([anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)), declarados en `enabledPlugins`:

| Plugin                 | Por qué                                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| `frontend-design`      | Guía de diseño para componentes y páginas con calidad de producción.                                   |
| `modern-web-guidance`  | Buenas prácticas web actuales (accesibilidad, rendimiento, SEO), mantenido por Google Chrome.          |
| `playwright`           | Navegador controlable: el `web-reviewer` lo usa para ver páginas en móvil/escritorio y en modo oscuro. |
| `code-review`          | Revisión de PRs con varios agentes y filtro de falsos positivos (`/code-review`).                      |
| `commit-commands`      | Flujo de commit, push y PR desde Claude.                                                               |
| `claude-md-management` | Auditar y mantener `CLAUDE.md` al día con lo aprendido en cada sesión.                                 |
| `skill-creator`        | Para que la comunidad cree y mejore skills nuevas para este repo.                                      |

Evaluados y **no** incluidos por ahora:

- `github` (MCP oficial de GitHub): requiere un token personal; `gh` ya cubre lo que necesitamos.
- `context7`: útil para docs de Astro al día, pero envía consultas a un servicio de terceros; actívalo en tu `settings.local.json` si lo quieres.
- `typescript-lsp`, `pyright-lsp`: requieren instalar los servidores de lenguaje localmente; recomendados a título personal.
- `pr-review-toolkit`, `feature-dev`, `security-guidance`: valiosos pero se solapan con `code-review` y los subagentes del repo; los dejamos fuera para no sobrecargar el contexto.

## Flujos típicos

**Escribir un post**: `/new-post <título>` → escribes (con o sin ayuda) → _"revisa con content-editor"_ → `draft: false` → `release-checker` → PR con la plantilla "Post nuevo".

**Proponer un blip**: abre un hilo en el foro de Discord (lo ideal) o usa `/radar-blip <nombre>` → `radar-curator` → PR con la plantilla "Blip nuevo". El anillo definitivo lo decide la votación del foro (ver `/radar/como-funciona`).

**Desarrollar un issue**: el issue debe tener el label `ready` ([docs/ISSUES.md](ISSUES.md)). Si no, `/issue-ready <n>` → revisas y confirmas → `ready`. Luego `/implement-issue <n>` → PR. En GitHub, el workflow `issue-ready.yml` quita `ready` a los issues incompletos.

**Cambio en la web**: trabaja en `feat/<tema>` → `web-reviewer` → `release-checker` → PR.

## Mantener esta configuración

- Si Claude se equivoca dos veces en lo mismo, agrega la regla a `CLAUDE.md` o a una regla con `paths:` (no a tu memoria personal) y abre un PR con la etiqueta `agentic`.
- Procedimientos de más de 3–4 pasos van como skill, no en `CLAUDE.md`.
- Cambios a `.claude/` se revisan como código.

## Pendiente

- **@claude en PRs** con [`anthropics/claude-code-action@v1`](https://code.claude.com/docs/en/github-actions): requiere instalar la GitHub App de Claude en la organización y un secret `ANTHROPIC_API_KEY`. Lo decidirán los owners (tiene costo de API).

## Referencias

- Memoria y `CLAUDE.md`: https://code.claude.com/docs/en/memory
- Subagentes: https://code.claude.com/docs/en/sub-agents
- Skills: https://code.claude.com/docs/en/skills
- Hooks: https://code.claude.com/docs/en/hooks
- Permisos y settings: https://code.claude.com/docs/en/permissions · https://code.claude.com/docs/en/settings
- Plugins: https://code.claude.com/docs/en/plugins/install

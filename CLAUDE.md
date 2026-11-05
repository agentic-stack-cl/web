# The Agentic Stack — web

Sitio público de la comunidad The Agentic Stack (https://agenticstack.cl): home, radar tecnológico, blog y páginas de comunidad. Repo: `agentic-stack-cl/web`. Tablero: org project "Web pública" (#1).

El sitio está en **español** (el nombre "The Agentic Stack" queda en inglés). Código, nombres de variables y commits pueden ir en inglés o español, pero el texto visible para el usuario va siempre en español neutro, tuteando.

## Stack

- Astro 7 (estático) con content collections, MDX, `@astrojs/rss`, `@astrojs/sitemap`.
- Tailwind CSS v4 vía `@tailwindcss/vite`. Tokens del brand en `src/styles/global.css` (`@theme`): `brand` #0F2A6B, `accent` #F97316, fuente Inter. No uses colores sueltos: usa los tokens.
- Modo oscuro por clase `.dark` en `<html>` (preferencia del sistema + toggle guardado en `localStorage`).
- Radar: `radar.js` de Zalando (vendorizado en `public/vendor/`) + tabla accesible, datos en `src/data/radar.json`.
- Comentarios: giscus (GitHub Discussions). Config en `src/config.ts`.
- Pipeline del radar: Python 3.11 sin dependencias externas en `scripts/radar/`; tests con pytest.
- Deploy: GitHub Pages vía `.github/workflows/deploy.yml`. Dominio en `public/CNAME`.

## Comandos

```bash
npm install          # instala dependencias y los git hooks (lefthook)
npm run dev          # servidor local en http://localhost:4321
npm run build        # build estático a dist/
npm run check        # astro check + eslint + prettier --check
npm run format       # prettier --write
npm run links        # enlaces internos rotos en dist/ (requiere build)
npm run radar:validate   # valida src/data/radar.json
npm run test:py      # tests del pipeline (uvx pytest)
```

Antes de dar por terminado un cambio: `npm run check && npm run build`. Si tocaste `scripts/radar/`: `npm run test:py`.

## Estructura

- `src/content/blog/` posts (`.md`/`.mdx`), `src/content/authors/` autores (`<handle-github>.json`). Esquemas en `src/content.config.ts`.
- `src/data/radar.json` blips del radar. Reglas detalladas en `.claude/rules/radar.md`.
- `src/pages/` rutas; `src/components/`, `src/layouts/`, `src/lib/`.
- `scripts/radar/` sync con Discord (`sync.py`), validador, resumen semanal; `tests/` y `fixtures/`.
- `docs/` documentación para humanos (AGENTIC, DNS, DEPLOY).

## Convenciones

- Commits: Conventional Commits en español, en imperativo: `feat(radar): agrega blip MCP`, `fix(blog): corrige fecha del RSS`, `docs: ...`, `chore: ...`. Scopes habituales: `web`, `blog`, `radar`, `infra`, `agentic`.
- Ramas: `post/<slug>`, `radar/<slug>`, `feat/<tema>`, `fix/<tema>`. Todo cambio entra por PR a `main` (ruleset: 1 aprobación + build verde, sin force-push).
- Un PR = un tema. Enlaza el issue (`Closes #N`).
- Contenido: front-matter según el esquema; fechas `YYYY-MM-DD`; slug en kebab-case sin tildes. Ver `.claude/rules/content.md`.
- Accesibilidad no negociable: contraste AA en ambos modos, `alt` en imágenes, jerarquía de headings, foco visible.
- No inventes datos de la comunidad (miembros, fechas de eventos, enlaces de Discord). Si falta el dato, deja un `TODO` visible en el PR.

## Issues y Definition of Ready

- Solo se implementan issues con el label `ready`, que cumplen `docs/ISSUES.md` (8 secciones, sin decisiones abiertas, label de área, cabe en un PR).
- Antes de escribir código para un issue: `python3 scripts/issues/check_ready.py --issue <n>`. Si falla o no tiene `ready`, **no implementes**: explica qué falta y ofrece `/issue-ready <n>`. El hook `UserPromptSubmit` te avisa cuando un prompt menciona un issue incompleto.
- Para desarrollar un issue `ready` usa `/implement-issue <n>`. Issues nuevos de desarrollo: plantilla "Tarea de desarrollo".
- Nunca pongas `ready` ni edites un issue sin confirmación humana.

## Agentes y skills del repo

- Subagentes en `.claude/agents/`: `content-editor`, `radar-curator`, `web-reviewer`, `release-checker`. Úsalos de forma proactiva según su descripción.
- Skills en `.claude/skills/`: `/new-post`, `/radar-blip`, `/weekly-digest`, `/issue-ready`, `/implement-issue`.
- Guía para personas: `docs/AGENTIC.md` (no la importes: es para humanos).

## Límites

- No hagas `git push` a `main` ni force-push. No toques `public/brand/` (lo mantienen los owners).
- No leas ni escribas `.env*`. Los secrets (`DISCORD_TOKEN`, etc.) viven solo en GitHub Actions.
- El sync del radar nunca escribe directo en `main`: abre un PR.

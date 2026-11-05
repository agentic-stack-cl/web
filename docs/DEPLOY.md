# Despliegue

El sitio es estático y se publica en **GitHub Pages** desde GitHub Actions.

| Workflow         | Cuándo                             | Qué hace                                                                                                                                     |
| ---------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `ci.yml`         | cada PR y push a `main` (y manual) | valida radar, `astro check` + ESLint + Prettier, Ruff, pytest, build y enlaces internos. Su job `build` es el check obligatorio del ruleset. |
| `deploy.yml`     | push a `main` (y manual)           | `withastro/action` construye y `actions/deploy-pages` publica.                                                                               |
| `radar-sync.yml` | diario 08:00 CLT (y manual)        | sincroniza el radar con Discord y abre un PR. Ver [RADAR-SYNC.md](RADAR-SYNC.md).                                                            |

## Flujo

1. Rama → PR → CI verde + 1 aprobación (ruleset de `main`, sin force-push).
2. Merge (squash) → `deploy.yml` publica en 1–2 minutos.
3. Rollback: revierte el commit en `main` (`git revert`) por PR; el deploy vuelve a correr.

## Configuración del repo (ya aplicada)

- Pages: _Source_ = GitHub Actions.
- Ruleset `main`: PR obligatorio, 1 aprobación, check `build`, sin force-push ni borrado.
- Merge: solo squash, borrar rama al mergear.

## Pendientes manuales (requieren a un owner)

- **Dominio**: seguir [DNS.md](DNS.md) y luego configurar el custom domain.
- **Actions puede abrir PRs**: _Settings → Actions → General → Workflow permissions_ → marcar _Allow GitHub Actions to create and approve pull requests_ (lo necesita `radar-sync.yml`).
- **giscus**: instalar la app en el repo desde https://github.com/apps/giscus (_Only select repositories_ → `web`). Opcional: crear la categoría de Discussions **"Comentarios del blog"** (formato _Announcement_, para que solo giscus y maintainers abran discusiones), obtener su id en https://giscus.app/es y actualizar `GISCUS.category`/`categoryId` en `src/config.ts`. Hoy usa la categoría _Announcements_.
- **Logo**: subir los archivos a `public/brand/` (ver su README). El sitio los detecta solo.
- **Secrets del radar**: `DISCORD_TOKEN`, `FORUM_CHANNEL_ID`, `DISCORD_WEBHOOK_URL`.

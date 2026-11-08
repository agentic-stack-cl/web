# Métricas de Vitalidad y Seguridad del Radar

Este pipeline enriquece el **Radar Tecnológico** con métricas automáticas de tracción comunitaria y postura de seguridad de cada tecnología, sin interferir con la sincronización diaria de votos de Discord.

---

## 1. Arquitectura de Datos

Para garantizar la estabilidad del radar y evitar conflictos de git, la información se divide en tres archivos:

| Archivo                       | Responsabilidad                                                                                       | Editado por                                            |
| :---------------------------- | :---------------------------------------------------------------------------------------------------- | :----------------------------------------------------- |
| `src/data/radar.json`         | Votos de la comunidad, anillos, cuadrantes y descripciones.                                           | Bot de Discord (`radar-sync.yml`) y curadores humanos. |
| `src/data/radar-sources.json` | Catálogo declarativo: mapeo de cada blip a su repo de GitHub, paquete npm/PyPI y certificaciones.     | Humanos (al indexar una nueva tecnología).             |
| `src/data/radar-metrics.json` | Métricas computadas: estrellas, forks, descargas, Scorecard OpenSSF, CVEs de OSV y series históricas. | GitHub Actions (`radar-metrics.yml`) semanalmente.     |

---

## 2. Tipos de Tecnologías y Clasificación (`kind`)

En `radar-sources.json`, cada entrada especifica su tipo:

- **`oss` (Código Abierto)**:
  - Fuentes: GitHub API, npm Registry API, PyPI Stats API, OpenSSF Scorecard API, OSV.dev.
  - Métricas: Estrellas, forks, descargas mensuales, historial temporal, Scorecard (0–10), días desde último release, releases en el año, mantenedores activos, CVEs activos y licencias.
- **`proprietary` (Propietario / SaaS / CLI cerrada)**:
  - Fuentes: Paquete de distribución público si existe (ej. `@anthropic-ai/claude-code` en npm) + sellos auditados declarados (SOC 2 Type II, ISO 27001, Zero Data Retention).
- **`pattern` (Práctica o Patrón Metodológico)**:
  - Sin código distribuible ni vulnerabilidades de software. Muestra etiqueta descriptiva `[📐] Práctica / Patrón`.

---

## 3. Niveles de Blindaje de Seguridad (Shield Tier)

> **Nota de diseño**: Los badges de seguridad **no usan colores semafóricos** (verde, azul, amarillo, rojo) para no competir visualmente con los anillos del radar (_Adoptar, Probar, Evaluar, Esperar_). Utilizan glifos e infografía neutra en escala de grises:

- `[▰▰▰] 🛡️ Tier A (Blindaje Alto)`: OpenSSF Scorecard ≥ 7.0, 0 CVEs activos y último release hace ≤ 60 días.
- `[▰▰▱] 🛡️ Tier B (Blindaje Medio)`: OpenSSF Scorecard entre 4.0 y 7.0 o release entre 60 y 180 días.
- `[▰▱▱] ⚠️ Tier C (Atención Requerida)`: CVEs activos en OSV.dev o proyecto sin releases hace más de 180 días.
- `[🏛️] Certificado Corporativo`: Herramienta propietaria con certificaciones auditadas (SOC 2, ISO 27001, ZDR).
- `[📐] Práctica / Patrón`: Técnicas conceptuales sin software ejecutable.
- `[—] Sin telemetría`: Tecnologías aún no mapeadas en `radar-sources.json`.

---

## 4. Uso y Desarrollo Local

```bash
# Ejecutar recolección en modo dry-run (sin escribir)
python3 scripts/radar/metrics.py --dry-run

# Modo offline (valida y recalcula tiers usando la caché existente sin red)
python3 scripts/radar/metrics.py --offline

# Recolección real escribiendo en src/data/radar-metrics.json
npm run radar:metrics

# Ejecutar tests unitarios
npm run test:py
```

---

## 5. Automatización Semanal

El workflow `.github/workflows/radar-metrics.yml` se ejecuta:

- **Cron**: Todos los lunes a las 06:00 UTC (03:00 CLT).
- **Manual**: Con `workflow_dispatch` desde la pestaña Actions de GitHub.
- Abre un Pull Request automático en la rama `radar/metrics` para revisión del equipo.

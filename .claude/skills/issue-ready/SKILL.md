---
name: issue-ready
description: Revisa un issue contra la Definition of Ready (docs/ISSUES.md), completa la información que falta investigando el repo y, con confirmación, actualiza el issue y le pone el label `ready`. Úsalo cuando un issue esté incompleto, cuando el hook avise que no está ready, o cuando pidan refinar, completar o preparar un ticket para desarrollo.
argument-hint: "<número de issue>"
allowed-tools: Read, Grep, Glob, Bash(python3 scripts/issues/check_ready.py *), Bash(gh issue view *), Bash(gh issue list *)
---

# Dejar un issue ready para desarrollar

Issue: `#$ARGUMENTS` (si viene vacío, pregunta el número).

## 1. Diagnóstico

1. `gh issue view $ARGUMENTS --json number,title,body,labels,state,comments`
2. `python3 scripts/issues/check_ready.py --issue $ARGUMENTS`
3. Si ya cumple y tiene `ready`, dilo y termina. Si cumple pero sin label, salta al paso 4.

## 2. Completar con evidencia del repo

Lee `docs/ISSUES.md` (estructura y ejemplos). Para cada sección que falte:

- **Contexto / Objetivo / Alcance**: sale del issue y sus comentarios. No inventes motivaciones ni datos de la comunidad.
- **Fuera de alcance**: propone límites razonables; menciona issues relacionados que cubren lo excluido (`gh issue list --state open`).
- **Criterios de aceptación**: casillas verificables y concretas (rutas, comandos, comportamientos), incluye casos borde y siempre `npm run check`, `npm run build` (y `npm run test:py` si toca Python).
- **Cómo verificar**: comandos exactos y páginas a revisar.
- **Pistas técnicas**: **investiga el código** (Grep/Glob/Read) y nombra archivos reales, componentes a reutilizar y patrones existentes. Es la sección que más ayuda a un agente.
- **Dependencias**: issues, secrets o archivos que faltan, con `#número`. "Ninguna" si no hay.

**Decisiones abiertas**: lístalas y **pregúntaselas al usuario** una por una (con tu recomendación). No las resuelvas tú. Con alguna pendiente, el issue no puede quedar `ready`.

Si el issue es demasiado grande para un PR (más de ~8 criterios o áreas sin relación), propone dividirlo y redacta los issues hijos.

## 3. Confirmar y actualizar

1. Muestra el cuerpo completo propuesto (mismo formato que la plantilla `tarea.yml`, títulos `###`).
2. Guárdalo en un archivo temporal y valida: `python3 scripts/issues/check_ready.py --body-file <archivo> --labels <labels>`.
3. **Solo con confirmación explícita del usuario**: `gh issue edit $ARGUMENTS --body-file <archivo>` y, si corresponde, `gh issue edit $ARGUMENTS --add-label ready --remove-label idea` y el label de área que falte.
4. Vuelve a ejecutar `check_ready.py --issue $ARGUMENTS` y reporta el resultado.

Nunca pongas `ready` a un issue que no pase el validador: el workflow `issue-ready.yml` lo quitaría.

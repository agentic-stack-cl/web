---
name: implement-issue
description: Desarrolla un issue que tiene el label `ready`, de principio a fin — rama, plan desde los criterios de aceptación, implementación, verificación y PR con Closes #n. Úsalo cuando pidan implementar, tomar, resolver o trabajar en un issue o ticket concreto.
argument-hint: "<número de issue>"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(python3 scripts/issues/check_ready.py *), Bash(gh issue view *), Bash(git switch *), Bash(git status *), Bash(git diff *), Bash(npm run *), Bash(uvx *)
---

# Implementar un issue ready

Issue: `#$ARGUMENTS`.

## 0. Puerta de entrada (obligatoria)

1. `gh issue view $ARGUMENTS --json number,title,body,labels,state`
2. `python3 scripts/issues/check_ready.py --issue $ARGUMENTS`

**Detente** si el validador falla, si el issue no tiene el label `ready` o si está cerrado. Explica qué falta (cita la salida del validador) y ofrece `/issue-ready $ARGUMENTS`. No escribas código.

## 1. Plan

- Lee las secciones del issue. Las **Pistas técnicas** te dicen por dónde empezar; las **Dependencias** deben estar resueltas (verifica que los issues o PRs citados estén cerrados o mergeados).
- Arma un plan que cubra **cada criterio de aceptación**, en orden, y respeta **Fuera de alcance**.
- Si descubres que falta información esencial, no la inventes: detente, explica y propone actualizar el issue.

## 2. Rama

`git switch -c <tipo>/<numero>-<slug-corto>` según el área: `feat/`, `fix/`, `post/`, `radar/`, `chore/`. Si ya estás en una rama para este issue, sigue en ella.

## 3. Implementar

- Sigue `CLAUDE.md` y las reglas de `.claude/rules/`.
- Cambios mínimos para cumplir los criterios; nada de refactors no pedidos.
- Agrega o actualiza tests cuando el issue toca lógica (Python en `scripts/`).

## 4. Verificar

1. Ejecuta lo indicado en **Cómo verificar** del issue.
2. `npm run check && npm run build && npm run links`; si tocaste Python, `npm run test:py`.
3. Según lo que tocaste, delega en `web-reviewer`, `content-editor` o `radar-curator`; al final, `release-checker`.
4. Recorre los criterios de aceptación y marca cuáles quedaron cumplidos y cómo lo comprobaste.

## 5. Entregar

- Commits en Conventional Commits en español.
- Redacta el PR con la plantilla del repo: qué cambia, `Closes #$ARGUMENTS`, y la lista de criterios con su verificación.
- Pide confirmación antes de `git push` y `gh pr create` (el repo los tiene en `ask`).

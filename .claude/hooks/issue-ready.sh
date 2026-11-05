#!/usr/bin/env bash
# Hook UserPromptSubmit: si el prompt menciona un issue (#42, "issue 42" o su URL) que no
# cumple la Definition of Ready (docs/ISSUES.md), avisa a Claude y a la persona. Nunca bloquea.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
command -v gh >/dev/null 2>&1 || exit 0
python3 scripts/issues/check_ready.py --hook 2>/dev/null || true
exit 0

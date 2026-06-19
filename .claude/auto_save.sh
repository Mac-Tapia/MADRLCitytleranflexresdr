#!/usr/bin/env bash
# .claude/auto_save.sh
# Ejecutado por el Stop hook: commit + push automatico despues de cada turno de Claude.
# Seguro: el .gitignore ya excluye outputs/, *.pt, .venv*/, __pycache__/, etc.

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$REPO"

# Salida rapida si no hay nada que guardar
if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
    exit 0
fi

TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"

# Agregar todo (gitignore se encarga de excluir binarios y outputs)
git add -A 2>/dev/null || true

# Si aun no hay nada en staging, salir
if git diff --cached --quiet 2>/dev/null; then
    exit 0
fi

# Construir lista de archivos para mensaje y README
FILES_RAW="$(git diff --cached --name-only 2>/dev/null)"
N="$(printf '%s\n' "$FILES_RAW" | grep -c . 2>/dev/null || echo 1)"
SHORT="$(printf '%s\n' "$FILES_RAW" | head -4 | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')"
[ "$N" -gt 4 ] && SHORT="${SHORT} (+$((N - 4)) mas)"

# Actualizar seccion "Cambios Recientes" del README.md via Python
export AUTO_ENTRY="- **${TIMESTAMP}**: ${SHORT}"
python -c "
import sys, os, re

entry = os.environ.get('AUTO_ENTRY', '')
try:
    with open('README.md', encoding='utf-8') as f:
        txt = f.read()
    marker = '## Cambios Recientes'
    if marker in txt:
        # Insertar nueva entrada como primera linea de la seccion
        txt = re.sub(
            r'(## Cambios Recientes[ \t]*\n)',
            r'\1' + entry + '\n',
            txt, count=1
        )
    else:
        txt = txt.rstrip() + '\n\n## Cambios Recientes\n\n' + entry + '\n'
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(txt)
except Exception as e:
    print('README no actualizado:', e, file=sys.stderr)
" 2>/dev/null || true

git add README.md 2>/dev/null || true

# Commit
MSG="auto: ${SHORT}"
[ "${#MSG}" -gt 72 ] && MSG="${MSG:0:69}..."
if ! git commit -m "$MSG" 2>/dev/null; then
    exit 0
fi

# Push a la rama actual
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
git push origin "$BRANCH" 2>/dev/null || true

echo "Guardado en GitHub: $SHORT"

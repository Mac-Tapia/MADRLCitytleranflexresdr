"""Fix literal newlines in Python string literals inside notebook source cells."""
import json, ast, re, sys
from pathlib import Path

path = Path('d:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb')

with open(path, 'rb') as f:
    nb = json.loads(f.read().decode('utf-8', errors='replace'))

ESC_N = chr(92) + 'n'   # the two-character string: backslash + n

def fix_literal_newlines(s):
    """Replace actual newlines inside single- or double-quoted string literals with \\n."""
    # Match a quote, optional non-newline/non-quote content, newline, optional content, closing quote
    s = re.sub(r"'([^'\n]*)\n([^'\n]*)'",
               lambda m: "'" + m.group(1) + ESC_N + m.group(2) + "'", s)
    s = re.sub(r'"([^"\n]*)\n([^"\n]*)"',
               lambda m: '"' + m.group(1) + ESC_N + m.group(2) + '"', s)
    return s

def has_unclosed_single_quote(body):
    """True if body has an odd number of unescaped ' not part of triple-quotes."""
    if "'''" in body:
        return False  # triple-quoted string — valid multiline
    count = body.replace("\\'", '').count("'")
    return count % 2 == 1

fixed_total = 0
for ci, cell in enumerate(nb['cells']):
    if cell['cell_type'] != 'code':
        continue
    src = cell['source']
    # First pass: within-element regex fix (handles merged elements from prior attempts)
    for i, line in enumerate(src):
        fixed = fix_literal_newlines(line)
        if fixed != line:
            src[i] = fixed
            fixed_total += 1
    # Second pass: merge split-element broken strings
    changed = True
    while changed:
        changed = False
        i = len(src) - 2
        while i >= 0:
            line = src[i]
            nxt  = src[i + 1]
            ends_with_open_quote = (
                line.endswith("'\n") and has_unclosed_single_quote(line[:-1])
            )
            if ends_with_open_quote:
                merged = line[:-1] + ESC_N + nxt
                src[i] = merged
                src.pop(i + 1)
                changed = True
                fixed_total += 1
            i -= 1

# Verify
errors = 0
for ci, cell in enumerate(nb['cells']):
    if cell['cell_type'] != 'code':
        continue
    src_str = ''.join(cell['source'])
    try:
        ast.parse(src_str)
    except SyntaxError as e:
        print(f'REMAINING ERROR Cell {ci} L{e.lineno}: {e.msg}')
        print(f'  -> {repr((e.text or "").strip()[:80])}')
        errors += 1

print(f'Fixed {fixed_total} broken string pairs. Remaining errors: {errors}')

if errors == 0:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print('Notebook written successfully.')
else:
    print('NOT written — fix incomplete.')
    sys.exit(1)

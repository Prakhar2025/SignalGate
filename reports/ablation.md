# Improvement changelog evidence (docs/04 §9)

| Stage | Tried & why | Catch rate | False-reject | F2 catch | Est. tokens/case | Decision |
|---|---|---|---|---|---|---|
| baseline | second regime-narrative agent | 0.475 (baseline 0.475) | 0.0 | 0.0 | 0 | starting point |
| iter1 | second regime-narrative agent | 1.0 (baseline 0.475) | 0.875 | 1.0 | 201 | kept only if false-reject stays under control |
| iter2 | second regime-narrative agent | 0.925 (baseline 0.475) | 0.0 | 1.0 | 201 | main contribution |
| iter3 | second regime-narrative agent | 0.925 (baseline 0.475) | 0.0 | 1.0 | 282 | est. tokens +40% vs iter2, no accuracy gain -> removed |

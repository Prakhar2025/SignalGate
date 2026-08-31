# Improvement changelog evidence (docs/04 §9)

| Stage | Tried & why | Catch rate | False-reject | F2 catch | Est. tokens/case | Decision |
|---|---|---|---|---|---|---|
| baseline | static lint rules (syntax only) | 0.475 (baseline 0.475) | 0.0 | 0.0 | 0 | starting point |
| iter1 | bare-prompt agent without verification tools | 1.0 (baseline 0.475) | 0.875 | 1.0 | 201 | kept only if false-reject stays under control |
| iter2 | lint + tool-agent with 4 deterministic probes | 0.925 (baseline 0.475) | 0.0 | 1.0 | 201 | main contribution |
| iter3 | second regime-narrative agent | 0.925 (baseline 0.475) | 0.0 | 1.0 | 281 | est. tokens +40% vs iter2, no accuracy gain -> removed |

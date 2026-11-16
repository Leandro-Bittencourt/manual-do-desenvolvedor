# Resultados da 1ª etapa — projetos controlados

## Projetos analisados

| Linguagem | Banco de dados (modelo) | Requisitos | Testes | Elementos de código | Vínculos sugeridos | Vínculos no gabarito | Tempo (ms) |
|---|---|---:|---:|---:|---:|---:|---:|
| Python | PostgreSQL (relacional) | 6 | 10 | 25 | 43 | 39 | 289,10 |
| Java | Neo4j (grafo) | 6 | 10 | 36 | 49 | 42 | 459,40 |
| JavaScript | MongoDB (documentos) | 6 | 10 | 22 | 46 | 39 | 426,30 |
| HTML + JavaScript | localStorage (chave-valor) | 6 | 13 | 35 | 57 | 57 | 70,50 |

## Combinação das estratégias por projeto

| Linguagem | Sugeridos | Corretos | Esperados | Precisão | Revocação | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Python | 43 | 34 | 39 | 0,79 | 0,87 | 0,83 |
| Java | 49 | 36 | 42 | 0,73 | 0,86 | 0,79 |
| JavaScript | 46 | 35 | 39 | 0,76 | 0,90 | 0,82 |
| HTML + JavaScript | 57 | 48 | 57 | 0,84 | 0,84 | 0,84 |
| **Total** | 195 | 153 | 177 | **0,78** | **0,86** | **0,82** |

## Desempenho de cada estratégia (4 projetos somados)

| Estratégia | Sugeridos | Corretos | Precisão | Revocação | F1 |
|---|---:|---:|---:|---:|---:|
| E1 | 33 | 33 | 1,00 | 0,19 | 0,31 |
| E2 | 84 | 81 | 0,96 | 0,46 | 0,62 |
| E3 | 47 | 23 | 0,49 | 0,13 | 0,21 |
| E4 | 84 | 65 | 0,77 | 0,37 | 0,50 |
| Combinação | 195 | 153 | 0,78 | 0,86 | 0,82 |

## Efeito do limiar de confiança (4 projetos somados)

| Vínculos considerados | Sugeridos | Corretos | Precisão | Revocação | F1 |
|---|---:|---:|---:|---:|---:|
| todos os vínculos | 195 | 153 | 0,78 | 0,86 | 0,82 |
| confiança média ou alta (≥ 0,50) | 149 | 130 | 0,87 | 0,73 | 0,80 |
| somente confiança alta (≥ 0,80) | 117 | 114 | 0,97 | 0,64 | 0,78 |

## Combinação por tipo de vínculo

| Linguagem | Tipo | Sugeridos | Corretos | Esperados | Precisão | Revocação |
|---|---|---:|---:|---:|---:|---:|
| Python | Requisito–código | 14 | 7 | 10 | 0,50 | 0,70 |
| Python | Requisito–teste | 9 | 8 | 10 | 0,89 | 0,80 |
| Python | Teste–código | 20 | 19 | 19 | 0,95 | 1,00 |
| Java | Requisito–código | 18 | 7 | 10 | 0,39 | 0,70 |
| Java | Requisito–teste | 9 | 8 | 10 | 0,89 | 0,80 |
| Java | Teste–código | 22 | 21 | 22 | 0,95 | 0,95 |
| JavaScript | Requisito–código | 15 | 7 | 10 | 0,47 | 0,70 |
| JavaScript | Requisito–teste | 11 | 9 | 10 | 0,82 | 0,90 |
| JavaScript | Teste–código | 20 | 19 | 19 | 0,95 | 1,00 |
| HTML + JavaScript | Requisito–código | 23 | 14 | 21 | 0,61 | 0,67 |
| HTML + JavaScript | Requisito–teste | 12 | 12 | 14 | 1,00 | 0,86 |
| HTML + JavaScript | Teste–código | 22 | 22 | 22 | 1,00 | 1,00 |

## Detalhe por projeto e estratégia

| Linguagem | Estratégia | Sugeridos | Corretos | Precisão | Revocação | F1 |
|---|---|---:|---:|---:|---:|---:|
| Python | E1 | 7 | 7 | 1,00 | 0,18 | 0,30 |
| Python | E2 | 20 | 19 | 0,95 | 0,49 | 0,64 |
| Python | E3 | 9 | 5 | 0,56 | 0,13 | 0,21 |
| Python | E4 | 19 | 14 | 0,74 | 0,36 | 0,48 |
| Python | Combinação | 43 | 34 | 0,79 | 0,87 | 0,83 |
| Java | E1 | 7 | 7 | 1,00 | 0,17 | 0,29 |
| Java | E2 | 22 | 21 | 0,95 | 0,50 | 0,66 |
| Java | E3 | 11 | 5 | 0,45 | 0,12 | 0,19 |
| Java | E4 | 21 | 14 | 0,67 | 0,33 | 0,44 |
| Java | Combinação | 49 | 36 | 0,73 | 0,86 | 0,79 |
| JavaScript | E1 | 7 | 7 | 1,00 | 0,18 | 0,30 |
| JavaScript | E2 | 20 | 19 | 0,95 | 0,49 | 0,64 |
| JavaScript | E3 | 10 | 5 | 0,50 | 0,13 | 0,20 |
| JavaScript | E4 | 21 | 15 | 0,71 | 0,38 | 0,50 |
| JavaScript | Combinação | 46 | 35 | 0,76 | 0,90 | 0,82 |
| HTML + JavaScript | E1 | 12 | 12 | 1,00 | 0,21 | 0,35 |
| HTML + JavaScript | E2 | 22 | 22 | 1,00 | 0,39 | 0,56 |
| HTML + JavaScript | E3 | 17 | 8 | 0,47 | 0,14 | 0,22 |
| HTML + JavaScript | E4 | 23 | 22 | 0,96 | 0,39 | 0,55 |
| HTML + JavaScript | Combinação | 57 | 48 | 0,84 | 0,84 | 0,84 |

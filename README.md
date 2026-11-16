# Manual do Desenvolvedor

Ferramenta web de **rastreabilidade entre requisitos, casos de teste e código-fonte**, desenvolvida como
Trabalho de Conclusão de Curso (Engenharia de Software — UNIVILLE).

O desenvolvedor envia o projeto em um arquivo `.zip`. A ferramenta lê os requisitos, o código Python e os
testes, sugere os vínculos entre eles com um grau de confiança e permite **localizar a origem de um erro**
a partir da mensagem de erro (*traceback*), mostrando os requisitos e testes relacionados.

> **Processamento 100% local.** Nenhum código ou requisito é enviado a serviços externos, incluindo
> modelos de inteligência artificial generativa. O código enviado nunca é executado e não fica armazenado:
> guardam-se apenas referências (arquivo e linhas).

## Como funciona (Capítulo 3 do TCC)

| Etapa | O que faz | Onde está no código |
|---|---|---|
| 1. Recepção e extração | Extrai o ZIP com verificações de segurança (*path traversal*, *zip bomb*, links simbólicos, limites de tamanho); ignora `.env`, chaves e credenciais | `app/analysis/extrator.py` |
| 2. Identificação dos artefatos | Requisitos em Markdown, CSV ou JSON com identificadores reconhecidos por expressões regulares; código Python pelo módulo `ast` (comentários pelo `tokenize`), Java e JavaScript pelo tree-sitter e HTML pelo `html.parser`; testes pelas convenções do pytest/unittest, JUnit e `node:test`/Jest/Playwright | `app/analysis/requisitos.py`, `app/analysis/codigo*.py` |
| 3. Vinculação | Estratégias E1 a E4 (quadro abaixo) | `app/analysis/estrategias.py`, `app/analysis/resolvedor.py`, `app/analysis/texto.py` |
| 4. Combinação das evidências | Grau de confiança `c = 1 − ∏(1 − wᵢ · sᵢ)`, classificado em alta, média ou baixa | `app/analysis/confianca.py` |
| 5. Revisão | O desenvolvedor confirma ou rejeita os vínculos; as decisões valem para as próximas versões | `app/services.py`, tela *Revisão de vínculos* |
| 6. Consulta e localização de erros | Consulta por requisito, por código ou a partir de um *traceback*; vínculos de código alterado voltam para revisão em uma nova versão | `app/analysis/localizador.py`, `app/services.py` |

| Estratégia | Funcionamento | Vínculos |
|---|---|---|
| **E1** – Marcação explícita | Identificadores de requisitos em comentários, *docstrings* e nomes de testes (`# @traces RF-01`, `test_rf01_login`) | requisito–código, requisito–teste |
| **E2** – Análise de chamadas | Funções chamadas por cada teste, obtidas pela árvore sintática e resolvidas pelas importações | teste–código |
| **E3** – Inferência transitiva | Se o requisito liga-se ao teste e o teste chama a função, o requisito liga-se à função (grafo NetworkX) | requisito–código |
| **E4** – Similaridade textual | TF-IDF e similaridade do cosseno (scikit-learn), com separação de identificadores, remoção de palavras vazias, glossário português→inglês e radicalização (NLTK) | requisito–código, requisito–teste |

O modelo de dados (`app/models.py`) segue o metamodelo de rastreabilidade de Escalona, Koch e
García-Borgoñón (2022): elementos rastreáveis, vínculos, evidências (regras) e decisões (monitoramento).

## Tecnologias

Python 3.12 · Flask · Flask-SQLAlchemy · Flask-Login · SQLite · scikit-learn · NetworkX · NLTK ·
tree-sitter (gramáticas Java e JavaScript) · módulos nativos `zipfile`, `re`, `ast`, `tokenize`, `html.parser` e
`hashlib` · HTML, CSS e JavaScript (sem dependências externas) · pytest.

### Linguagens analisadas

| Linguagem | Leitura | Elementos rastreáveis | Testes reconhecidos |
|---|---|---|---|
| Python | `ast` + `tokenize` | funções, classes, métodos | pytest / unittest (`test_*.py`) |
| Java | tree-sitter | classes, interfaces, records, métodos | JUnit (`*Test.java`, `src/test`, `@Test`) |
| JavaScript | tree-sitter | funções, classes, métodos | `node:test`, Jest, Mocha, Playwright (`*.test.js`, `*.spec.js`) |
| HTML | `html.parser` | elementos de interface com `id` (formulários, seções, botões, listas) | ligados aos testes de interface pelos seletores (`#id`) |

No HTML, a marcação explícita pode ser feita por comentário (`<!-- @traces RF-01 -->`) ou pelo atributo
`data-requisito="RF-01"`. A localização de erros entende o *traceback* do Python e as pilhas do Java e do Node.js.

## Executar no Windows

Requer Python 3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Abra <http://127.0.0.1:5000>, crie uma conta e envie um projeto. O banco SQLite e a chave secreta são
criados automaticamente na pasta `instance/` (que não vai para o Git).

No Linux ou macOS, troque a ativação por `source .venv/bin/activate`.

### Com Docker (opcional)

```bash
docker compose up --build
```

## Como preparar um projeto para análise

```
meu_projeto/
├── requisitos.md          # ou requisitos.csv / requisitos.json
├── src/minha_app/*.py     # código de produção
└── tests/test_*.py        # testes (pytest ou unittest)
```

Exemplo de `requisitos.md`:

```markdown
## RF-01 — Cadastro de usuário
O sistema deve permitir cadastrar um usuário com nome, e-mail e senha.
```

Também são aceitos itens de lista (`- RF-01: Título — descrição`), tabelas Markdown, CSV
(`id;titulo;descricao`) e JSON (`[{"id": "RF-01", "titulo": "...", "descricao": "..."}]`).
Prefixos reconhecidos: `RF`, `RNF`, `REQ`, `RN`, `UC`, `US`, `HU` (`RF-01`, `RF01`, `rf_1`...).

A marcação explícita é opcional, mas aumenta a confiança dos vínculos:

```python
# @traces RF-01
def cadastrar(self, nome, email, senha): ...

def test_rf01_cadastra_usuario(): ...
```

## Projeto de exemplo e avaliação (Seção 3.5 do TCC)

A pasta `exemplos/` contém o projeto controlado **Loja Virtual** e o gabarito com os vínculos corretos.
O script de avaliação calcula precisão, revocação e F1 por estratégia:

```powershell
python scripts/gerar_zip_exemplo.py
python -m app.analysis.avaliacao exemplos/loja_virtual.zip exemplos/gabarito_loja_virtual.json --detalhar
```

Resultado com a configuração padrão:

| Estratégia | Sugeridos | Corretos | Esperados | Precisão | Revocação | F1 |
|---|---:|---:|---:|---:|---:|---:|
| E1 | 7 | 7 | 44 | 1,00 | 0,16 | 0,27 |
| E2 | 24 | 24 | 44 | 1,00 | 0,55 | 0,71 |
| E3 | 12 | 7 | 44 | 0,58 | 0,16 | 0,25 |
| E4 | 24 | 17 | 44 | 0,71 | 0,39 | 0,50 |
| **Combinação** | 53 | 42 | 44 | **0,79** | **0,95** | **0,87** |

`--detalhar` lista os falsos positivos e os vínculos não encontrados. Os pesos e limiares ficam em
`app/config.py` (`ANALISE_*`) e devem ser recalibrados com os demais projetos da primeira etapa.

Para criar o gabarito de outro projeto, use o formato:

```json
{"vinculos": [
  {"origem": "RF-01", "destino": "src/app/usuarios.py::Cadastro.cadastrar"},
  {"origem": "tests/test_usuarios.py::test_cadastro", "destino": "src/app/usuarios.py::Cadastro.cadastrar"}
]}
```

## Primeira etapa de avaliação: 4 projetos controlados

A pasta `exemplos/etapa1/` contém o mesmo **sistema de biblioteca** (6 requisitos) implementado em quatro
linguagens e quatro modelos de banco de dados, com gabaritos definidos antes da avaliação:

| Projeto | Linguagem | Banco de dados (modelo) | Requisitos | Testes |
|---|---|---|---|---|
| `biblioteca_python` | Python | PostgreSQL (relacional) | `requisitos.md` | pytest |
| `biblioteca_java` | Java | Neo4j (grafo) | `requisitos.csv` | JUnit 5 |
| `biblioteca_javascript` | JavaScript (Node.js) | MongoDB (documentos) | `requisitos.json` | `node:test` |
| `biblioteca_html` | HTML + JavaScript | localStorage (chave-valor) | tabela em `requisitos.md` | `node:test` + Playwright |

```powershell
python scripts/gerar_gabaritos_etapa1.py   # (re)gera os gabaritos
python scripts/avaliar_etapa1.py           # precisão e revocação dos 4 projetos
python scripts/experimento_localizacao.py  # insere defeitos, executa os testes e localiza a origem
```

Os resultados ficam em `exemplos/etapa1/resultados/`. Resumo com a configuração padrão:

| Linguagem | Precisão | Revocação | F1 |
|---|---:|---:|---:|
| Python | 0,79 | 0,87 | 0,83 |
| Java | 0,73 | 0,86 | 0,79 |
| JavaScript | 0,76 | 0,90 | 0,82 |
| HTML + JavaScript | 0,84 | 0,84 | 0,84 |
| **Total** | **0,78** | **0,86** | **0,82** |

Vínculos com confiança alta (≥ 0,80) tiveram precisão de 0,97. No experimento de localização de erros
(12 defeitos inseridos, 3 por projeto), o requisito correto foi apontado em primeiro lugar em 12 de 12
casos e o elemento defeituoso apareceu entre os suspeitos em 12 de 12.

## Testes automatizados

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Estrutura

```
app/
├── analysis/          # motor de análise (independente do Flask)
│   ├── extrator.py    # Etapa 1
│   ├── requisitos.py  # Etapa 2 — requisitos
│   ├── codigo.py      # Etapa 2 — escolha do leitor + leitor Python (ast/tokenize)
│   ├── codigo_java.py, codigo_js.py, codigo_html.py, codigo_base.py
│   ├── resolvedor.py  # resolução de chamadas
│   ├── texto.py       # pré-processamento para TF-IDF
│   ├── estrategias.py # Etapa 3 — E1 a E4
│   ├── confianca.py   # Etapa 4
│   ├── pipeline.py    # orquestra as etapas
│   ├── localizador.py # Etapa 6 — leitura de tracebacks
│   └── avaliacao.py   # precisão e revocação contra gabarito
├── models.py          # modelo de dados (metamodelo de rastreabilidade)
├── services.py        # persistência, decisões, cobertura e localização de erros
├── views.py, auth.py  # telas
├── seguranca.py       # CSRF e cabeçalhos de segurança
├── templates/, static/
exemplos/              # projeto controlado + gabarito
scripts/               # utilitários
tests/                 # testes automatizados (pytest)
```

## Segurança

- Processamento local, sem dependência de rede durante a execução.
- O código enviado não é executado nem armazenado; o ZIP é apagado após a análise.
- Arquivos sensíveis (`.env`, chaves, credenciais) são ignorados e nunca lidos.
- Senhas guardadas apenas como *hash*; proteção CSRF; cabeçalhos de segurança (CSP, X-Frame-Options).
- Cada usuário acessa apenas os próprios projetos; excluir um projeto remove todos os seus dados.

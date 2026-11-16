"""Motor de análise da ferramenta.

Os módulos deste pacote implementam as etapas descritas no Capítulo 3:

* ``extrator``    — Etapa 1: recepção e extração segura do arquivo ZIP;
* ``requisitos``  — Etapa 2: leitura dos requisitos (expressões regulares);
* ``codigo``      — Etapa 2: leitura do código e dos testes (módulos ast e tokenize);
* ``estrategias`` — Etapa 3: estratégias de vinculação E1 a E4;
* ``confianca``   — Etapa 4: combinação das evidências em um grau de confiança;
* ``localizador`` — Etapa 6: leitura de mensagens de erro (traceback);
* ``pipeline``    — orquestra as etapas e devolve o resultado da análise;
* ``avaliacao``   — cálculo de precisão e revocação contra um gabarito.

Nada aqui depende do Flask ou do banco de dados: o pacote pode ser usado
e testado de forma independente.
"""

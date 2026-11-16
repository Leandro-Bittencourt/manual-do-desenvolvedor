# Requisitos — Loja Virtual (projeto de exemplo)

Projeto controlado usado na primeira etapa de avaliação da ferramenta.

## RF-01 — Cadastro de usuário
O sistema deve permitir cadastrar um usuário com nome, e-mail e senha,
validando o formato do e-mail e impedindo e-mails repetidos.

## RF-02 — Autenticação
O usuário deve entrar no sistema informando e-mail e senha. A senha
informada deve ser conferida com a senha cadastrada.

## RF-03 — Carrinho de compras
O usuário deve adicionar e remover produtos do carrinho, informando a quantidade.

## RF-04 — Cálculo do total com cupom
O sistema deve calcular o valor total do carrinho e aplicar o cupom de desconto quando informado.

## RF-05 — Pagamento
O sistema deve processar o pagamento do pedido com cartão e recusar cartões inválidos.

## RNF-01 — Senhas protegidas
As senhas nunca devem ser armazenadas em texto puro; deve ser guardado apenas o hash da senha.

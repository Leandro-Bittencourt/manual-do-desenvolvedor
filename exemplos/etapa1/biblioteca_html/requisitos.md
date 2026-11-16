# Requisitos — Sistema de Biblioteca

Projeto controlado 4 — HTML + JavaScript no navegador, com armazenamento chave-valor (localStorage).

| ID | Título | Descrição |
|----|--------|-----------|
| RF-01 | Cadastro de livro | O sistema deve cadastrar livros com título, autor e ISBN, validando o ISBN e impedindo o cadastro de um ISBN repetido. |
| RF-02 | Cadastro de leitor | O sistema deve cadastrar leitores com nome e e-mail, validando o formato do e-mail. |
| RF-03 | Empréstimo de livro | O leitor pode pegar um livro emprestado se o livro estiver disponível e se ele tiver menos de 3 empréstimos ativos. |
| RF-04 | Devolução e multa por atraso | Na devolução do livro, o sistema deve calcular a multa de R$ 2,00 por dia de atraso após o prazo de 14 dias. |
| RF-05 | Busca de livros | O sistema deve buscar livros por título ou autor, sem diferenciar letras maiúsculas e minúsculas. |
| RNF-01 | Persistência | Os dados de livros, leitores e empréstimos devem ser gravados no banco de dados. |

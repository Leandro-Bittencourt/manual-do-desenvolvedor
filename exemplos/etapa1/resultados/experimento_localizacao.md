# Experimento de localização de erros — 1ª etapa

| Linguagem | Defeito inserido | Origem apontada | Requisitos apontados | Requisito correto? | Elemento defeituoso entre os suspeitos? |
|---|---|---|---|---|---|
| Python | D1 — cálculo da multa | `test_multa_por_dias_de_atraso` (teste) | RF-04, RF-03 (herdado) | Sim | Sim |
| Python | D2 — exceção na devolução | `ServicoBiblioteca.devolver` (código) | RF-04 | Sim | Sim |
| Python | D3 — exceção na validação do ISBN | `validar_isbn` (código) | RF-01, RF-05 (herdado) | Sim | Sim |
| Java | D1 — cálculo da multa | `EmprestimosTest.multaPorDiasDeAtraso` (teste) | RF-04 | Sim | Sim |
| Java | D2 — exceção na devolução | `ServicoBiblioteca.devolver` (código) | RF-04 | Sim | Sim |
| Java | D3 — exceção na validação do ISBN | `Validacoes.validarIsbn` (código) | RF-01, RF-05 (herdado) | Sim | Sim |
| JavaScript | D1 — cálculo da multa | `Empréstimos e devoluções > multa por dias de atraso` (teste) | RF-04 | Sim | Sim |
| JavaScript | D2 — exceção na devolução | `ServicoBiblioteca.devolver` (código) | RF-04 | Sim | Sim |
| JavaScript | D3 — exceção na validação do ISBN | `validarIsbn` (código) | RF-01, RF-05, RF-02 (herdado) | Sim | Sim |
| HTML + JavaScript | D1 — cálculo da multa | `Empréstimos e devoluções > multa por dias de atraso` (teste) | RF-04 | Sim | Sim |
| HTML + JavaScript | D2 — exceção na devolução | `ServicoBiblioteca.devolver` (código) | RF-04 | Sim | Sim |
| HTML + JavaScript | D3 — exceção na validação do ISBN | `validarIsbn` (código) | RF-01, RF-05 (herdado) | Sim | Sim |

- Requisito correto apontado: 12 de 12 cenários (12 em 1º lugar; 5 herdado(s) pelo grafo de chamadas).
- Elemento defeituoso entre os suspeitos: 12 de 12.
- Origem apontada exatamente no elemento defeituoso: 8 de 12 (nos defeitos de cálculo o erro aparece na asserção do teste, e a ferramenta aponta o teste e o código que ele exercita).

## Mensagens de erro utilizadas

### Python — D1 — cálculo da multa

```
F                                                                        [100%]
================================== FAILURES ===================================
________________________ test_multa_por_dias_de_atraso ________________________
Traceback (most recent call last):
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\runner.py", line 341, in from_call
    result: TResult | None = func()
                             ^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\runner.py", line 242, in <lambda>
    lambda: runtest_hook(item=item, **kwds), when=when, reraise=reraise
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_caller.py", line 197, in __call__
    return self._hookexec(
           ^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_manager.py", line 183, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 195, in _multicall
    raise exception
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 167, in _multicall
    teardown.throw(exception)
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\threadexception.py", line 92, in pytest_runtest_call
    yield from thread_exception_runtest_hook()
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\threadexception.py", line 68, in thread_exception_runtest_hook
    yield
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 167, in _multicall
```

### Python — D2 — exceção na devolução

```
F                                                                        [100%]
================================== FAILURES ===================================
___________________ test_devolucao_no_prazo_nao_gera_multa ____________________
Traceback (most recent call last):
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\runner.py", line 341, in from_call
    result: TResult | None = func()
                             ^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\runner.py", line 242, in <lambda>
    lambda: runtest_hook(item=item, **kwds), when=when, reraise=reraise
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_caller.py", line 197, in __call__
    return self._hookexec(
           ^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_manager.py", line 183, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 195, in _multicall
    raise exception
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 167, in _multicall
    teardown.throw(exception)
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\threadexception.py", line 92, in pytest_runtest_call
    yield from thread_exception_runtest_hook()
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\threadexception.py", line 68, in thread_exception_runtest_hook
    yield
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 167, in _multicall
```

### Python — D3 — exceção na validação do ISBN

```
F                                                                        [100%]
================================== FAILURES ===================================
__________________ test_rf01_cadastra_livro_com_isbn_valido ___________________
Traceback (most recent call last):
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\runner.py", line 341, in from_call
    result: TResult | None = func()
                             ^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\runner.py", line 242, in <lambda>
    lambda: runtest_hook(item=item, **kwds), when=when, reraise=reraise
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_caller.py", line 197, in __call__
    return self._hookexec(
           ^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_manager.py", line 183, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 195, in _multicall
    raise exception
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 167, in _multicall
    teardown.throw(exception)
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\threadexception.py", line 92, in pytest_runtest_call
    yield from thread_exception_runtest_hook()
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\_pytest\threadexception.py", line 68, in thread_exception_runtest_hook
    yield
  File "C:\Users\lapsb\Downloads\manual-do-desenvolvedor\.venv\Lib\site-packages\pluggy\_execution.py", line 167, in _multicall
```

### Java — D1 — cálculo da multa

```
org.opentest4j.AssertionFailedError: expected: <6.0> but was: <9.0>
	at org.junit.jupiter.api.AssertionFailureBuilder.build(AssertionFailureBuilder.java:151)
	at org.junit.jupiter.api.AssertionFailureBuilder.buildAndThrow(AssertionFailureBuilder.java:132)
	at org.junit.jupiter.api.AssertEquals.failNotEqual(AssertEquals.java:197)
	at org.junit.jupiter.api.AssertEquals.assertEquals(AssertEquals.java:70)
	at org.junit.jupiter.api.AssertEquals.assertEquals(AssertEquals.java:65)
	at org.junit.jupiter.api.Assertions.assertEquals(Assertions.java:889)
	at br.biblioteca.EmprestimosTest.multaPorDiasDeAtraso(EmprestimosTest.java:56)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:569)
	at ExecutorTestes.main(ExecutorTestes.java:10)
```

### Java — D2 — exceção na devolução

```
java.util.NoSuchElementException: No value present
	at java.base/java.util.Optional.orElseThrow(Optional.java:377)
	at br.biblioteca.servico.ServicoBiblioteca.devolver(ServicoBiblioteca.java:67)
	at br.biblioteca.EmprestimosTest.devolucaoNoPrazoNaoGeraMulta(EmprestimosTest.java:49)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:569)
	at ExecutorTestes.main(ExecutorTestes.java:10)
```

### Java — D3 — exceção na validação do ISBN

```
java.lang.StringIndexOutOfBoundsException: begin 14, end 13, length 13
	at java.base/java.lang.String.checkBoundsBeginEnd(String.java:4606)
	at java.base/java.lang.String.substring(String.java:2709)
	at java.base/java.lang.String.substring(String.java:2682)
	at br.biblioteca.servico.Validacoes.validarIsbn(Validacoes.java:14)
	at br.biblioteca.servico.ServicoBiblioteca.cadastrarLivro(ServicoBiblioteca.java:26)
	at br.biblioteca.LivrosTest.rf01CadastraLivroComIsbnValido(LivrosTest.java:17)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:569)
	at ExecutorTestes.main(ExecutorTestes.java:10)
```

### JavaScript — D1 — cálculo da multa

```
▶ Empréstimos e devoluções
  ✖ multa por dias de atraso (2.4359ms)
✖ Empréstimos e devoluções (3.3626ms)
ℹ tests 1
ℹ suites 1
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 100.1391

✖ failing tests:

test at test\emprestimos.test.js:42:3
✖ multa por dias de atraso (2.4359ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  9 !== 6
  
      at TestContext.<anonymous> (file:///C:/Users/lapsb/AppData/Local/Temp/tmpi2mwxyy3/biblioteca_javascript/test/emprestimos.test.js:44:12)
      at async Test.run (node:internal/test_runner/test:980:9)
      at async Promise.all (index 3)
      at async Suite.run (node:internal/test_runner/test:1358:7)
      at async startSubtestAfterBootstrap (node:internal/test_runner/harness:296:3) {
```

### JavaScript — D2 — exceção na devolução

```
▶ Empréstimos e devoluções
  ✖ devolução no prazo não gera multa (1.3179ms)
✖ Empréstimos e devoluções (1.9452ms)
ℹ tests 1
ℹ suites 1
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 127.4131

✖ failing tests:

test at test\emprestimos.test.js:36:3
✖ devolução no prazo não gera multa (1.3179ms)
  TypeError [Error]: Cannot read properties of undefined (reading 'ativo')
      at ServicoBiblioteca.devolver (file:///C:/Users/lapsb/AppData/Local/Temp/tmp0kir6imu/biblioteca_javascript/src/servicoBiblioteca.js:61:39)
      at async TestContext.<anonymous> (file:///C:/Users/lapsb/AppData/Local/Temp/tmp0kir6imu/biblioteca_javascript/test/emprestimos.test.js:39:18)
      at async Test.run (node:internal/test_runner/test:980:9)
      at async Promise.all (index 2)
      at async Suite.run (node:internal/test_runner/test:1358:7)
      at async startSubtestAfterBootstrap (node:internal/test_runner/harness:296:3)
```

### JavaScript — D3 — exceção na validação do ISBN

```
▶ Cadastro de livros
  ✖ RF-01 cadastra livro com ISBN válido (0.603ms)
✖ Cadastro de livros (1.3589ms)
ℹ tests 1
ℹ suites 1
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 80.9651

✖ failing tests:

test at test\livros.test.js:9:3
✖ RF-01 cadastra livro com ISBN válido (0.603ms)
  TypeError [Error]: isbn.digitos is not iterable
      at validarIsbn (file:///C:/Users/lapsb/AppData/Local/Temp/tmpvtiumka5/biblioteca_javascript/src/validacoes.js:5:28)
      at ServicoBiblioteca.cadastrarLivro (file:///C:/Users/lapsb/AppData/Local/Temp/tmpvtiumka5/biblioteca_javascript/src/servicoBiblioteca.js:15:10)
      at TestContext.<anonymous> (file:///C:/Users/lapsb/AppData/Local/Temp/tmpvtiumka5/biblioteca_javascript/test/livros.test.js:11:33)
      at Test.runInAsyncScope (node:async_hooks:211:14)
      at Test.run (node:internal/test_runner/test:979:25)
      at Test.start (node:internal/test_runner/test:877:17)
      at node:internal/test_runner/test:1356:71
      at node:internal/per_context/primordials:483:82
```

### HTML + JavaScript — D1 — cálculo da multa

```
▶ Empréstimos e devoluções
  ✖ multa por dias de atraso (1.9909ms)
✖ Empréstimos e devoluções (2.6942ms)
ℹ tests 1
ℹ suites 1
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 80.3948

✖ failing tests:

test at test\biblioteca.test.js:68:3
✖ multa por dias de atraso (1.9909ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  9 !== 6
  
      at TestContext.<anonymous> (file:///C:/Users/lapsb/AppData/Local/Temp/tmplqg01q65/biblioteca_html/test/biblioteca.test.js:70:12)
      at Test.runInAsyncScope (node:async_hooks:211:14)
      at Test.run (node:internal/test_runner/test:979:25)
      at async Promise.all (index 3)
      at async Suite.run (node:internal/test_runner/test:1358:7)
```

### HTML + JavaScript — D2 — exceção na devolução

```
▶ Empréstimos e devoluções
  ✖ devolução no prazo não gera multa (2.2311ms)
✖ Empréstimos e devoluções (3.3479ms)
ℹ tests 1
ℹ suites 1
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 100.9718

✖ failing tests:

test at test\biblioteca.test.js:62:3
✖ devolução no prazo não gera multa (2.2311ms)
  TypeError [Error]: Cannot read properties of undefined (reading 'ativo')
      at ServicoBiblioteca.devolver (file:///C:/Users/lapsb/AppData/Local/Temp/tmpzckdd0qe/biblioteca_html/js/biblioteca.js:85:39)
      at TestContext.<anonymous> (file:///C:/Users/lapsb/AppData/Local/Temp/tmpzckdd0qe/biblioteca_html/test/biblioteca.test.js:65:26)
      at Test.runInAsyncScope (node:async_hooks:211:14)
      at Test.run (node:internal/test_runner/test:979:25)
      at async Promise.all (index 2)
      at async Suite.run (node:internal/test_runner/test:1358:7)
      at async startSubtestAfterBootstrap (node:internal/test_runner/harness:296:3)
```

### HTML + JavaScript — D3 — exceção na validação do ISBN

```
▶ Cadastro de livros
  ✖ RF-01 cadastra livro com ISBN válido (0.8073ms)
✖ Cadastro de livros (1.6758ms)
ℹ tests 1
ℹ suites 1
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 95.2627

✖ failing tests:

test at test\biblioteca.test.js:20:3
✖ RF-01 cadastra livro com ISBN válido (0.8073ms)
  TypeError [Error]: isbn.digitos is not iterable
      at validarIsbn (file:///C:/Users/lapsb/AppData/Local/Temp/tmprrj980bb/biblioteca_html/js/biblioteca.js:10:28)
      at ServicoBiblioteca.cadastrarLivro (file:///C:/Users/lapsb/AppData/Local/Temp/tmprrj980bb/biblioteca_html/js/biblioteca.js:40:10)
      at TestContext.<anonymous> (file:///C:/Users/lapsb/AppData/Local/Temp/tmprrj980bb/biblioteca_html/test/biblioteca.test.js:21:26)
      at Test.runInAsyncScope (node:async_hooks:211:14)
      at Test.run (node:internal/test_runner/test:979:25)
      at async Promise.all (index 0)
      at async Suite.run (node:internal/test_runner/test:1358:7)
      at async startSubtestAfterBootstrap (node:internal/test_runner/harness:296:3)
```


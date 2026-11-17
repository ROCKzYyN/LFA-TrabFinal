# Gerador de AFD

Aplicacao em Python para carregar sentencas e Gramaticas Regulares,
gerar o AFND, determinizar, remover estados inalcancaveis e mortos e
adicionar o estado de erro.

## Executar

Interface grafica:

```powershell
python main.py --gui
```

Linha de comando:

```powershell
python main.py exemplo.txt -o afd.txt
```

## Formato de entrada

Cada linha sem producao de gramatica representa uma sentenca. As
producoes usam a notacao BNF/gramatica regular, por exemplo:

```text
se
entao
senao

<S> ::= a<A> | e<A> | i<A> | o<A> | u<A>
<A> ::= a<A> | e<A> | i<A> | o<A> | u<A> | ε
```

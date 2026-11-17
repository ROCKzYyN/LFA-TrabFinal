"""Análise (parsing) do texto de entrada: tokens e gramáticas regulares em BNF.

Formato da entrada:
    - Linha comum         -> token (palavra reservada, ex.: "se")
    - Linhas "<A> ::= ..." -> uma gramática regular (GR)
    - Linha em branco     -> separa uma GR da próxima
    - A primeira variável de cada GR é o símbolo inicial dela.
"""

from __future__ import annotations

import re

# "<S> ::= corpo"  -> grupo 1 = nome da variável, grupo 2 = corpo da produção
BNF_LINE = re.compile(r"^<([^<>\s]+)>\s*::=\s*(.*)$")
# "<A>" sozinho
NONTERMINAL = re.compile(r"^<([^<>\s]+)>$")


def parse_symbols(text: str) -> list[str]:
    """Quebra uma alternativa em símbolos: terminais (1 char) e variáveis '<N>'.

    Exemplo: "ab<A>" -> ["a", "b", "<A>"].  "ε" -> [] (cadeia vazia).
    """
    compact = "".join(text.split())  # ignora espaços
    if compact == "ε":
        return []
    if not compact:
        raise ValueError("Alternativa vazia: use ε para representar a cadeia vazia.")

    symbols: list[str] = []
    position = 0
    while position < len(compact):
        char = compact[position]
        if char == "<":
            end = compact.find(">", position + 1)
            if end < 0:
                raise ValueError(f"Variável BNF sem '>': {text!r}")
            token = compact[position : end + 1]
            if not NONTERMINAL.fullmatch(token):
                raise ValueError(f"Variável BNF inválida: {token!r}")
            symbols.append(token)
            position = end + 1
        elif char == ">" or char == "ε":
            raise ValueError(f"Símbolo inválido na produção {text!r}. Use ε isoladamente.")
        else:
            symbols.append(char)  # terminal
            position += 1
    return symbols


def split_alternatives(body: str) -> list[str]:
    """Separa "a<A> | b | ε" nas alternativas por '|'."""
    alternatives = [part.strip() for part in body.split("|")]
    if not all(alternatives):
        raise ValueError("Produção com alternativa vazia; escreva ε explicitamente.")
    return alternatives


def grammar_direction(productions: dict[str, list[str]]) -> str:
    """Valida que a gramática é regular e devolve 'right' ou 'left'.

    Regras de uma GR linear:
      - no máximo UMA variável por alternativa;
      - a variável fica no fim (linear à direita: aA)
        ou no início (linear à esquerda: Aa);
      - não se pode misturar as duas orientações na mesma GR.
    Produções unitárias (<A> ::= <B>) valem nas duas orientações.
    """
    direction = None
    for name, alternatives in productions.items():
        for alternative in alternatives:
            symbols = parse_symbols(alternative)
            variables = [(index, s[1:-1]) for index, s in enumerate(symbols)
                         if NONTERMINAL.fullmatch(s)]
            if len(variables) > 1:
                raise ValueError(
                    f"Produção <{name}> ::= {alternative} não é regular: "
                    "cada alternativa pode conter no máximo uma variável."
                )
            if variables:
                index, target = variables[0]
                if target not in productions:
                    raise ValueError(f"Variável <{target}> usada, mas não definida na gramática.")
                if index not in (0, len(symbols) - 1):
                    raise ValueError(
                        f"Produção <{name}> ::= {alternative} não é regular: "
                        "a variável deve ficar no início ou no final."
                    )
                if len(symbols) > 1:  # unitária não define orientação
                    current = "left" if index == 0 else "right"
                    if direction is not None and current != direction:
                        raise ValueError(
                            "A gramática mistura produções lineares à esquerda e à direita. "
                            "Use uma única orientação em cada bloco de GR."
                        )
                    direction = current
    return direction or "right"


def parse_regular_grammar(text: str) -> dict[str, list[str]]:
    """Lê UM bloco de GR e devolve {variável: [alternativas]}. 1ª variável = inicial."""
    productions: dict[str, list[str]] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = BNF_LINE.fullmatch(line)
        if not match:
            raise ValueError(f"Linha {line_number}: produção BNF inválida: {line!r}.")
        name, body = match.groups()
        try:
            alternatives = split_alternatives(body)
        except ValueError as exc:
            raise ValueError(f"Linha {line_number}: {exc}") from exc
        # setdefault permite definir a mesma variável em várias linhas
        productions.setdefault(name, []).extend(alternatives)
    if productions:
        grammar_direction(productions)  # só valida; levanta ValueError se inválida
    return productions


def parse_source(text: str) -> tuple[list[str], list[dict[str, list[str]]]]:
    """Separa o arquivo inteiro em (lista de tokens, lista de GRs)."""
    tokens: list[str] = []
    grammars: list[dict[str, list[str]]] = []
    grammar_lines: list[str] = []  # linhas BNF do bloco atual

    def finish_grammar() -> None:
        """Fecha o bloco de GR em andamento (se houver)."""
        if grammar_lines:
            grammars.append(parse_regular_grammar("\n".join(grammar_lines)))
            grammar_lines.clear()

    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:  # linha em branco encerra a GR atual
            finish_grammar()
            continue
        if BNF_LINE.fullmatch(line):
            grammar_lines.append(line)
        else:
            finish_grammar()
            if "::=" in line and line.startswith("<"):
                raise ValueError(f"Linha {line_number}: regra BNF inválida: {line!r}.")
            tokens.append(line)  # qualquer outra linha é um token
    finish_grammar()

    if not tokens and not grammars:
        raise ValueError("Arquivo vazio: informe pelo menos um token ou uma GR em BNF.")
    return tokens, grammars

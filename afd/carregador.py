"""Converte tokens e gramáticas regulares em um único AFND.

Todos os tokens e GRs compartilham o MESMO estado inicial q0, de modo que o
AFND resultante reconhece a união das linguagens.
"""

from __future__ import annotations

from typing import Iterable

from .analisador import NONTERMINAL, grammar_direction, parse_symbols
from .automato import EPSILON, FiniteAutomaton


class LanguageLoader:
    def __init__(self) -> None:
        self._next_state = 1  # contador para nomear q1, q2, ...
        self.nfa = FiniteAutomaton({"q0"}, set(), "q0", set())

    def new_state(self) -> str:
        """Cria e registra um estado novo (q1, q2, ...)."""
        name = f"q{self._next_state}"
        self._next_state += 1
        self.nfa.states.add(name)
        return name

    # ------------------------------------------------------------------ tokens
    def load_tokens(self, tokens: Iterable[str]) -> None:
        """Cada token vira uma cadeia de estados: q0 -a-> q1 -b-> q2 (final).

        Só q0 é compartilhado; mesmo com prefixos iguais criamos estados
        novos (a determinização depois junta o que for preciso).
        """
        for token in tokens:
            if not token:
                raise ValueError("Token vazio: represente ε por uma GR.")
            current = self.nfa.start
            for symbol in token:
                destination = self.new_state()
                self.nfa.add_transition(current, symbol, destination)
                current = destination
            self.nfa.finals.add(current)

    # ---------------------------------------------------------------- gramática
    def load_grammar(self, productions: dict[str, list[str]]) -> None:
        """Gramática linear à direita -> AFND (cada variável vira um estado)."""
        if not productions:
            return
        if grammar_direction(productions) == "left":
            self.load_left_linear_grammar(productions)
            return

        start_name = next(iter(productions))

        # Se a variável inicial aparece no lado direito de alguma regra,
        # usar q0 para ela faria o ciclo "vazar" para os outros tokens/GRs.
        # Nesse caso criamos uma cópia privada e ligamos q0 -ε-> cópia.
        recursive_start = any(
            f"<{start_name}>" in parse_symbols(alt)
            for alternatives in productions.values()
            for alt in alternatives
        )

        # Um estado por variável (a inicial reaproveita q0 quando possível)
        states: dict[str, str] = {}
        for name in productions:
            if name == start_name and not recursive_start:
                states[name] = self.nfa.start
            else:
                states[name] = self.new_state()
        if recursive_start:
            self.nfa.add_transition(self.nfa.start, EPSILON, states[start_name])

        for name, alternatives in productions.items():
            source = states[name]
            for alternative in alternatives:
                symbols = parse_symbols(alternative)

                if not symbols:  # <A> ::= ε  -> A é estado final
                    self.nfa.finals.add(source)
                    continue

                # Separa a variável do final (se houver): "ab<A>" -> "ab" + A
                target_var = None
                if NONTERMINAL.fullmatch(symbols[-1]):
                    target_var = symbols.pop()[1:-1]

                if not symbols:  # <A> ::= <B>  (unitária) -> transição ε
                    self.nfa.add_transition(source, EPSILON, states[target_var])
                    continue

                # Percorre os terminais criando estados intermediários.
                current = source
                for index, symbol in enumerate(symbols):
                    # A última letra de "w<A>" já vai direto para o estado de A.
                    last = index == len(symbols) - 1
                    destination = (states[target_var] if last and target_var
                                   else self.new_state())
                    self.nfa.add_transition(current, symbol, destination)
                    current = destination

                if target_var is None:  # só terminais: termina em estado final
                    self.nfa.finals.add(current)

    def load_left_linear_grammar(self, productions: dict[str, list[str]]) -> None:
        """Gramática linear à esquerda (<A> ::= <B>w | w | ε).

        Lê-se a derivação "ao contrário": o estado global q0 inicia as regras
        base (sem variável) e a variável inicial da GR é o estado FINAL.
        """
        states = {name: self.new_state() for name in productions}
        start_variable = next(iter(productions))
        self.nfa.finals.add(states[start_variable])

        for name, alternatives in productions.items():
            for alternative in alternatives:
                symbols = parse_symbols(alternative)

                if not symbols:  # <A> ::= ε  -> q0 -ε-> A
                    self.nfa.add_transition(self.nfa.start, EPSILON, states[name])
                    continue

                # Se começa com variável, a origem é o estado dela; senão, q0.
                first_is_var = bool(NONTERMINAL.fullmatch(symbols[0]))
                source = states[symbols.pop(0)[1:-1]] if first_is_var else self.nfa.start

                if not symbols:  # <A> ::= <B>  (unitária)
                    self.nfa.add_transition(source, EPSILON, states[name])
                    continue

                current = source
                for index, symbol in enumerate(symbols):
                    last = index == len(symbols) - 1
                    destination = states[name] if last else self.new_state()
                    self.nfa.add_transition(current, symbol, destination)
                    current = destination

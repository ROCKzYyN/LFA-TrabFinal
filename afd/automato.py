"""Estrutura de dados do autômato finito (serve para AFND e AFD)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Uma transição ε (vazia) é representada internamente por string vazia.
EPSILON = ""


@dataclass
class FiniteAutomaton:
    """Autômato finito M = (Q, Σ, δ, q0, F).

    transitions mapeia (estado, símbolo) -> CONJUNTO de destinos.
    Num AFD cada conjunto tem 1 elemento; num AFND pode ter vários
    e o símbolo EPSILON ("") é permitido.
    """

    states: set[str]                 # Q: estados
    alphabet: set[str]               # Σ: alfabeto (nunca contém ε)
    start: str                       # q0: estado inicial
    finals: set[str]                 # F: estados finais
    transitions: dict[tuple[str, str], set[str]] = field(default_factory=dict)  # δ

    def add_transition(self, source: str, symbol: str, destination: str) -> None:
        """Adiciona δ(source, symbol) ∋ destination, registrando estados/alfabeto."""
        self.states.update((source, destination))
        if symbol:  # ε não faz parte do alfabeto
            self.alphabet.add(symbol)
        self.transitions.setdefault((source, symbol), set()).add(destination)

    def destinations(self, source: str, symbol: str) -> set[str]:
        """Destinos de (source, symbol); conjunto vazio se não houver transição."""
        return set(self.transitions.get((source, symbol), set()))


def sort_state(name: str) -> tuple[int, int, str]:
    """Chave de ordenação: q1, q2, ..., q10 (numérica), depois outros, ERRO por último."""
    if name == "ERRO":
        return (2, 0, "")
    match = re.fullmatch(r"[qD](\d+)", name)
    if match:
        return (0, int(match.group(1)), name)
    return (1, 0, name)

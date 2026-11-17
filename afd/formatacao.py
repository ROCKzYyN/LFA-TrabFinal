"""Montagem das tabelas de transição (texto puro e dados para a GUI)."""

from __future__ import annotations

from .automato import EPSILON, FiniteAutomaton, sort_state


def _symbols(automaton: FiniteAutomaton, nfa: bool) -> list[str]:
    """Colunas da tabela. Para AFND com transições ε, ε vem primeiro."""
    has_epsilon = nfa and any(key[1] == EPSILON for key in automaton.transitions)
    return ([EPSILON] if has_epsilon else []) + sorted(automaton.alphabet)


def format_transition_table(automaton: FiniteAutomaton, *, nfa: bool = False) -> str:
    """Tabela em texto alinhado. '->' marca o estado inicial."""
    symbols = _symbols(automaton, nfa)
    headers = ["Estado", "Final"] + ["ε" if s == EPSILON else s for s in symbols]
    rows = [headers]
    for state in sorted(automaton.states, key=sort_state):
        label = ("->" if state == automaton.start else "  ") + state
        row = [label, "Sim" if state in automaton.finals else "Não"]
        for symbol in symbols:
            destinations = sorted(automaton.destinations(state, symbol), key=sort_state)
            row.append(", ".join(destinations) if destinations else "-")
        rows.append(row)
    # largura de cada coluna = maior célula dela
    widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    return "\n".join(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
                     for row in rows)


def format_gui_table(automaton: FiniteAutomaton, *,
                     nfa: bool = False) -> tuple[list[str], list[list[str]]]:
    """Devolve (cabeçalhos, linhas) para o Treeview. '→' inicial, '*' final."""
    symbols = _symbols(automaton, nfa)
    headers = ["δ"] + ["ε" if s == EPSILON else s for s in symbols]
    rows: list[list[str]] = []
    for state in sorted(automaton.states, key=sort_state):
        marker = ""
        if state == automaton.start:
            marker += "→ "
        if state in automaton.finals:
            marker += "*"
        row = [f"{marker}{state}"]
        for symbol in symbols:
            destinations = sorted(automaton.destinations(state, symbol), key=sort_state)
            row.append(", ".join(destinations) if destinations else "-")
        rows.append(row)
    return headers, rows

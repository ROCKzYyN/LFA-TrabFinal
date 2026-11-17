"""Algoritmos sobre autômatos: determinização, limpeza, minimização e erro."""

from __future__ import annotations

from collections import deque
from typing import Iterable

from .automato import EPSILON, FiniteAutomaton


def epsilon_closure(nfa: FiniteAutomaton, states: Iterable[str]) -> frozenset[str]:
    """ε-fecho: todos os estados alcançáveis a partir de `states` só por ε."""
    result = set(states)
    pending = list(result)  # pilha de estados ainda a explorar
    while pending:
        for target in nfa.destinations(pending.pop(), EPSILON):
            if target not in result:
                result.add(target)
                pending.append(target)
    return frozenset(result)


def determinize(nfa: FiniteAutomaton) -> FiniteAutomaton:
    """Construção dos subconjuntos (AFND com ε -> AFD).

    Cada estado do AFD (D0, D1, ...) representa um CONJUNTO de estados do AFND.
    Transições inexistentes são omitidas (o estado de erro vem só no final).
    """
    initial = epsilon_closure(nfa, [nfa.start])
    names: dict[frozenset[str], str] = {initial: "D0"}  # conjunto -> nome
    pending = deque([initial])                          # fila (BFS)
    dfa = FiniteAutomaton({"D0"}, set(nfa.alphabet), "D0", set())

    while pending:
        subset = pending.popleft()
        current = names[subset]
        if subset & nfa.finals:  # basta conter um final do AFND
            dfa.finals.add(current)
        for symbol in sorted(nfa.alphabet):
            # move(subset, symbol): união dos destinos de cada estado
            moved: set[str] = set()
            for state in subset:
                moved.update(nfa.destinations(state, symbol))
            destination = epsilon_closure(nfa, moved)
            if not destination:
                continue
            if destination not in names:  # conjunto novo -> novo estado
                names[destination] = f"D{len(names)}"
                dfa.states.add(names[destination])
                pending.append(destination)
            dfa.add_transition(current, symbol, names[destination])
    return dfa


def remove_unreachable_and_dead(dfa: FiniteAutomaton) -> FiniteAutomaton:
    """Mantém só estados ALCANÇÁVEIS (a partir do início) e VIVOS (chegam a um final)."""
    # 1) Alcançáveis: busca em profundidade a partir do estado inicial.
    reachable: set[str] = set()
    pending = [dfa.start]
    while pending:
        source = pending.pop()
        if source in reachable:
            continue
        reachable.add(source)
        for symbol in dfa.alphabet:
            pending.extend(dfa.destinations(source, symbol))

    # 2) Vivos: busca nas arestas INVERTIDAS, partindo dos finais.
    reverse_edges: dict[str, set[str]] = {state: set() for state in dfa.states}
    for (source, symbol), targets in dfa.transitions.items():
        if symbol in dfa.alphabet:
            for target in targets:
                reverse_edges[target].add(source)
    productive = set(dfa.finals)
    pending = list(productive)
    while pending:
        for predecessor in reverse_edges[pending.pop()]:
            if predecessor not in productive:
                productive.add(predecessor)
                pending.append(predecessor)

    keep = reachable & productive
    keep.add(dfa.start)  # linguagem vazia ainda precisa de estado inicial
    filtered = FiniteAutomaton(keep, set(dfa.alphabet), dfa.start, dfa.finals & keep)
    for (source, symbol), targets in dfa.transitions.items():
        if source in keep:
            for target in targets & keep:
                filtered.add_transition(source, symbol, target)
    return filtered


def reverse_automaton(automaton: FiniteAutomaton) -> FiniteAutomaton:
    """Autômato reverso: inverte setas; finais viram início, início vira final.

    Como pode haver vários finais, cria-se um novo início "REV" com
    transições ε para cada final antigo.
    """
    new_start = "REV"
    while new_start in automaton.states:  # evita colisão de nome
        new_start += "_"
    reverse = FiniteAutomaton(
        set(automaton.states) | {new_start},
        set(automaton.alphabet),
        new_start,
        {automaton.start},  # o início antigo é o único final
    )
    for (source, symbol), targets in automaton.transitions.items():
        for target in targets:
            reverse.add_transition(target, symbol, source)  # seta invertida
    for final in automaton.finals:
        reverse.add_transition(new_start, EPSILON, final)
    return reverse


def minimize_without_equivalence(dfa: FiniteAutomaton) -> FiniteAutomaton:
    """Minimização de Brzozowski: (reverter + determinizar) duas vezes.

    O resultado é o AFD mínimo, sem usar classes de equivalência/partições.
    """
    reversed_dfa = determinize(reverse_automaton(dfa))
    minimized = determinize(reverse_automaton(reversed_dfa))
    return remove_unreachable_and_dead(minimized)


def add_error_state(dfa: FiniteAutomaton) -> FiniteAutomaton:
    """Completa o AFD: toda transição faltante vai para ERRO (sorvedouro não final)."""
    result = FiniteAutomaton(set(dfa.states) | {"ERRO"}, set(dfa.alphabet),
                             dfa.start, set(dfa.finals))
    for (source, symbol), targets in dfa.transitions.items():
        for target in targets:
            result.add_transition(source, symbol, target)
    for state in dfa.states:
        for symbol in dfa.alphabet:
            if not result.destinations(state, symbol):
                result.add_transition(state, symbol, "ERRO")
    for symbol in dfa.alphabet:  # ERRO nunca sai de ERRO
        result.add_transition("ERRO", symbol, "ERRO")
    return result

"""Junta todas as etapas: texto -> AFND -> AFD -> mínimo -> final com ERRO."""

from __future__ import annotations

from dataclasses import dataclass

from .algoritmos import (add_error_state, determinize,
                         minimize_without_equivalence, remove_unreachable_and_dead)
from .analisador import parse_source
from .automato import FiniteAutomaton
from .carregador import LanguageLoader


@dataclass
class GenerationResult:
    """Guarda o autômato de cada etapa (útil para exibir passo a passo)."""
    nfa: FiniteAutomaton        # 1. AFND
    dfa: FiniteAutomaton        # 2. AFD determinizado
    minimized: FiniteAutomaton  # 3. AFD mínimo (sem ERRO)
    final: FiniteAutomaton      # 4. AFD mínimo + estado ERRO


def generate_steps(source_text: str) -> GenerationResult:
    tokens, grammars = parse_source(source_text)

    loader = LanguageLoader()
    loader.load_tokens(tokens)
    for grammar in grammars:
        loader.load_grammar(grammar)

    dfa = determinize(loader.nfa)
    useful = remove_unreachable_and_dead(dfa)
    minimized = minimize_without_equivalence(useful)
    final = add_error_state(minimized)
    return GenerationResult(loader.nfa, dfa, minimized, final)


def generate(source_text: str) -> tuple[FiniteAutomaton, FiniteAutomaton]:
    """Compatibilidade com a interface do projeto original: (AFND, AFD final)."""
    result = generate_steps(source_text)
    return result.nfa, result.final

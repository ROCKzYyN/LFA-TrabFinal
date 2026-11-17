"""Interface de linha de comando."""

from __future__ import annotations

import sys
from pathlib import Path

from .formatacao import format_transition_table
from .pipeline import generate_steps


def run_cli(source_path: str | None, output_path: str | None,
            show_steps: bool = False) -> int:
    """Lê a entrada (arquivo ou stdin), gera o AFD e imprime/salva a tabela.

    Retorna 0 em sucesso e 1 em erro (usado como código de saída do programa).
    """
    try:
        source = (Path(source_path).read_text(encoding="utf-8-sig") if source_path
                  else sys.stdin.read())
        result = generate_steps(source)
        if show_steps:
            stages = (
                ("AFND de carga", result.nfa, True),
                ("AFD determinizado", result.dfa, False),
                ("AFD mínimo, sem ERRO", result.minimized, False),
                ("AFD final com ERRO", result.final, False),
            )
            text = "\n\n".join(f"== {name} ==\n{format_transition_table(af, nfa=is_nfa)}"
                               for name, af, is_nfa in stages)
        else:
            text = format_transition_table(result.final)
        if output_path:
            Path(output_path).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

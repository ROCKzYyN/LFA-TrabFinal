"""Ponto de entrada do Gerador de AFD (toda a lógica está no pacote `afd/`).

Uso:
    python main.py --gui
    python main.py entrada.txt
    python main.py entrada.txt -o saida.txt
    python main.py entrada.txt --etapas
"""

import argparse
import sys

from afd.cli import run_cli


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerador de AFD mínimo sem classes de equivalência")
    parser.add_argument("arquivo", nargs="?", help="Arquivo de tokens e/ou GRs em BNF")
    parser.add_argument("-o", "--saida", help="Arquivo de saída .txt")
    parser.add_argument("--gui", action="store_true", help="Abre a interface gráfica")
    parser.add_argument("--etapas", action="store_true", help="Mostra AFND, AFD, mínimo e final")
    args = parser.parse_args()

    # Sem arquivo e sem entrada redirecionada -> abre a GUI.
    if args.gui or (args.arquivo is None and sys.stdin.isatty()):
        from afd.gui import Application  # importa Tkinter só quando necessário
        Application().mainloop()
    else:
        raise SystemExit(run_cli(args.arquivo, args.saida, args.etapas))


if __name__ == "__main__":
    main()

"""Interface gráfica (Tkinter): entrada à esquerda, 4 abas de tabelas à direita."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .automato import FiniteAutomaton
from .formatacao import format_gui_table, format_transition_table
from .pipeline import GenerationResult, generate_steps

DEFAULT_EXAMPLE = (
    "se\nentao\nsenao\n\n"
    "<S> ::= a<A> | e<A> | i<A> | o<A> | u<A>\n"
    "<A> ::= a<A> | e<A> | i<A> | o<A> | u<A> | ε\n"
)

TAB_TITLES = ("1. AFND", "2. Determinizado", "3. Mínimo", "4. Final + erro")


class Application(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gerador de AFD — Linguagens Formais e Autômatos")
        self.geometry("1130x680")
        self.minsize(760, 480)
        self.result: GenerationResult | None = None  # último resultado gerado

        style = ttk.Style(self)
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10),
                        borderwidth=1, relief="solid")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # Barra de botões
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Button(top, text="Abrir arquivo", command=self.open_file).pack(side="left")
        ttk.Button(top, text="Gerar AFD", command=self.generate).pack(side="left", padx=6)
        ttk.Button(top, text="Salvar tabela final", command=self.save_table).pack(side="left")

        self.status = tk.StringVar(value="Informe tokens/GRs e clique em Gerar AFD.")
        ttk.Label(self, textvariable=self.status, padding=(8, 3)).pack(fill="x")

        # Painel dividido: entrada | abas
        panels = ttk.PanedWindow(self, orient="horizontal")
        panels.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Labelframe(panels, text="Tokens e gramáticas regulares (BNF)")
        right = ttk.Frame(panels)
        panels.add(left, weight=2)
        panels.add(right, weight=3)

        self.input_text = tk.Text(left, wrap="none", font=("Consolas", 10))
        self.input_text.pack(fill="both", expand=True)
        self.input_text.insert("1.0", DEFAULT_EXAMPLE)

        # Uma aba por etapa, cada uma com um Treeview (tabela) e barras de rolagem
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)
        self.tables: dict[str, ttk.Treeview] = {}
        for title in TAB_TITLES:
            frame = ttk.Frame(self.tabs, padding=6)
            table = ttk.Treeview(frame, show="headings", selectmode="browse")
            yscroll = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
            xscroll = ttk.Scrollbar(frame, orient="horizontal", command=table.xview)
            table.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
            table.tag_configure("even", background="#f2f6fa")
            table.tag_configure("final", foreground="#155e36", font=("Segoe UI", 10, "bold"))
            table.grid(row=0, column=0, sticky="nsew")
            yscroll.grid(row=0, column=1, sticky="ns")
            xscroll.grid(row=1, column=0, sticky="ew")
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            self.tabs.add(frame, text=title)
            self.tables[title] = table
        ttk.Label(right, text="→ Estado inicial    * Estado final",
                  padding=(8, 4)).pack(anchor="w")
        self.tabs.select(3)

    def fill_table(self, table: ttk.Treeview, automaton: FiniteAutomaton,
                   is_nfa: bool) -> None:
        """Preenche um Treeview com a tabela de transições do autômato."""
        headers, rows = format_gui_table(automaton, nfa=is_nfa)
        table.delete(*table.get_children())
        table.configure(columns=headers)
        for column in headers:
            table.heading(column, text=column)
            table.column(column, width=110 if column == "δ" else 90, minwidth=54,
                         anchor="center", stretch=column == "δ")
        for index, row in enumerate(rows):
            tags: list[str] = []
            if index % 2 == 0:
                tags.append("even")   # listras
            if "*" in row[0]:
                tags.append("final")  # destaca estados finais
            table.insert("", "end", values=row, tags=tags)

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")]
        )
        if not filename:
            return
        try:
            content = Path(filename).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            messagebox.showerror("Erro ao abrir", str(exc))
            return
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", content)
        self.result = None
        self.status.set(f"Arquivo carregado: {Path(filename).name}. Gere o AFD.")

    def generate(self) -> None:
        try:
            result = generate_steps(self.input_text.get("1.0", "end"))
        except ValueError as exc:
            messagebox.showerror("Entrada inválida", str(exc))
            return
        self.result = result
        data = (
            ("1. AFND", result.nfa, True),
            ("2. Determinizado", result.dfa, False),
            ("3. Mínimo", result.minimized, False),
            ("4. Final + erro", result.final, False),
        )
        for title, automaton, is_nfa in data:
            self.fill_table(self.tables[title], automaton, is_nfa)
        self.tabs.select(3)
        self.status.set(
            f"AFND: {len(result.nfa.states)} estados | "
            f"AFD: {len(result.dfa.states)} | "
            f"Mínimo: {len(result.minimized.states)} | "
            f"Final com ERRO: {len(result.final.states)}"
        )

    def save_table(self) -> None:
        if self.result is None:
            messagebox.showinfo("Sem resultado", "Gere o AFD antes de salvar a tabela.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Arquivos de texto", "*.txt")]
        )
        if not filename:
            return
        try:
            Path(filename).write_text(format_transition_table(self.result.final),
                                      encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", str(exc))
            return
        self.status.set(f"Tabela do AFD final salva em {Path(filename).name}.")

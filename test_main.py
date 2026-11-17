import unittest

from main import format_gui_table, generate


class AutomatonTests(unittest.TestCase):
    def run_words(self, dfa, words):
        for word, accepted in words:
            state = dfa.start
            for symbol in word:
                destinations = dfa.destinations(state, symbol)
                if not destinations:
                    state = "ERRO"
                    break
                state = next(iter(destinations))
            self.assertEqual(state in dfa.finals, accepted, word)

    def test_plain_tokens(self):
        _, dfa = generate("se\nentao\nsenao\n")
        self.run_words(dfa, [
            ("se", True),
            ("entao", True),
            ("senao", True),
            ("s", False),
            ("seja", False),
        ])

    def test_regular_grammar_vowel_language(self):
        _, dfa = generate(
            "<S> ::= a<A>\n"
            "<A> ::= a<A> | e<A> | i<A> | o<A> | u<A> | ε\n"
        )
        self.run_words(dfa, [
            ("a", True),
            ("aeiou", True),
            ("b", False),
            ("aa", True),
            ("oa", False),
        ])

    def test_error_state(self):
        _, dfa = generate("a\n")
        self.assertIn("ERRO", dfa.states)
        for state in dfa.states:
            for symbol in dfa.alphabet:
                self.assertTrue(dfa.destinations(state, symbol))

    def test_gui_table_matches_transition_matrix(self):
        _, dfa = generate("a\n")
        headers, rows = format_gui_table(dfa)
        row_by_state = {row[0]: row[1:] for row in rows}

        self.assertEqual(headers, ["δ", "a"])
        self.assertIn("→ D0", row_by_state)
        self.assertEqual(row_by_state["→ D0"], ["D1"])
        self.assertIn("*D1", row_by_state)
        self.assertEqual(row_by_state["*D1"], ["ERRO"])
        self.assertEqual(row_by_state["ERRO"], ["ERRO"])


if __name__ == "__main__":
    unittest.main()

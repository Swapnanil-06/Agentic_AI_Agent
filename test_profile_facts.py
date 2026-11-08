from datetime import date
import ast
from pathlib import Path
from unittest.mock import Mock, patch
from types import SimpleNamespace
import unittest
from profile_facts import education_facts, education_context, factual_reply

NOW = date(2026, 11, 8)


class ProfileFactsTests(unittest.TestCase):
    def test_repeated_introductions_and_user_typo(self):
        for question in ["who is swapnanil", "Who is Swapnanil Chattopadhyay?", "who os swapnanil", "Tell me about yourself"]:
            answer = factual_reply(question, NOW)
            self.assertIn("third-year", answer)
            self.assertNotIn("fourth-year", answer)

    def test_corrections_do_not_change_the_fact(self):
        for question in ["fourth year? or third year?", "but u said 4th to who is swapnanil?", "what year is he in?", "Are you a fourth-year student?"]:
            self.assertIn("third year", factual_reply(question, NOW))

    def test_future_final_year_is_distinguished_from_current_year(self):
        self.assertEqual(education_facts(NOW)["year"], 3)
        self.assertEqual(education_facts(date(2027, 9, 1))["year"], 4)
        self.assertEqual(education_facts(date(2027, 8, 1))["year"], 3)
        self.assertIn("fourth-year", factual_reply("who is swapnanil", date(2027, 10, 1)))

    def test_unknown_completion_is_not_claimed(self):
        self.assertIsNone(education_facts(date(2028, 10, 1))["year"])
        self.assertIn("needs confirmation", factual_reply("who is swapnanil", date(2028, 10, 1)))

    def test_substantive_questions_still_reach_the_agent(self):
        for question in ["What did he build at Mastek?", "Explain the auction algorithm", "What projects might he work on in fourth year?"]:
            self.assertIsNone(factual_reply(question, NOW))

    def test_prompt_makes_the_current_year_authoritative(self):
        self.assertIn("THIRD-YEAR student, not a fourth-year student", education_context(NOW))

    def test_chat_routing_ignores_an_old_wrong_assistant_answer(self):
        # Exercise the actual chat method without loading a CV, API key or model.
        tree = ast.parse(Path(__file__).with_name("app.py").read_text(encoding="utf-8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Me")
        namespace = {"factual_reply": lambda text: factual_reply(text, NOW), "education_context": lambda: education_context(NOW)}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), "app.py", "exec"), namespace)
        agent = namespace["Me"].__new__(namespace["Me"])
        agent.openai = Mock()
        agent.openai.chat.completions.create.side_effect = AssertionError("Known facts must not be regenerated")
        wrong_history = [{"role": "assistant", "content": "I am a fourth-year student."}]
        for question in ["who is swapnanil", "fourth year? or third year?", "but u said 4th to who is swapnanil?", "who os swapnanil", "who is swapnanil"]:
            answer = agent.chat(question, wrong_history)
            self.assertTrue("third-year" in answer or "third year" in answer)
            self.assertNotIn("a fourth-year student", answer)
        agent.openai.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()

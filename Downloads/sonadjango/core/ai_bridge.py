import random

class AIBridgeService:

    def generate_question(self):
        questions = [
            "Tell me about yourself.",
            "Explain Python OOP.",
            "What is Django ORM?",
            "Describe REST API.",
            "What are your strengths?"
        ]

        return random.choice(questions)

    def evaluate_answer(self, answer):

        if len(answer) > 30:
            score = 90
        elif len(answer) > 15:
            score = 75
        else:
            score = 50

        return {
            "score": score,
            "feedback": "Answer evaluated successfully."
        }
    
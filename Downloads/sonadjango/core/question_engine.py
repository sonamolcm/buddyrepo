class QuestionEngine:
    def __init__(self):

        self.questions = {
            "Introduction": [
                "Tell me about yourself.",
                "Introduce yourself."
            ],

            "Experience": [
                "How many years of experience do you have?",
                "Describe your previous project."
            ],

            "Skills": [
                "What programming languages do you know?",
                "Explain Django ORM."
            ],

            "Availability": [
                "When can you join?",
                "Are you available for full-time work?"
            ],

            "Salary": [
                "What is your expected salary?",
                "Are you comfortable with the offered salary?"
            ]
        }
    def get_questions(self, category):
        return self.questions.get(category, [])
    def get_all_categories(self):
        return list(self.questions.keys())

    
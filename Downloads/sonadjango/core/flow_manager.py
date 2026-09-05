from core.question_engine import QuestionEngine


class AIFlowManager:

    def __init__(self):

        self.engine = QuestionEngine()

        self.current_index = 0

        self.category = "Introduction"

    def next_question(self):

        questions = self.engine.get_questions(self.category)

        if self.current_index < len(questions):

            question = questions[self.current_index]

            self.current_index += 1

            return question

        return "Interview Completed"
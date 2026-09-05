from core.models import AIAnswer


class AnswerEvaluationAPI:

    def submit_answer(self, answer):

        return {
            "status": "Success",
            "message": "Answer submitted successfully.",
            "answer": answer
        }

    def retrieve_score(self, score):

        return {
            "status": "Success",
            "score": score
        }
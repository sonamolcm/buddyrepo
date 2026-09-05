from core.ai_bridge import AIBridgeService

class AIServiceLayer:

    def ask_question(self):

        try:

            ai = AIBridgeService()

            question = ai.generate_question()

            return {
                "status": "Success",
                "question": question
            }

        except Exception as e:

            return {
                "status": "Failed",
                "error": str(e)
            }
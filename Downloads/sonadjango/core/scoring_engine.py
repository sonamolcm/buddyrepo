class ScoringEngine:

    def evaluate(self, answer):

        score = 0

        if len(answer) > 20:
            score += 40

        keywords = [
            "python",
            "django",
            "database",
            "orm"
        ]

        matched = 0

        for word in keywords:

            if word.lower() in answer.lower():

                matched += 1

        score += matched * 15

        return {
            "score": min(score,100),
            "matched_keywords": matched
        }
    
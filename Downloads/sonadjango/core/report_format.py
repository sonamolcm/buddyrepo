import json

class ReportFormat:

    def generate_json(self):

        report = {
            "candidate": "Rafia Noufal",
            "ats_score": 88,
            "ai_call_score": 91,
            "status": "Recommended"
        }

        return json.dumps(report, indent=4)

    
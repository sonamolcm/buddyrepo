class FunnelAPI:

    def get_funnel_data(self):
        return {
            "status": "Success",
            "funnel": {
                "Applied": 100,
                "Shortlisted": 60,
                "Interviewed": 35,
                "Selected": 10
            }
        }

    def get_conversion_ratio(self):
        return {
            "shortlisted_rate": 60,
            "interview_rate": 35,
            "selection_rate": 10
        }
    
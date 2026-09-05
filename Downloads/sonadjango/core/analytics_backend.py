class AnalyticsBackend:

    def get_funnel_metrics(self):

        return {
            "Applied": 100,
            "Shortlisted": 60,
            "Interviewed": 35,
            "Selected": 10
        }

    def get_job_performance(self, job_title):

        return {
            "job": job_title,
            "applications": 100,
            "shortlisted": 60,
            "interviewed": 35,
            "selected": 10
        }
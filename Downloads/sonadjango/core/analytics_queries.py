from django.db.models import Count
from core.models import Application


class AnalyticsQueries:

    def get_status_counts(self):
        return Application.objects.values(
            "status"
        ).annotate(
            total=Count("id")
        )

    def get_job_counts(self):
        return Application.objects.values(
            "job__title"
        ).annotate(
            total=Count("id")
        )

    
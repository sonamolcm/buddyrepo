from .models import Application

def check_eligibility(application):

    if (
        application.status == "Selected"
        and application.job.is_active
    ):
        return True

    return False


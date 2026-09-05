from .eligibility import check_eligibility

def trigger_ai_call(application):

    if check_eligibility(application):

        application.call_status = "queued"
        application.save()

        return "AI Call Queued"

    return "Candidate Not Eligible"


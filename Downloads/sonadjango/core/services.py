from .models import Application, ATSScore, CandidateProfile
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailLog
def calculate_ats_score(application_id):
    application = Application.objects.get(id=application_id)

    profile = CandidateProfile.objects.get(
        user=application.candidate.user
    )

    job = application.job

    candidate_skills = [
        skill.strip().lower()
        for skill in profile.skills.split(",")
    ]

    job_skills = [
        skill.strip().lower()
        for skill in job.skills.split(",")
    ]

    matched_skills = set(candidate_skills) & set(job_skills)

    if len(job_skills) > 0:
        skill_score = (len(matched_skills) / len(job_skills)) * 50
    else:
        skill_score = 0

    if job.experience == 0:
        experience_score = 30
    elif profile.experience >= job.experience:
        experience_score = 30
    else:
        experience_score = (
            profile.experience / job.experience
        ) * 30

    if profile.education.lower() == job.education.lower():
        education_score = 20
    else:
        education_score = 0

    total_score = (
        skill_score
        + experience_score
        + education_score
    )

    match_percentage = round(total_score, 2)

    ATSScore.objects.update_or_create(
        application=application,
        defaults={
            "skill_score": skill_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "total_score": total_score,
            "match_percentage": match_percentage,
        },
    )

    return {
        "application_id": application.id,
        "candidate": application.candidate.user.username,
        "job": job.title,
        "skill_score": round(skill_score, 2),
        "experience_score": round(experience_score, 2),
        "education_score": round(education_score, 2),
        "total_score": round(total_score, 2),
        "match_percentage": match_percentage,
    }

def get_ranked_candidates(job_id):
    applications = Application.objects.filter(job_id=job_id)

    ranked_candidates = []

    for application in applications:

        ats = ATSScore.objects.filter(
            application=application
        ).first()

        if ats:
            ranked_candidates.append({
                "candidate": application.candidate.user.username,
                "application_id": application.id,
                "match_percentage": ats.match_percentage,
                "status": application.status
            })

    ranked_candidates.sort(
        key=lambda x: x["match_percentage"],
        reverse=True
    )

    return ranked_candidates

def check_candidate_eligibility(application):

    ats = ATSScore.objects.get(application=application)

    cutoff = application.job.minimum_ats_score

    if ats.match_percentage >= cutoff:
        return True

    return False

def auto_shortlist(application):

    eligible = check_candidate_eligibility(application)

    if eligible:
        application.status = "Shortlisted"
    else:
        application.status = "Rejected"

    application.save()

    return application.status

def send_notification_email(subject, message, recipient):

    try:

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )

        EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            status="Success"
        )

    except Exception:

        EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            status="Failed"
        )
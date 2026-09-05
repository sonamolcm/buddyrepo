from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Employer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)

    def __str__(self):
        return self.company_name


class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    skills = models.CharField(max_length=200)

    def __str__(self):
        return self.user.username

class Job(models.Model):

    JOB_TYPES = [
        ('Full-Time', 'Full-Time'),
        ('Part-Time', 'Part-Time'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
    ]

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    skills = models.CharField(max_length=300)
    experience = models.IntegerField()
    salary_min = models.DecimalField(max_digits=10, decimal_places=2)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=150)
    education = models.CharField(max_length=200, default="Any")
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    minimum_ats_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00
    )

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["location"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.title


class Application(models.Model):

    STATUS_CHOICES = [
    ("Applied", "Applied"),
    ("Shortlisted", "Shortlisted"),
    ("Interview Scheduled", "Interview Scheduled"),
    ("Rejected", "Rejected"),
    ("Selected", "Selected"),
]

    CALL_STATUS = [
    ("queued", "Queued"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("failed", "Failed"),
]

    call_status = models.CharField(
    max_length=20,
    choices=CALL_STATUS,
    default="queued"
)

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    resume_snapshot = models.FileField(
        upload_to="application_resumes/",
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Applied")
    applied_date = models.DateTimeField(auto_now_add=True)
    status_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("candidate", "job")

    def __str__(self):
        return f"{self.candidate} - {self.job}"

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    skills = models.CharField(max_length=200)
    education = models.CharField(max_length=200)
    experience = models.IntegerField()
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)
    size = models.IntegerField()
    verification = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name

class Flag(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    reason = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )


class AuditLog(models.Model):

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
class ATSScore(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="ats_score"
    )

    skill_score = models.FloatField(default=0)

    experience_score = models.FloatField(default=0)

    education_score = models.FloatField(default=0)

    total_score = models.FloatField(default=0)

    match_percentage = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.match_percentage}%"
    
class EmailLog(models.Model):

    recipient = models.EmailField()

    subject = models.CharField(
        max_length=200
    )

    status = models.CharField(
        max_length=20
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.recipient} - {self.status}"

class AIInterviewSession(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="Started")
    transcript = models.JSONField(default=dict)
    def __str__(self):
        return self.session_id

class AIQuestion(models.Model):
    session = models.ForeignKey(AIInterviewSession, on_delete=models.CASCADE)
    question = models.TextField()
    sequence = models.IntegerField()

    def __str__(self):
        return self.question

class AIAnswer(models.Model):
    question = models.ForeignKey(AIQuestion, on_delete=models.CASCADE)
    answer = models.TextField()
    answered_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)
    confidence = models.FloatField(default=0)
    ai_annotation = models.TextField(blank=True)


class CallLog(models.Model):
    session = models.ForeignKey(AIInterviewSession, on_delete=models.CASCADE)
    event = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event

class InterviewSchedule(models.Model):

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE
    )

    interview_date = models.DateField()

    interview_time = models.TimeField()

    status = models.CharField(
        max_length=30,
        default="Scheduled"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.application} - {self.interview_date}"

class ReminderLog(models.Model):

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE
    )

    reminder_type = models.CharField(
        max_length=30
    )

    status = models.CharField(
        max_length=20,
        default="Sent"
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.application} - {self.status}"

class AuditLog(models.Model):

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_days = models.PositiveIntegerField(default=30)
    max_job_posts = models.PositiveIntegerField(default=0)
    ai_analytics = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT
    )
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.plan}"


class PaymentTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    transaction_id = models.CharField(
        max_length=200,
        unique=True
    )
    status = models.CharField(
        max_length=30,
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


class BillingHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    billing_date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user} - {self.amount}"  
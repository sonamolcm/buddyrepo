
from email.mime import application

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Q , Count
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from .models import AuditLog, Flag
from PyPDF2 import PdfReader
from docx import Document
import re
from rest_framework.decorators import api_view
from .serializers import ResumeUploadSerializer
from .services import auto_shortlist
from .services import send_notification_email
from .services import (
    calculate_ats_score,
    get_ranked_candidates
)

from .models import (
    Job,
    Employer,
    Candidate,
    CandidateProfile,
    EmployerProfile,
    Application
)
from .serializers import (
    JobSerializer,
    CandidateProfileSerializer,
    EmployerProfileSerializer,
    ApplicationSerializer
)
from .utils import (
    extract_email,
    extract_phone,
    extract_skills,
    extract_experience,
    extract_education
)
from .permissions import IsEmployer, IsCandidate, IsAdmin
from .pagination import CustomPagination
from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello Zecpath Backend")

class UserTestAPI(APIView):

    def get(self, request):
        return Response({
            "message": "User API Working"
        })


from rest_framework.permissions import AllowAny, IsAuthenticated

class JobListAPI(ListCreateAPIView):

    serializer_class = JobSerializer
    pagination_class = CustomPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter
    ]

    filterset_fields = [
        "location",
        "job_type",
        "experience",
        "is_active",
        "is_featured"
    ]

    search_fields = [
        "title",
        "description",
        "skills"
    ]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]     
        return [IsAuthenticated(), IsEmployer()]   

    def get_queryset(self):
        return Job.objects.filter(
            is_active=True
        ).select_related("employer")

    def perform_create(self, serializer):
        employer = Employer.objects.get(user=self.request.user)
        serializer.save(employer=employer)

class JobCreateAPI(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        serializer = JobSerializer(data=request.data)

        if serializer.is_valid():

            employer = Employer.objects.get(user=request.user)

            serializer.save(employer=employer)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class JobDetailAPI(RetrieveUpdateDestroyAPIView):

    queryset = Job.objects.select_related("employer")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsEmployer]

    def get_object(self):

        job = super().get_object()

        employer = Employer.objects.get(user=self.request.user)

        if job.employer != employer:
            raise PermissionDenied(
                "You are not allowed to modify this job."
            )

        return job


class SignupView(APIView):

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        User.objects.create_user(
            username=username,
            password=password
        )

        return Response({
            "message": "User Created Successfully"
        })


class ProtectedView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "username": request.user.username,
            "user_id": request.user.id,
        })


class EmployerAPI(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):
        return Response({
            "message": "Welcome Employer",
            "username": request.user.username
        })


class CandidateAPI(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):
        return Response({
            "message": "Welcome Candidate"
        })


class AdminAPI(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({
            "message": "Welcome Admin"
        })


class CandidateProfileAPI(ListCreateAPIView):

    queryset = CandidateProfile.objects.select_related("user")
    serializer_class = CandidateProfileSerializer
    pagination_class = CustomPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter
    ]

    filterset_fields = [
        "experience",
        "is_deleted"
    ]

    search_fields = [
        "skills",
        "education"
    ]


class CandidateProfileDetailAPI(RetrieveUpdateDestroyAPIView):

    queryset = CandidateProfile.objects.select_related("user")
    serializer_class = CandidateProfileSerializer


class EmployerProfileAPI(ListCreateAPIView):

    queryset = EmployerProfile.objects.select_related("user")
    serializer_class = EmployerProfileSerializer
    pagination_class = CustomPagination


class EmployerProfileDetailAPI(RetrieveUpdateDestroyAPIView):

    queryset = EmployerProfile.objects.select_related("user")
    serializer_class = EmployerProfileSerializer

class FeaturedJobAPI(APIView):

    def get(self, request):

        jobs = Job.objects.filter(
            is_active=True,
            is_featured=True
        )

        serializer = JobSerializer(jobs, many=True)

        return Response(serializer.data)


class LatestJobAPI(APIView):

    def get(self, request):

        jobs = Job.objects.filter(
            is_active=True
        ).order_by("-created_at")[:10]

        serializer = JobSerializer(jobs, many=True)

        return Response(serializer.data)


class ApplyJobAPI(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request, pk):

        try:
            job = Job.objects.get(pk=pk, is_active=True)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        candidate = Candidate.objects.get(user=request.user)

        if Application.objects.filter(candidate=candidate, job=job).exists():
            return Response(
                {"error": "You have already applied for this job."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApplicationSerializer(data=request.data)

        if serializer.is_valid():

            application = serializer.save(
                candidate=candidate,
                job=job
            )

            send_notification_email(
                subject="Application Submitted",
                message=f"Dear {candidate.user.username},\n\nYour application for '{job.title}' has been submitted successfully.",
                recipient=candidate.user.email
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class MyApplicationsAPI(ListCreateAPIView):

    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsCandidate]
    pagination_class = CustomPagination

    def get_queryset(self):

        candidate = Candidate.objects.get(user=self.request.user)

        return Application.objects.filter(
            candidate=candidate
        ).select_related(
            "candidate",
            "job"
        ).order_by("-applied_date")


class EmployerApplicationsAPI(ListCreateAPIView):

    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    pagination_class = CustomPagination

    def get_queryset(self):

        employer = Employer.objects.get(user=self.request.user)

        return (
            Application.objects.select_related(
                "candidate",
                "job"
            )
            .filter(
                job__employer=employer
            )
            .order_by("-applied_date")
        )
    
class UpdateApplicationStatusAPI(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def patch(self, request, pk):

        try:
            application = Application.objects.get(id=pk)

        except Application.DoesNotExist:

            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        employer = Employer.objects.get(user=request.user)

        if application.job.employer != employer:

            return Response(
                {"error": "This application is not yours"},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get("status")

        allowed_status = [
            "Applied",
            "Shortlisted",
            "Interview Scheduled",
            "Rejected",
            "Selected"
        ]

        if new_status not in allowed_status:

            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        workflow = {
            "Applied": ["Shortlisted", "Rejected"],
            "Shortlisted": ["Interview Scheduled", "Rejected"],
            "Interview Scheduled": ["Selected", "Rejected"],
            "Selected": [],
            "Rejected": []
        }

        current_status = application.status

        if new_status not in workflow[current_status]:

            return Response(
                {
                    "error": f"Cannot move from {current_status} to {new_status}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save()

        if application.status == "Shortlisted":

            send_notification_email(
                subject="Congratulations! You are Shortlisted",
                message=f"Dear {application.candidate.user.username},\n\nCongratulations! You have been shortlisted for the '{application.job.title}' position.",
                recipient=application.candidate.user.email,
            )

        elif application.status == "Rejected":

            send_notification_email(
                subject="Application Update",
                message=f"Dear {application.candidate.user.username},\n\nThank you for applying for the '{application.job.title}' position. We regret to inform you that your application was not selected.",
                recipient=application.candidate.user.email,
            )

        return Response(
            {
                "message": "Status updated successfully",
                "status": application.status
            },
            status=status.HTTP_200_OK
        )
class EmployerJobsAPI(ListCreateAPIView):

    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    pagination_class = CustomPagination

    def get_queryset(self):

        employer = Employer.objects.get(user=self.request.user)

        return Job.objects.filter(
            employer=employer
        ).order_by("-created_at")
    
class EmployerDashboardAPI(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):

        employer = Employer.objects.get(user=request.user)

        total_jobs = Job.objects.filter(
            employer=employer
        ).count()

        applications = Application.objects.filter(
            job__employer=employer
        )

        total_applications = applications.count()
        shortlisted = applications.filter(status="Shortlisted").count()
        selected = applications.filter(status="Selected").count()
        rejected = applications.filter(status="Rejected").count()

        return Response({
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "shortlisted": shortlisted,
            "selected": selected,
            "rejected": rejected,
        })
class CandidateDashboardAPI(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        candidate = Candidate.objects.get(user=request.user)

        applied_jobs = Application.objects.filter(
            candidate=candidate
        ).count()

        interview_scheduled = Application.objects.filter(
            candidate=candidate,
            status="Interview Scheduled"
        ).count()

        shortlisted = Application.objects.filter(
            candidate=candidate,
            status="Shortlisted"
        ).count()

        selected = Application.objects.filter(
            candidate=candidate,
            status="Selected"
        ).count()

        rejected = Application.objects.filter(
            candidate=candidate,
            status="Rejected"
        ).count()

        return Response(
            {
                "applied_jobs": applied_jobs,
                "interview_scheduled": interview_scheduled,
                "shortlisted": shortlisted,
                "selected": selected,
                "rejected": rejected
            }
        )
class RecommendedJobsAPI(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        candidate = Candidate.objects.get(user=request.user)

        jobs = Job.objects.filter(
            is_active=True
        )

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(serializer.data)

class AdminDashboardAPI(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        return Response({
            "username": request.user.username,
            "id": request.user.id,
            "is_authenticated": request.user.is_authenticated
        })
class ApproveEmployerAPI(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def patch(self, request, pk):

        try:
            employer = Employer.objects.get(id=pk)

        except Employer.DoesNotExist:

            return Response(
                {"error":"Employer not found"},
                status=404
            )


        employer.is_approved = True
        employer.save()


        AuditLog.objects.create(
            admin=request.user,
            action=f"Approved employer {employer.company_name}"
        )


        return Response({
            "message":"Employer approved successfully"
        })

class BlockUserAPI(APIView):

    permission_classes=[
        IsAuthenticated,
        IsAdmin
    ]


    def patch(self,request,pk):

        try:
            user = User.objects.get(id=pk)

        except User.DoesNotExist:

            return Response(
                {"error":"User not found"},
                status=404
            )


        user.is_active=False
        user.save()


        AuditLog.objects.create(
            admin=request.user,
            action=f"Blocked user {user.username}"
        )


        return Response({
            "message":"User blocked"
        })
class RemoveJobAPI(APIView):

    permission_classes=[
        IsAuthenticated,
        IsAdmin
    ]


    def delete(self,request,pk):

        try:

            job=Job.objects.get(id=pk)

        except Job.DoesNotExist:

            return Response(
                {"error":"Job not found"},
                status=404
            )


        job.is_active=False
        job.save()


        AuditLog.objects.create(
            admin=request.user,
            action=f"Removed job {job.title}"
        )


        return Response({
            "message":"Job removed successfully"
        })
class PlatformStatsAPI(APIView):

    permission_classes=[
        IsAuthenticated,
        IsAdmin
    ]


    def get(self,request):

        return Response({

            "total_users":
            User.objects.count(),

            "total_employers":
            Employer.objects.count(),

            "total_candidates":
            Candidate.objects.count(),

            "total_jobs":
            Job.objects.count(),

            "total_applications":
            Application.objects.count()

        })

class UserGrowthAPI(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        data = (
            User.objects
            .annotate(month=TruncMonth("date_joined"))
            .values("month")
            .annotate(total_users=Count("id"))
            .order_by("month")
        )

        return Response(data)

class FlagAccountAPI(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def post(self, request, pk):

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        reason = request.data.get("reason")

        if not reason:
            return Response(
                {"error": "Reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        Flag.objects.create(
            user=user,
            reason=reason
        )

        return Response(
            {
                "message": "User flagged successfully"
            },
            status=status.HTTP_201_CREATED
        )

        return Response({
            "message":"Account flagged"
        })

class JobActivityAPI(APIView):

    permission_classes=[
        IsAuthenticated,
        IsAdmin
    ]


    def get(self,request):

        data = {

            "active_jobs":
            Job.objects.filter(
                is_active=True
            ).count(),


            "inactive_jobs":
            Job.objects.filter(
                is_active=False
            ).count(),


            "applications":
            Application.objects.count()

        }


        return Response(data)

class AuditLogAPI(APIView):

    permission_classes=[
        IsAuthenticated,
        IsAdmin
    ]


    def get(self,request):

        logs = AuditLog.objects.all().values()


        return Response(logs)
class ResumeExtractorAPI(APIView):

    def post(self, request):

        serializer = ResumeUploadSerializer(data=request.data)

        if serializer.is_valid():

            resume = serializer.validated_data["resume"]

            text = ""

            if resume.name.endswith(".pdf"):

                reader = PdfReader(resume)

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        text += page_text

            elif resume.name.endswith(".docx"):

                document = Document(resume)

                for paragraph in document.paragraphs:
                    text += paragraph.text + "\n"

            else:

                return Response(
                    {
                        "error": "Only PDF and DOCX files are allowed."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            cleaned_text = re.sub(r"\s+", " ", text).strip()

            email = extract_email(cleaned_text)
            phone = extract_phone(cleaned_text)
            skills = extract_skills(cleaned_text)
            experience = extract_experience(cleaned_text)
            education = extract_education(cleaned_text)

            return Response(
                    {
                        "message": "Resume parsed successfully",

                        "resume_data": {
                            "email": email,
                            "phone": phone,
                            "skills": skills,
                            "experience": experience,
                            "education": education
                        }
                    },
                    status=status.HTTP_200_OK
                )
@api_view(["POST"])
def calculate_ats(request, application_id):
    result = calculate_ats_score(application_id)
    return Response(result)

@api_view(["GET"])
def ranked_candidates(request, job_id):

    results = get_ranked_candidates(job_id)

    return Response(results)

@api_view(["POST"])

def auto_shortlist_api(request, application_id):

    application = Application.objects.get(
        id=application_id
    )

    status = auto_shortlist(application)

    return Response({
        "application_id": application.id,
        "candidate": application.candidate.user.username,
        "job": application.job.title,
        "status": status
    })

class CallStatusAPIView(APIView):

    def get(self, request, pk):

        application = Application.objects.get(id=pk)

        return Response({

            "candidate": application.candidate.user.username,

            "call_status": application.call_status

        })

from rest_framework import serializers
from .models import Job, CandidateProfile, EmployerProfile
from .models import Application

class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = "__all__"
        read_only_fields = ["employer"]

class CandidateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = CandidateProfile
        fields = "__all__"

    def validate_expected_salary(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Salary cannot be negative"
            )
        return value

    def validate_resume(self, value):

        if value:
            allowed_types = ['pdf', 'doc', 'docx']

            extension = value.name.split('.')[-1].lower()

            if extension not in allowed_types:
                raise serializers.ValidationError(
                    "Only PDF, DOC and DOCX files allowed"
                )

            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "File size must be below 5 MB"
                )

        return value


class EmployerProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployerProfile
        fields = "__all__"

    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Company size must be greater than zero"
            )
        return value

class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = ["candidate", "job", "status", "applied_date"]

class ResumeUploadSerializer(serializers.Serializer):
    resume = serializers.FileField()
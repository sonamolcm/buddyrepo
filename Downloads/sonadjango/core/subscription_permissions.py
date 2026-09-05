from django.utils import timezone
from rest_framework.permissions import BasePermission

from .models import UserSubscription


class HasActiveSubscription(BasePermission):

    message = "An active subscription is required to access this feature."

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False

        subscription = UserSubscription.objects.filter(
            user=request.user,
            end_date__gt=timezone.now()
        ).order_by("-end_date").first()

        return subscription is not None

class IsEmployerUser(BasePermission):

    message = "Only employers can access recruiter analytics."

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False

        return hasattr(request.user, "employer")


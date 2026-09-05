from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.is_staff
        )


class IsEmployer(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and hasattr(request.user, "employer")
        )


class IsCandidate(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and hasattr(request.user, "candidate")
        )
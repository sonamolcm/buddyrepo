# pyrefly: ignore [missing-import]
from rest_framework import permissions


class IsCallerUser(permissions.BasePermission):
    """
    Permission check: User is authenticated and has the CALLER role.
    Callers cannot access Listener-only or Admin-only endpoints.
    """
    message = "Access restricted to Caller accounts only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_caller
        )


class IsListenerUser(permissions.BasePermission):
    """
    Permission check: User is authenticated and has the LISTENER role.
    Listeners cannot access Caller-only signup/profile or Admin endpoints.
    """
    message = "Access restricted to Listener accounts only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_listener
        )


class IsAdminUser(permissions.BasePermission):
    """
    Permission check: User is authenticated and has the ADMIN role or is_staff.
    """
    message = "Access restricted to Admin accounts only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsAgentUser(permissions.BasePermission):
    """
    Permission check: User is authenticated and has the AGENT/LISTENER role.
    Callers and unauthenticated users cannot access Agent-only endpoints.
    """
    message = "Access restricted to Agent accounts only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (getattr(request.user, 'is_agent', False) or getattr(request.user, 'is_listener', False) or request.user.role in ('AGENT', 'LISTENER', 'BUDDY'))
        )


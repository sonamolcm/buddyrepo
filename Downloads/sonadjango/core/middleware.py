from django.http import JsonResponse

class RoleMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            if request.path.startswith('/api/admin/'):
                if request.user.username != "admin":
                    return JsonResponse(
                        {"message": "Admin Access Only"},
                        status=403
                    )

        response = self.get_response(request)
        return response
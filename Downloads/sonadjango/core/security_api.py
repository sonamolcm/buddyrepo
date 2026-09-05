from rest_framework.views import APIView
from rest_framework.response import Response


class SecurityTestAPI(APIView):

    def get(self, request):

        return Response({
            "status": "Success",
            "message": "API request accepted"
        })

    
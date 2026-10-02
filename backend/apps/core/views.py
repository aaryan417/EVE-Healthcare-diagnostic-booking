from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """
    GET /api/health/
    Public health check endpoint validating system and database connectivity.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
            return Response(
                {"status": "ok", "database": "ok"},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"status": "unhealthy", "database": "error"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

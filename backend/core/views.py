from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=["System"],
    summary="Health check",
    description="Checks whether the backend service is running.",
    responses={
        200: OpenApiTypes.OBJECT,
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response(
        {
            "status": "ok",
            "service": "helpdesk-api",
        }
    )

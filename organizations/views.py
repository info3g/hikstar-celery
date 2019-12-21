from rest_framework import permissions, status, views, viewsets
from rest_framework.response import Response

from .models import Organization
from .serializers import OrgWithUserSerializer, ValidateWidgetSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrgWithUserSerializer

    def get_queryset(self):
        return self.queryset.filter(members__user=self.request.user)


class ValidateWidgetView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = ValidateWidgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_200_OK)

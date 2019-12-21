from rest_framework import generics, status
from rest_framework import permissions
from rest_framework.response import Response
from .serializers import ReservationMailSerializer


class ReservationMailView(generics.CreateAPIView):
    serializer_class = ReservationMailSerializer
    permission_classes = (permissions.AllowAny, )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': "Courriel envoyé avec succès"
        }, status=status.HTTP_200_OK)

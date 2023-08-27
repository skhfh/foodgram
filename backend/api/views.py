from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from djoser.serializers import TokenSerializer
from djoser.utils import login_user
from djoser.views import TokenCreateView
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.pagination import PageNumberPagination

from .serializers import SetPasswordSerializer, UsersSerializer
from .permissions import CurrentUserOrAdminPermission

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    http_method_names = ['get', 'post']
    permission_classes = (permissions.AllowAny,)
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.save()
        user = get_object_or_404(User,
                                 email=serializer.validated_data['email'])
        user.set_password(serializer.validated_data['password'])
        user.save()

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UsersSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            permission_classes=[CurrentUserOrAdminPermission])
    def set_password(self, request):
        current_user = self.request.user
        current_password = request.data['current_password']
        if not current_user.check_password(current_password):
            raise ValidationError('Введенный существующий пароль неверный')
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_user.set_password(serializer.validated_data['new_password'])
        current_user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenCreateView(TokenCreateView):

    def _action(self, serializer):
        token = login_user(self.request, serializer.user)
        token_serializer_class = TokenSerializer
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_201_CREATED
        )

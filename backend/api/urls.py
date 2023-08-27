from django.urls import include, path
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import routers

from .views import CustomTokenCreateView, UsersViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', UsersViewSet, basename='users')


urlpatterns = [
    path('auth/token/login/',
         CustomTokenCreateView.as_view(),
         name='create_token'),
    path('auth/', include('djoser.urls.authtoken'), name='token'),
    path('', include(router.urls)),
]

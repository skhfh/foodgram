from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import TokenSerializer
from djoser.utils import login_user
from djoser.views import TokenCreateView
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from .filters import IngredientFilter, RecipeFilter
from .mixins import CreateListRetrieveViewSet
from .pagination import CustomPagination
from .permissions import (AuthorOrReadOnlyPermission,
                          CurrentUserOrAdminPermission)
from .serializers import (FollowSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeLightSerializer,
                          RecipeSerializer, SetPasswordSerializer,
                          ShoppingCart, TagSerializer, UserSerializer)

User = get_user_model()


class UserViewSet(CreateListRetrieveViewSet):
    """Вьюсет для работы с User"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
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

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        follows = self.request.user.follower.all()
        serializer = FollowSerializer(follows,
                                      many=True,
                                      context={'request': request})
        response_qs = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(response_qs)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated],)
    def subscribe(self, request, pk):
        current_user = self.request.user
        following = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            if current_user == following:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST)
            follow, status_created = Follow.objects.get_or_create(
                user=current_user, following=following
            )
            if not status_created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = FollowSerializer(follow,
                                          context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if current_user == following:
                return Response(
                    {'errors': 'Вы не подписаны на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST)
            delete_status, _ = Follow.objects.filter(
                user=current_user,
                following=following).delete()
            if not delete_status:
                return Response({
                    'errors': 'Вы не были подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenCreateView(TokenCreateView):
    """Вью-класс для создания токенов"""

    def _action(self, serializer):
        token = login_user(self.request, serializer.user)
        token_serializer_class = TokenSerializer
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_201_CREATED
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения Ингредиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения Тэгов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с Рецептами"""
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnlyPermission,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def favorite_shopping_cart(self, request, pk, model):
        errors_answers = (['Избранное', 'Избранном'] if model == Favorite
                          else ['Корзину', 'Корзине'])
        current_user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            obj, status_created = model.objects.get_or_create(
                user=current_user, recipe=recipe
            )
            if not status_created:
                return Response({
                    'errors':
                        f'Рецепт уже был добавлен в {errors_answers[0]}'},
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeLightSerializer(obj.recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            delete_status, _ = model.objects.filter(user=current_user,
                                                    recipe=recipe).delete()
            if not delete_status:
                return Response(
                    {'errors': f'Рецепта не было в {errors_answers[1]}'},
                    status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated],)
    def favorite(self, request, pk):
        return self.favorite_shopping_cart(request, pk, Favorite)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated],)
    def shopping_cart(self, request, pk):
        return self.favorite_shopping_cart(request, pk, ShoppingCart)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated],)
    def download_shopping_cart(self, request):
        shopping_cart_qs = (
            RecipeIngredient.objects.
            filter(recipe__in_shoppingcart_for_users__user=request.user).
            values('ingredient__name', 'ingredient__measurement_unit').
            annotate(total_count=Sum('amount')))
        if shopping_cart_qs.count() == 0:
            return HttpResponse('Список покупок ПУСТ',
                                'Content-Type: text/plain')
        shopping_cart = []
        for ingredient in shopping_cart_qs:
            shopping_cart.append([
                ingredient.get('ingredient__name'),
                ingredient.get('ingredient__measurement_unit'),
                ingredient.get('total_count')
            ])
        shopping_cart_txt = render_to_string(
            'shopping_cart.txt',
            context={'shopping_cart': shopping_cart}
        )
        response = HttpResponse(shopping_cart_txt, 'Content-Type: text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename=shopping_cart.pdf')
        return response

from django_filters.rest_framework import filters, FilterSet

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'tags__slug')

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(
                favorite_for_users__user=self.request.user).all()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(
                in_shoppingcart_for_users__user=self.request.user).all()
        return queryset

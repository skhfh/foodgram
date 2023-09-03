from django.contrib import admin

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit',)
    search_fields = ('name',)


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    verbose_name_plural = 'Ингредиенты'
    verbose_name = 'Ингредиент'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk',
                    'name',
                    'author',
                    'text',
                    'cooking_time',
                    'added_in_favorite')
    list_filter = ('tags',)
    search_fields = ('name', 'author')
    inlines = [IngredientInline]

    @admin.display(description='Количество добавлений в Избранное')
    def added_in_favorite(self, obj):
        return obj.favorite_for_users.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient',  'amount',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'following')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')

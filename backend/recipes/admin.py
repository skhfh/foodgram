from django.contrib import admin

from .models import Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit',)


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    verbose_name_plural = 'Ингредиенты'
    verbose_name = 'Ингредиент'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'text', 'cooking_time',)
    inlines = [IngredientInline]


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

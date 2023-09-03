import re
import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from foodgram.settings import RECIPES_LIMIT
from recipes.models import Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
from users.validators import validate_username_not_me

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.SlugField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message='Пользователь с таким username уже'
                                            'существует'),
                    validate_username_not_me],
    )
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message='Пользователь с таким email уже'
                                            'существует')]
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128,
                                     write_only=True,
                                     validators=[validate_password],
                                     style={"input_type": "password"})
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'password',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Follow.objects.filter(user=current_user, following=obj).exists()

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"},
                                         max_length=128,
                                         write_only=True,
                                         validators=[validate_password])
    current_password = serializers.CharField(style={"input_type": "password"})

    def validate(self, data):
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(
                'Введите новый пароль отличный от существующего!')
        return data


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Follow.objects.filter(user=current_user,
                                     following=obj.following).exists()

    def get_recipes(self, obj):
        recipes_limit = (self.context.get('request').query_params.
                         get('recipes_limit'))
        if not recipes_limit.isdigit():
            recipes_limit = RECIPES_LIMIT
        recipes = obj.following.recipes.values(
            'id',
            'name',
            'image',
            'cooking_time',
        )[:int(recipes_limit)]
        return recipes

    def get_recipes_count(self, obj):
        recipes_count = obj.following.recipes.count()
        return recipes_count


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_representation(self, instance):
        data = super(RecipeIngredientSerializer, self).to_representation(instance)
        data['id'] = instance.ingredient.id
        return data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(source='ingredients_in_recipe',
                                             many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Favorite.objects.filter(user=current_user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=current_user, recipe=obj).exists()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name', 'text', 'cooking_time', 'author')
        read_only_fields = ('author',)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один ингредиент!')
        ingredients_list = [ingredient.get('id') for ingredient in value]
        if len(set(ingredients_list)) < len(ingredients_list):
            raise serializers.ValidationError(
                f'Выбранные ингредиенты повторяются! {ingredients_list}')
        return value

    def get_ingredients_data(self, ingredients, recipe):
        ingredients_data = []
        for ingredient_orderdict in ingredients:
            recipe_ingredient = RecipeIngredient(
                ingredient=ingredient_orderdict.get('id'),
                recipe=recipe,
                amount=ingredient_orderdict.get('amount')
            )
            ingredients_data.append(recipe_ingredient)
        return ingredients_data

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data

    def create(self, validated_data):
        current_user = self.context.get('request').user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=current_user)
        recipe.tags.set(tags)
        ingredients_data = self.get_ingredients_data(ingredients, recipe)
        RecipeIngredient.objects.bulk_create(ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            ingredients_data = self.get_ingredients_data(ingredients, instance)
            instance.ingredients.clear()
            RecipeIngredient.objects.bulk_create(ingredients_data)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)
            super().update(instance, validated_data)
        return instance


class RecipeLightSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = ('id', 'name', 'image', 'cooking_time',)

import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from food.models import Favorite, Ingredient, IngredientRecipe, Recipe, Tag
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from shopping_list_service.models import ShoppingList
from users.models import Follow, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerialiser(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'id', 'username',
                  'first_name', 'last_name')


class CustomUserSerialiser(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Follow.objects.filter(
                    user=request.user, following=obj
                ).exists())


class RecipeBriefSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserFollowGetSerializer(CustomUserSerialiser):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        return RecipeBriefSerializer(recipes, many=True,
                                     context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('id', 'user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Подписка на данного пользователя существует'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['following']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserFollowGetSerializer(
            instance.following, context={'request': request}
        ).data


class IngredientGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField()
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerialiser(many=True)
    author = CustomUserSerialiser()
    ingredients = IngredientGetSerializer(many=True,
                                          source='ingredientrecipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')
        read_only_fields = ('tags', 'author', 'ingredients',)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and Favorite.objects.filter(
                    user=request.user, recipe=obj
                ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and ShoppingList.objects.filter(
                    user=request.user, recipe=obj
                ).exists())


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(
        many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления меньше 1 минуты')
        return value

    def validate(self, data):
        ingredients_list = []
        for ingredient in data.get('ingredients'):
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиентов должно быть больше 0'
                )
            ingredients_list.append(ingredient.get('id'))
        if len(set(ingredients_list)) != len(ingredients_list):
            raise serializers.ValidationError(
                'Нельзя добавлять одинаковые ингредиенты'
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(Ingredient,
                                                   id=ingredient.get('id'))
            amount = ingredient.get('amount')
            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            amount=amount, recipe=recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        IngredientRecipe.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(Ingredient,
                                                   id=ingredient.get('id'))
            amount = ingredient.get('amount')
            IngredientRecipe.objects.create(ingredient=current_ingredient,
                                            amount=amount, recipe=instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeGetSerializer(
            instance,
            context={'request': request}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeBriefSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('id', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeBriefSerializer(
            instance.recipe,
            context={'request': request}
        ).data

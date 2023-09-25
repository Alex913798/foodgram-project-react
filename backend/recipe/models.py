from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.db.models import Sum
from users.models import User


class Ingredient (models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Цвет не соответствует HEX-формату'
            )
        ]
    )
    slug = models.SlugField(
        max_length=200,
        unique=True
    )


class Recipe (models.Model):

    name = models.CharField(max_length=256, unique=True)

    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Напишите рецепт'
    )
    image = models.ImageField(
        upload_to='recipe/',
        blank=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')

    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientRecipe')
    tags = models.ManyToManyField(
        Tag
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(
                1440, 'Время приготовления не должно быть дольше 1 дня'
            ),
            MinValueValidator(
                1, 'Время приготовления не должно быть меньше 1 минуты'
            )
        ]
    )


class IngredientRecipe(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE, related_name='ingredientrecipes')

    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE)
    amount = models.IntegerField(
        validators=[
            MaxValueValidator(
                3000, 'Количество не должно превышать 3000'
            ),
            MinValueValidator(
                1, 'Количество не должно быть меньше 1'
            )
        ]
    )

    @classmethod
    def get(cls, user):
        ingredients = cls.objects.filter(
            recipe__shoppings__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')
        return shopping_list


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favoritesresipe'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorites'
    )


class ShoppingList (models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppings'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppings'
    )

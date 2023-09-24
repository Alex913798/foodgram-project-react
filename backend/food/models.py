from django.db import models
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
        unique=True
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
        upload_to='food/',
        blank=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')

    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientRecipe')
    tags = models.ManyToManyField(
        Tag
    )
    cooking_time = models.IntegerField()


class IngredientRecipe(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE, related_name='ingredientrecipes')

    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE)
    amount = models.IntegerField()


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favoritesresipe'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorites'
    )

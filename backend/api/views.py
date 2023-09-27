from api.filters import RecipeFilter
from api.permissions import AuthorAdmin, ReadOnly
from api.serializers import (FavoriteSerializer, FollowSerializer,
                             IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeGetSerializer,
                             ShoppingListSerializer, TagSerialiser,
                             UserFollowGetSerializer)
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipe.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                           ShoppingList, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Follow, User


class APIUserFollow(APIView):
    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = FollowSerializer(
            data={'user': request.user.id, 'following': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Follow.objects.filter(user=request.user,
                                     following=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.get(user=request.user.id,
                           following=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetFollowViewSet(mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = UserFollowGetSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AuthorAdmin,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateUpdateSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            return (ReadOnly(),)
        return super().get_permissions()


class APIFavorite (APIView):
    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id, },
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if not Favorite.objects.filter(user=request.user,
                                       recipe=recipe).exists():
            return Response(
                {'errors': 'Данный рецепт отсутствует в избранном'},
                status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIShoppingList (APIView):
    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = ShoppingListSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if not ShoppingList.objects.filter(user=request.user,
                                           recipe=recipe).exists():
            return Response(
                {'errors': 'Данный рецепт отсутствует в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST)
        ShoppingList.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIShoppingListDownload (APIView):
    def get(self, request):
        user = request.user
        shopping_list = IngredientRecipe.get(user)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_cart.txt"'
        return response

from api.views import (APIFavorite, APIShoppingList, APIShoppingListDownload,
                       APIUserFollow, GetFollowViewSet, IngredientViewSet,
                       RecipeViewSet, TagViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('users/subscriptions/', GetFollowViewSet.as_view({'get': 'list'})),
    path('users/<int:user_id>/subscribe/', APIUserFollow.as_view()),
    path('recipes/<int:pk>/favorite/', APIFavorite.as_view()),
    path('recipes/<int:pk>/shopping_cart/', APIShoppingList.as_view()),
    path('recipes/download_shopping_cart/', APIShoppingListDownload.as_view()),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]

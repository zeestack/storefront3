from django.db.models import base
from django.urls import path
from django.urls.conf import include
from django.urls.resolvers import URLPattern
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter()

router.register("products", views.ProductViewSet, basename="products")
router.register("collections", views.CollectionViewSet)
router.register("cart", views.CartViewSet)
router.register("orders", views.OrderViewSet, basename="orders")
router.register("customers", views.CustomerViewSet, basename="customers")

product_router = routers.NestedDefaultRouter(router, "products", lookup="product")
product_router.register("reviews", views.ReviewViewSet, basename="product-reviews")
product_router.register("images", views.ProductImageViewSet, basename="product-images")

cart_router = routers.NestedDefaultRouter(router, "cart", lookup="cart")
cart_router.register("items", views.CartItemViewSet, basename="cart-items")
# URL Configuration

urlpatterns = router.urls + product_router.urls + cart_router.urls

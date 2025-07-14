from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompradorViewSet, PedidoViewSet

router = DefaultRouter()
router.register(r'compradores', CompradorViewSet)
router.register(r'pedidos', PedidoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
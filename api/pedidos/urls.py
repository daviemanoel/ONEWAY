from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompradorViewSet, PedidoViewSet, ItemPedidoViewSet, setup_estoque_view

router = DefaultRouter()
router.register(r'compradores', CompradorViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'itempedidos', ItemPedidoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('setup-estoque/', setup_estoque_view, name='setup-estoque'),
]
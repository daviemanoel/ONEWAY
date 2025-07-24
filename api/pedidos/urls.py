from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompradorViewSet, PedidoViewSet, ItemPedidoViewSet, 
    setup_estoque_view, validar_estoque_view, estoque_multiplo_view, gerar_products_json_view,
    decrementar_estoque_view
)

router = DefaultRouter()
router.register(r'compradores', CompradorViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'itempedidos', ItemPedidoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('setup-estoque/', setup_estoque_view, name='setup-estoque'),
    path('validar-estoque/', validar_estoque_view, name='validar-estoque'),
    path('estoque-multiplo/', estoque_multiplo_view, name='estoque-multiplo'),
    path('gerar-products-json/', gerar_products_json_view, name='gerar-products-json'),
    path('decrementar-estoque/', decrementar_estoque_view, name='decrementar-estoque'),
]
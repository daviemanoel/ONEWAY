from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
import requests
from django.conf import settings
from .models import Comprador, Pedido
from .serializers import (
    CompradorSerializer, 
    PedidoSerializer, 
    CriarPedidoSerializer,
    AtualizarStatusSerializer
)


class CompradorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para visualizar compradores (somente leitura)"""
    queryset = Comprador.objects.all()
    serializer_class = CompradorSerializer
    authentication_classes = [TokenAuthentication]
    
    def get_permissions(self):
        # Permitir acesso sem autenticação para métodos de leitura
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()


class PedidoViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gerenciar pedidos"""
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    authentication_classes = [TokenAuthentication]
    
    def get_permissions(self):
        # Permitir criar pedido sem autenticação (vem do Node.js)
        if self.action == 'create':
            return [AllowAny()]
        # Permitir consultar por external_reference sem autenticação
        if self.action in ['buscar_por_referencia', 'consultar_mercadopago']:
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CriarPedidoSerializer
        if self.action == 'atualizar_status':
            return AtualizarStatusSerializer
        return PedidoSerializer
    
    def create(self, request):
        """Criar novo pedido com dados do comprador"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        
        # Retornar o pedido criado com o serializer padrão
        output_serializer = PedidoSerializer(pedido)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='referencia/(?P<external_reference>[^/.]+)')
    def buscar_por_referencia(self, request, external_reference=None):
        """Buscar pedido por external_reference"""
        try:
            pedido = Pedido.objects.get(external_reference=external_reference)
            serializer = PedidoSerializer(pedido)
            return Response(serializer.data)
        except Pedido.DoesNotExist:
            return Response(
                {'erro': 'Pedido não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def atualizar_status(self, request, pk=None):
        """Atualizar status do pedido"""
        pedido = self.get_object()
        serializer = AtualizarStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Atualizar campos
        if 'status_pagamento' in serializer.validated_data:
            pedido.status_pagamento = serializer.validated_data['status_pagamento']
        
        if 'payment_id' in serializer.validated_data:
            pedido.payment_id = serializer.validated_data['payment_id']
        
        if 'preference_id' in serializer.validated_data:
            pedido.preference_id = serializer.validated_data['preference_id']
        
        if 'merchant_order_id' in serializer.validated_data:
            pedido.merchant_order_id = serializer.validated_data['merchant_order_id']
            
        if 'observacoes' in serializer.validated_data:
            pedido.observacoes = serializer.validated_data['observacoes']
        
        pedido.save()
        
        output_serializer = PedidoSerializer(pedido)
        return Response(output_serializer.data)
    
    @action(detail=True, methods=['post'])
    def consultar_mercadopago(self, request, pk=None):
        """Consultar status do pagamento no Mercado Pago"""
        pedido = self.get_object()
        
        if not pedido.payment_id:
            return Response(
                {'erro': 'Payment ID não disponível'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aqui seria feita a consulta real ao Mercado Pago
        # Por enquanto, apenas retornar os dados atuais
        try:
            # TODO: Implementar consulta real ao MP quando tivermos o token
            # headers = {'Authorization': f'Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}'}
            # response = requests.get(
            #     f'https://api.mercadopago.com/v1/payments/{pedido.payment_id}',
            #     headers=headers
            # )
            # mp_data = response.json()
            
            # Simulação de resposta
            return Response({
                'pedido_id': pedido.id,
                'payment_id': pedido.payment_id,
                'status_atual': pedido.status_pagamento,
                'mensagem': 'Consulta ao MP será implementada com token válido'
            })
            
        except Exception as e:
            return Response(
                {'erro': f'Erro ao consultar Mercado Pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

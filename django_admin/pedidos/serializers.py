from rest_framework import serializers
from .models import Comprador, Pedido


class CompradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comprador
        fields = ['id', 'nome', 'email', 'telefone', 'data_cadastro']
        read_only_fields = ['id', 'data_cadastro']


class PedidoSerializer(serializers.ModelSerializer):
    comprador = CompradorSerializer(read_only=True)
    status_display = serializers.ReadOnlyField()
    valor_com_desconto = serializers.ReadOnlyField()
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'comprador', 'produto', 'tamanho', 'preco',
            'forma_pagamento', 'external_reference', 'payment_id',
            'preference_id', 'merchant_order_id', 'status_pagamento',
            'status_display', 'valor_com_desconto', 'data_pedido',
            'data_atualizacao', 'observacoes'
        ]
        read_only_fields = ['id', 'data_pedido', 'data_atualizacao']


class CriarPedidoSerializer(serializers.Serializer):
    """Serializer para criar novo pedido com dados do comprador"""
    # Dados do comprador
    nome = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    telefone = serializers.CharField(max_length=20)
    
    # Dados do pedido
    produto = serializers.ChoiceField(choices=Pedido.PRODUTOS_CHOICES)
    tamanho = serializers.ChoiceField(choices=Pedido.TAMANHOS_CHOICES)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = serializers.ChoiceField(choices=Pedido.FORMA_PAGAMENTO_CHOICES)
    
    # Dados opcionais do Mercado Pago
    payment_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    preference_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    merchant_order_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    external_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def create(self, validated_data):
        # Extrair dados do comprador
        comprador_data = {
            'nome': validated_data.pop('nome'),
            'email': validated_data.pop('email'),
            'telefone': validated_data.pop('telefone')
        }
        
        # Criar ou buscar comprador existente
        comprador, created = Comprador.objects.get_or_create(
            email=comprador_data['email'],
            defaults=comprador_data
        )
        
        # Se o comprador já existe, atualizar nome e telefone se necessário
        if not created:
            if comprador.nome != comprador_data['nome']:
                comprador.nome = comprador_data['nome']
            if comprador.telefone != comprador_data['telefone']:
                comprador.telefone = comprador_data['telefone']
            comprador.save()
        
        # Criar o pedido
        pedido = Pedido.objects.create(
            comprador=comprador,
            **validated_data
        )
        
        return pedido


class AtualizarStatusSerializer(serializers.Serializer):
    """Serializer para atualizar status do pedido"""
    status_pagamento = serializers.ChoiceField(choices=Pedido.STATUS_CHOICES, required=False)
    payment_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    preference_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    merchant_order_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    observacoes = serializers.CharField(required=False, allow_blank=True)
from rest_framework import serializers
from .models import Comprador, Pedido, ItemPedido


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
    status_pagamento = serializers.ChoiceField(choices=Pedido.STATUS_CHOICES, required=False, default='pending')
    
    def validate(self, data):
        """Validação customizada para garantir dados obrigatórios conforme forma de pagamento"""
        forma_pagamento = data.get('forma_pagamento')
        external_reference = data.get('external_reference')
        
        # Para pagamento presencial, gerar external_reference automático se não fornecido
        if forma_pagamento == 'presencial':
            if not external_reference or external_reference.strip() == '':
                import time
                data['external_reference'] = f'PRESENCIAL-{int(time.time())}'
        
        # Para outros pagamentos via gateway, apenas logar warning se não tiver external_reference
        # IMPORTANTE: NÃO bloquear criação para manter compatibilidade com sistema atual
        pagamentos_com_gateway = ['pix', '2x', '4x', 'paypal', 'paypal_3x', 'mercadopago']
        if forma_pagamento in pagamentos_com_gateway:
            if not external_reference or external_reference.strip() == '':
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"⚠️ PEDIDO SEM EXTERNAL_REFERENCE: forma_pagamento={forma_pagamento} "
                    f"pode ficar órfão se página de retorno falhar"
                )
        
        return data
    
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
        
        # Log da criação do pedido para auditoria
        forma_pagamento = validated_data.get('forma_pagamento')
        external_reference = validated_data.get('external_reference')
        payment_id = validated_data.get('payment_id')
        
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 CRIANDO PEDIDO: forma_pagamento={forma_pagamento}, external_reference={external_reference}, payment_id={payment_id}")
        
        # Criar o pedido
        pedido = Pedido.objects.create(
            comprador=comprador,
            **validated_data
        )
        
        # Log adicional para pedidos sem dados MP quando deveriam ter
        pagamentos_com_gateway = ['pix', '2x', '4x', 'paypal', 'paypal_3x', 'mercadopago']
        if forma_pagamento in pagamentos_com_gateway and not payment_id:
            logger.warning(f"⚠️ ATENÇÃO: Pedido {pedido.id} criado com pagamento {forma_pagamento} mas SEM payment_id - pode ficar órfão!")
        
        return pedido


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = ItemPedido
        fields = [
            'id', 'pedido', 'produto', 'tamanho', 'quantidade', 
            'preco_unitario', 'subtotal'
        ]
        read_only_fields = ['id']


class AtualizarStatusSerializer(serializers.Serializer):
    """Serializer para atualizar status do pedido"""
    status_pagamento = serializers.ChoiceField(choices=Pedido.STATUS_CHOICES, required=False)
    payment_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    preference_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    merchant_order_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    observacoes = serializers.CharField(required=False, allow_blank=True)
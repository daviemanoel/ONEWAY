from django.db import models
from django.utils import timezone
from decimal import Decimal


class Produto(models.Model):
    """Model para gerenciar produtos do e-commerce"""
    nome = models.CharField(max_length=200, verbose_name="Nome do Produto")
    slug = models.SlugField(unique=True, verbose_name="Slug (para URL)")
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Custo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    ordem = models.IntegerField(default=0, verbose_name="Ordem de Exibição")
    json_key = models.CharField(max_length=100, unique=True, help_text="Chave no products.json para compatibilidade")
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['ordem', 'nome']
    
    def __str__(self):
        return self.nome
    
    @property
    def estoque_total(self):
        """Retorna o estoque total somando todos os tamanhos"""
        return sum(tamanho.estoque for tamanho in self.tamanhos.all())
    
    @property
    def tem_estoque(self):
        """Verifica se há estoque em algum tamanho"""
        return any(tamanho.disponivel and tamanho.estoque > 0 for tamanho in self.tamanhos.all())


class ProdutoTamanho(models.Model):
    """Model para gerenciar estoque por tamanho de produto"""
    TAMANHOS_CHOICES = [
        ('P', 'P'),
        ('M', 'M'),
        ('G', 'G'),
        ('GG', 'GG'),
    ]
    
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name='tamanhos',
        verbose_name="Produto"
    )
    tamanho = models.CharField(
        max_length=5, 
        choices=TAMANHOS_CHOICES,
        verbose_name="Tamanho"
    )
    estoque = models.IntegerField(
        default=0,
        verbose_name="Estoque"
    )
    disponivel = models.BooleanField(
        default=True,
        verbose_name="Disponível"
    )
    
    class Meta:
        verbose_name = "Tamanho do Produto"
        verbose_name_plural = "Tamanhos dos Produtos"
        unique_together = [['produto', 'tamanho']]
        ordering = ['produto', 'tamanho']
    
    def __str__(self):
        return f"{self.produto.nome} - {self.tamanho}"
    
    @property
    def esta_disponivel(self):
        """Verifica se o produto está disponível para venda"""
        return self.disponivel and self.estoque > 0
    
    def decrementar_estoque(self, quantidade=1):
        """Decrementa o estoque e atualiza disponibilidade se necessário"""
        if self.estoque >= quantidade:
            self.estoque -= quantidade
            if self.estoque == 0:
                self.disponivel = False
            self.save()
            return True
        return False
    
    def incrementar_estoque(self, quantidade=1):
        """Incrementa o estoque e reativa produto se necessário"""
        if quantidade > 0:
            self.estoque += quantidade
            # Reativar produto se estava indisponível e agora tem estoque
            if not self.disponivel and self.estoque > 0:
                self.disponivel = True
            self.save()
            return True
        return False


class Comprador(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")

    class Meta:
        verbose_name = "Comprador"
        verbose_name_plural = "Compradores"
        ordering = ['-data_cadastro']

    def __str__(self):
        return f"{self.nome} ({self.email})"


class Pedido(models.Model):
    PRODUTOS_CHOICES = [
        ('camiseta-marrom', 'Camiseta One Way Marrom'),
        ('camiseta-jesus', 'Camiseta Jesus'),
        ('camiseta-oneway-branca', 'Camiseta ONE WAY Off White'),
        ('camiseta-the-way', 'Camiseta The Way'),
    ]
    
    TAMANHOS_CHOICES = [
        ('P', 'P'),
        ('M', 'M'),
        ('G', 'G'),
        ('GG', 'GG'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('pix', 'PIX (5% desconto)'),
        ('2x', 'Cartão 2x sem juros'),
        ('4x', 'Cartão até 4x'),
        ('paypal', 'PayPal'),
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('ticket', 'Boleto'),
        ('bank_transfer', 'Transferência'),
        ('account_money', 'Dinheiro em Conta'),
        ('presencial', 'Pagamento Presencial'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('in_process', 'Processando'),
        ('rejected', 'Rejeitado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    # Dados do Pedido
    comprador = models.ForeignKey(Comprador, on_delete=models.CASCADE, verbose_name="Comprador")
    
    # Campos legacy (mantidos para compatibilidade)
    produto = models.CharField(max_length=100, choices=PRODUTOS_CHOICES, verbose_name="Produto")
    tamanho = models.CharField(max_length=5, choices=TAMANHOS_CHOICES, verbose_name="Tamanho")
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    
    # Novo campo para integração com controle de estoque
    produto_tamanho = models.ForeignKey(
        'ProdutoTamanho',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Produto/Tamanho (Novo Sistema)",
        help_text="Referência ao novo sistema de controle de estoque"
    )
    estoque_decrementado = models.BooleanField(
        default=False,
        verbose_name="Estoque Decrementado",
        help_text="Indica se o estoque já foi decrementado para este pedido"
    )
    
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, verbose_name="Forma de Pagamento")
    
    # Dados Mercado Pago / PayPal
    external_reference = models.CharField(max_length=100, unique=True, verbose_name="Referência Externa")
    payment_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="ID Pagamento MP/PayPal")
    preference_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="ID Preferência MP/Ordem PayPal")
    merchant_order_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="ID Ordem Comerciante")
    
    # Status e Controle
    status_pagamento = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Status do Pagamento"
    )
    data_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Data do Pedido")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-data_pedido']

    def __str__(self):
        if self.produto_tamanho:
            return f"Pedido #{self.id} - {self.comprador.nome} - {self.produto_tamanho}"
        return f"Pedido #{self.id} - {self.comprador.nome} - {self.get_produto_display()}"
    
    @property
    def usa_novo_sistema(self):
        """Indica se o pedido usa o novo sistema de controle de estoque"""
        return self.produto_tamanho is not None
    
    @property
    def produto_display(self):
        """Retorna o nome do produto de forma unificada"""
        if self.produto_tamanho:
            return self.produto_tamanho.produto.nome
        return self.get_produto_display()
    
    @property
    def tamanho_display(self):
        """Retorna o tamanho de forma unificada"""
        if self.produto_tamanho:
            return self.produto_tamanho.tamanho
        return self.tamanho

    @property
    def status_display(self):
        """Retorna o status com emoji para melhor visualização"""
        status_icons = {
            'pending': '⏳',
            'approved': '✅',
            'in_process': '🔄',
            'rejected': '❌',
            'cancelled': '🚫',
            'refunded': '↩️',
        }
        icon = status_icons.get(self.status_pagamento, '❓')
        return f"{icon} {self.get_status_pagamento_display()}"

    @property
    def valor_com_desconto(self):
        """Calcula o valor final considerando desconto PIX"""
        from decimal import Decimal
        if self.forma_pagamento == 'pix':
            return self.preco * Decimal('0.95')  # 5% desconto
        return self.preco

    def save(self, *args, **kwargs):
        # Se não tem external_reference, gerar uma baseada no timestamp
        if not self.external_reference:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.external_reference = f"ONEWAY-{self.id or 'NEW'}-{timestamp}"
        super().save(*args, **kwargs)
    
    @property
    def total_pedido(self):
        """Calcula o total do pedido baseado nos itens (para nova estrutura)"""
        if hasattr(self, 'itens'):
            total = sum(item.subtotal for item in self.itens.all())
            # Aplicar desconto PIX se necessário
            if self.forma_pagamento == 'pix':
                return total * Decimal('0.95')
            return total
        # Fallback para pedidos antigos
        return self.valor_com_desconto


class ItemPedido(models.Model):
    """Modelo para representar cada item dentro de um pedido"""
    PRODUTOS_CHOICES = Pedido.PRODUTOS_CHOICES
    TAMANHOS_CHOICES = Pedido.TAMANHOS_CHOICES
    
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE, 
        related_name='itens',
        verbose_name="Pedido"
    )
    
    # Campos legacy
    produto = models.CharField(
        max_length=100, 
        choices=PRODUTOS_CHOICES, 
        verbose_name="Produto"
    )
    tamanho = models.CharField(
        max_length=5, 
        choices=TAMANHOS_CHOICES, 
        verbose_name="Tamanho"
    )
    
    # Novo campo para integração com controle de estoque
    produto_tamanho = models.ForeignKey(
        'ProdutoTamanho',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Produto/Tamanho (Novo Sistema)"
    )
    
    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantidade"
    )
    preco_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Preço Unitário"
    )
    
    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
        unique_together = [['pedido', 'produto', 'tamanho']]
    
    def __str__(self):
        return f"{self.quantidade}x {self.get_produto_display()} ({self.tamanho})"
    
    @property
    def subtotal(self):
        """Calcula o subtotal do item"""
        return self.preco_unitario * self.quantidade
    
    def save(self, *args, **kwargs):
        # Validar preço contra products.json seria ideal aqui
        super().save(*args, **kwargs)

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
    
    def decrementar_estoque(self, quantidade=1, pedido=None, usuario="", observacao="", origem=""):
        """
        Decrementa o estoque e atualiza disponibilidade se necessário
        Registra automaticamente a movimentação no histórico
        """
        if self.estoque >= quantidade:
            # Registrar movimentação ANTES de alterar o estoque
            from .models import MovimentacaoEstoque
            MovimentacaoEstoque.registrar_movimentacao(
                produto_tamanho=self,
                tipo='saida',
                quantidade=quantidade,
                pedido=pedido,
                usuario=usuario,
                observacao=observacao or f"Decremento de estoque: {quantidade} unidade(s)",
                origem=origem or 'decrementar_estoque'
            )
            
            # Atualizar estoque
            self.estoque -= quantidade
            if self.estoque == 0:
                self.disponivel = False
            self.save()
            return True
        return False
    
    def incrementar_estoque(self, quantidade=1, pedido=None, usuario="", observacao="", origem=""):
        """
        Incrementa o estoque e reativa produto se necessário
        Registra automaticamente a movimentação no histórico
        """
        if quantidade > 0:
            # Registrar movimentação ANTES de alterar o estoque
            from .models import MovimentacaoEstoque
            MovimentacaoEstoque.registrar_movimentacao(
                produto_tamanho=self,
                tipo='entrada',
                quantidade=quantidade,
                pedido=pedido,
                usuario=usuario,
                observacao=observacao or f"Incremento de estoque: {quantidade} unidade(s)",
                origem=origem or 'incrementar_estoque'
            )
            
            # Atualizar estoque
            self.estoque += quantidade
            # Reativar produto se estava indisponível e agora tem estoque
            if not self.disponivel and self.estoque > 0:
                self.disponivel = True
            self.save()
            return True
        return False
    
    def ajustar_estoque(self, novo_estoque, usuario="", observacao="", origem="ajuste_manual"):
        """
        Ajusta o estoque para um valor específico
        Registra a movimentação com a diferença
        """
        diferenca = novo_estoque - self.estoque
        if diferenca != 0:
            tipo = 'entrada' if diferenca > 0 else 'saida'
            
            # Registrar movimentação
            from .models import MovimentacaoEstoque
            MovimentacaoEstoque.registrar_movimentacao(
                produto_tamanho=self,
                tipo='ajuste',
                quantidade=diferenca,
                usuario=usuario,
                observacao=observacao or f"Ajuste de estoque: {self.estoque} → {novo_estoque}",
                origem=origem
            )
            
            # Atualizar estoque
            self.estoque = novo_estoque
            self.disponivel = novo_estoque > 0
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


class MovimentacaoEstoque(models.Model):
    """
    Histórico de todas as movimentações de estoque
    Registra automaticamente entradas, saídas e ajustes
    """
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste'),
        ('reset', 'Reset'),
        ('setup', 'Setup Inicial'),
    ]
    
    # Relacionamentos
    produto_tamanho = models.ForeignKey(
        'ProdutoTamanho',
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name="Produto/Tamanho"
    )
    pedido = models.ForeignKey(
        'Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Pedido Relacionado",
        help_text="Pedido que gerou esta movimentação (se aplicável)"
    )
    
    # Dados da movimentação
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimentação"
    )
    quantidade = models.IntegerField(
        verbose_name="Quantidade",
        help_text="Quantidade movimentada (positiva para entrada, negativa para saída)"
    )
    estoque_anterior = models.IntegerField(
        verbose_name="Estoque Anterior",
        help_text="Quantidade de estoque antes da movimentação"
    )
    estoque_posterior = models.IntegerField(
        verbose_name="Estoque Posterior",
        help_text="Quantidade de estoque após a movimentação"
    )
    
    # Metadados
    data_movimentacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Movimentação"
    )
    usuario = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Usuário",
        help_text="Usuário ou sistema que executou a movimentação"
    )
    observacao = models.TextField(
        blank=True,
        verbose_name="Observação",
        help_text="Detalhes adicionais sobre a movimentação"
    )
    origem = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Origem",
        help_text="Sistema/comando que originou a movimentação (ex: pagamento_presencial, sincronizacao)"
    )
    
    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data_movimentacao']
        indexes = [
            models.Index(fields=['produto_tamanho', '-data_movimentacao']),
            models.Index(fields=['tipo', '-data_movimentacao']),
            models.Index(fields=['pedido']),
        ]
    
    def __str__(self):
        sinal = "+" if self.quantidade >= 0 else ""
        return f"{self.produto_tamanho} - {sinal}{self.quantidade} ({self.get_tipo_display()})"
    
    @property
    def quantidade_display(self):
        """Exibe quantidade com sinal para melhor visualização"""
        sinal = "+" if self.quantidade >= 0 else ""
        return f"{sinal}{self.quantidade}"
    
    @classmethod
    def registrar_movimentacao(cls, produto_tamanho, tipo, quantidade, pedido=None, usuario="", observacao="", origem=""):
        """
        Método utilitário para registrar movimentações
        
        Args:
            produto_tamanho: Instância do ProdutoTamanho
            tipo: Tipo da movimentação ('entrada', 'saida', 'ajuste', etc.)
            quantidade: Quantidade (positiva ou negativa)
            pedido: Pedido relacionado (opcional)
            usuario: Usuário que executou (opcional)
            observacao: Observações adicionais (opcional)
            origem: Sistema de origem (opcional)
        """
        # Capturar estoque anterior
        estoque_anterior = produto_tamanho.estoque
        
        # Calcular estoque posterior
        if tipo in ['entrada', 'ajuste', 'reset', 'setup']:
            # Para esses tipos, quantidade já é o valor final ou diferença
            if tipo in ['reset', 'setup']:
                estoque_posterior = quantidade
                quantidade_real = quantidade - estoque_anterior
            else:
                estoque_posterior = estoque_anterior + quantidade
                quantidade_real = quantidade
        else:  # saida
            estoque_posterior = estoque_anterior - abs(quantidade)
            quantidade_real = -abs(quantidade)
        
        # Criar registro de movimentação
        movimentacao = cls.objects.create(
            produto_tamanho=produto_tamanho,
            pedido=pedido,
            tipo=tipo,
            quantidade=quantidade_real,
            estoque_anterior=estoque_anterior,
            estoque_posterior=estoque_posterior,
            usuario=usuario,
            observacao=observacao,
            origem=origem
        )
        
        return movimentacao

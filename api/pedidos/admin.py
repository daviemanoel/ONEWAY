from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import Comprador, Pedido, ItemPedido, Produto, ProdutoTamanho, MovimentacaoEstoque
import requests
from django.conf import settings
import os
from django.db.models import Q


class PedidosOrfaosFilter(admin.SimpleListFilter):
    """Filtro para identificar pedidos órfãos (sem dados MP quando deveriam ter)"""
    title = 'Pedidos Órfãos (sem dados MP)'
    parameter_name = 'orfaos'
    
    def lookups(self, request, model_admin):
        return (
            ('sim', 'Sim - Sem dados MP'),
            ('pendentes_antigos', 'Pendentes há mais de 2h'),
            ('todos_problemas', 'Todos os problemas'),
        )
    
    def queryset(self, request, queryset):
        pagamentos_com_gateway = ['pix', '2x', '4x', 'paypal', 'paypal_3x', 'mercadopago']
        
        if self.value() == 'sim':
            # Pedidos com forma de pagamento via gateway mas sem dados MP
            return queryset.filter(
                Q(forma_pagamento__in=pagamentos_com_gateway) &
                (Q(payment_id__isnull=True) | Q(payment_id__exact='') |
                 Q(external_reference__isnull=True) | Q(external_reference__exact=''))
            )
        elif self.value() == 'pendentes_antigos':
            # Pedidos antigos pendentes (mais de 2h)
            from django.utils import timezone
            from datetime import timedelta
            limite_tempo = timezone.now() - timedelta(hours=2)
            return queryset.filter(
                forma_pagamento__in=pagamentos_com_gateway,
                status_pagamento='pending',
                data_pedido__lt=limite_tempo
            )
        elif self.value() == 'todos_problemas':
            # Combinar ambos os problemas
            from django.utils import timezone
            from datetime import timedelta
            limite_tempo = timezone.now() - timedelta(hours=2)
            
            sem_dados_mp = Q(forma_pagamento__in=pagamentos_com_gateway) & (
                Q(payment_id__isnull=True) | Q(payment_id__exact='') |
                Q(external_reference__isnull=True) | Q(external_reference__exact='')
            )
            
            pendentes_antigos = Q(
                forma_pagamento__in=pagamentos_com_gateway,
                status_pagamento='pending',
                data_pedido__lt=limite_tempo
            )
            
            return queryset.filter(sem_dados_mp | pendentes_antigos)
        
        return queryset


class PedidosComDadosVaziosFilter(admin.SimpleListFilter):
    """Filtro para verificar campos específicos vazios"""
    title = 'Campos MP Vazios'
    parameter_name = 'dados_vazios'
    
    def lookups(self, request, model_admin):
        return (
            ('sem_payment_id', 'Sem Payment ID'),
            ('sem_external_ref', 'Sem External Reference'),
            ('sem_preference_id', 'Sem Preference ID'),
            ('todos_vazios', 'Todos os campos vazios'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'sem_payment_id':
            return queryset.filter(Q(payment_id__isnull=True) | Q(payment_id__exact=''))
        elif self.value() == 'sem_external_ref':
            return queryset.filter(Q(external_reference__isnull=True) | Q(external_reference__exact=''))
        elif self.value() == 'sem_preference_id':
            return queryset.filter(Q(preference_id__isnull=True) | Q(preference_id__exact=''))
        elif self.value() == 'todos_vazios':
            return queryset.filter(
                (Q(payment_id__isnull=True) | Q(payment_id__exact='')) &
                (Q(external_reference__isnull=True) | Q(external_reference__exact='')) &
                (Q(preference_id__isnull=True) | Q(preference_id__exact=''))
            )
        
        return queryset


class ProdutoTamanhoInline(admin.TabularInline):
    """Inline para editar tamanhos do produto"""
    model = ProdutoTamanho
    extra = 0
    fields = ['tamanho', 'estoque', 'disponivel', 'estoque_status']
    readonly_fields = ['estoque_status']
    
    def estoque_status(self, obj):
        """Exibe status visual do estoque"""
        if not obj.pk:
            return '-'
        
        if obj.estoque == 0:
            return format_html('<span style="color: red; font-weight: bold;">❌ Esgotado</span>')
        elif obj.estoque <= 2:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ Baixo ({} un.)</span>', obj.estoque)
        else:
            return format_html('<span style="color: green; font-weight: bold;">✅ OK ({} un.)</span>', obj.estoque)
    estoque_status.short_description = 'Status'


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_display', 'estoque_total_display', 'tamanhos_disponiveis', 'ativo', 'ordem']
    list_filter = ['ativo']
    search_fields = ['nome', 'slug', 'json_key']
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [ProdutoTamanhoInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'json_key', 'ativo', 'ordem')
        }),
        ('Preços', {
            'fields': ('preco', 'preco_custo', 'margem_display'),
        }),
    )
    
    readonly_fields = ['margem_display']
    
    def preco_display(self, obj):
        """Exibe o preço formatado"""
        return f'R$ {obj.preco:.2f}'
    preco_display.short_description = 'Preço'
    
    def estoque_total_display(self, obj):
        """Exibe o estoque total com indicador visual"""
        total = obj.estoque_total
        
        if total == 0:
            return format_html('<span style="color: red; font-weight: bold;">❌ 0</span>')
        elif total <= 10:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ {}</span>', total)
        else:
            return format_html('<span style="color: green; font-weight: bold;">✅ {}</span>', total)
    estoque_total_display.short_description = 'Estoque Total'
    
    def tamanhos_disponiveis(self, obj):
        """Mostra os tamanhos disponíveis"""
        tamanhos = []
        for t in obj.tamanhos.all().order_by('tamanho'):
            if t.disponivel and t.estoque > 0:
                tamanhos.append(f'{t.tamanho}({t.estoque})')
            else:
                tamanhos.append(f'<s>{t.tamanho}</s>')
        return format_html(' | '.join(tamanhos))
    tamanhos_disponiveis.short_description = 'Tamanhos'
    
    def margem_display(self, obj):
        """Calcula e exibe a margem de lucro"""
        if obj.preco_custo and obj.preco_custo > 0:
            margem = ((obj.preco - obj.preco_custo) / obj.preco_custo) * 100
            color = 'green' if margem > 50 else 'orange' if margem > 30 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, margem
            )
        return '-'
    margem_display.short_description = 'Margem de Lucro'
    
    actions = ['gerar_products_json', 'marcar_sem_estoque']
    
    def gerar_products_json(self, request, queryset):
        """Action para gerar o products.json"""
        import json
        
        products_data = {"products": {}}
        
        for produto in Produto.objects.filter(ativo=True).order_by('ordem'):
            sizes = {}
            for tamanho in produto.tamanhos.all():
                sizes[tamanho.tamanho] = {
                    "product_size_id": tamanho.id,
                    "available": tamanho.disponivel and tamanho.estoque > 0,
                    "qtda_estoque": tamanho.estoque,
                    # Manter campos legacy
                    "stripe_link": None,
                    "id_stripe": f"prod_{produto.json_key}_{tamanho.tamanho.lower()}"
                }
            
            products_data["products"][produto.json_key] = {
                "id": str(produto.id),
                "title": produto.nome,
                "price": float(produto.preco),
                "preco_custo": float(produto.preco_custo),
                "image": f"./img/camisetas/{produto.json_key.replace('-', '_')}.jpeg",
                "sizes": sizes
            }
        
        # Salvar em arquivo temporário para download
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
            temp_path = f.name
        
        self.message_user(
            request,
            f'✅ products.json gerado com sucesso! Arquivo salvo em: {temp_path}',
            level='SUCCESS'
        )
    gerar_products_json.short_description = "📄 Gerar products.json"
    
    def marcar_sem_estoque(self, request, queryset):
        """Marca produtos selecionados como sem estoque"""
        for produto in queryset:
            produto.tamanhos.update(disponivel=False)
        
        self.message_user(
            request,
            f'✅ {queryset.count()} produtos marcados como sem estoque',
            level='SUCCESS'
        )
    marcar_sem_estoque.short_description = "❌ Marcar como sem estoque"


class MovimentacaoEstoqueInline(admin.TabularInline):
    """Inline para mostrar histórico de movimentações de um produto"""
    model = MovimentacaoEstoque
    extra = 0
    readonly_fields = ['data_movimentacao', 'tipo', 'quantidade_display', 'estoque_anterior', 'estoque_posterior', 'pedido', 'usuario', 'observacao', 'origem']
    fields = ['data_movimentacao', 'tipo', 'quantidade_display', 'estoque_anterior', 'estoque_posterior', 'pedido', 'usuario', 'observacao', 'origem']
    ordering = ['-data_movimentacao']
    
    def quantidade_display(self, obj):
        """Exibe quantidade com cores"""
        if obj.quantidade > 0:
            return format_html('<span style="color: green; font-weight: bold;">+{}</span>', obj.quantidade)
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', obj.quantidade)
    quantidade_display.short_description = 'Quantidade'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProdutoTamanho)
class ProdutoTamanhoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tamanho', 'estoque_display', 'disponivel_display', 'acoes']
    list_filter = ['produto', 'tamanho', 'disponivel']
    search_fields = ['produto__nome']
    list_editable = []  # Removido para usar ações customizadas
    inlines = [MovimentacaoEstoqueInline]
    
    def estoque_display(self, obj):
        """Exibe o estoque com cores"""
        if obj.estoque == 0:
            color = 'red'
            emoji = '❌'
        elif obj.estoque <= 2:
            color = 'orange'
            emoji = '⚠️'
        else:
            color = 'green'
            emoji = '✅'
        
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{}</span>',
            emoji, color, obj.estoque
        )
    estoque_display.short_description = 'Estoque'
    
    def disponivel_display(self, obj):
        """Exibe disponibilidade com ícone"""
        if obj.disponivel and obj.estoque > 0:
            return format_html('<span style="color: green;">✅ Disponível</span>')
        else:
            return format_html('<span style="color: red;">❌ Indisponível</span>')
    disponivel_display.short_description = 'Status'
    
    def acoes(self, obj):
        """Botões de ação rápida"""
        buttons = []
        
        # Botão adicionar estoque
        buttons.append(
            format_html(
                '<a class="button" href="#" onclick="adicionarEstoque({}, 5); return false;" '
                'style="background: green; color: white; padding: 2px 8px; margin: 2px;">+5</a>',
                obj.id
            )
        )
        
        # Botão remover estoque
        if obj.estoque > 0:
            buttons.append(
                format_html(
                    '<a class="button" href="#" onclick="removerEstoque({}, 1); return false;" '
                    'style="background: red; color: white; padding: 2px 8px; margin: 2px;">-1</a>',
                    obj.id
                )
            )
        
        return format_html(' '.join(buttons))
    acoes.short_description = 'Ações Rápidas'
    
    class Media:
        js = ('admin/js/estoque_admin.js',)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = [
        'data_movimentacao',
        'produto_tamanho',
        'tipo',
        'quantidade_colored',
        'estoque_anterior',
        'estoque_posterior',
        'pedido_link',
        'usuario',
        'origem'
    ]
    
    list_filter = [
        'tipo',
        'origem',
        'data_movimentacao',
        'produto_tamanho__produto',
        'usuario'
    ]
    
    search_fields = [
        'produto_tamanho__produto__nome',
        'observacao',
        'usuario',
        'pedido__id',
        'pedido__external_reference'
    ]
    
    readonly_fields = [
        'data_movimentacao',
        'produto_tamanho',
        'tipo',
        'quantidade',
        'estoque_anterior', 
        'estoque_posterior',
        'pedido',
        'usuario',
        'observacao',
        'origem'
    ]
    
    date_hierarchy = 'data_movimentacao'
    ordering = ['-data_movimentacao']
    
    def quantidade_colored(self, obj):
        """Exibe quantidade com cores"""
        if obj.quantidade > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">+{}</span>',
                obj.quantidade
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                obj.quantidade
            )
    quantidade_colored.short_description = 'Quantidade'
    quantidade_colored.admin_order_field = 'quantidade'
    
    def pedido_link(self, obj):
        """Link para o pedido relacionado"""
        if obj.pedido:
            url = reverse('admin:pedidos_pedido_change', args=[obj.pedido.id])
            return format_html('<a href="{}">Pedido #{}</a>', url, obj.pedido.id)
        return '-'
    pedido_link.short_description = 'Pedido'
    
    def has_add_permission(self, request):
        # Movimentações são criadas automaticamente
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Não permitir deletar histórico
        return False


@admin.register(Comprador)
class CompradorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'data_cadastro', 'total_pedidos']
    list_filter = ['data_cadastro']
    search_fields = ['nome', 'email', 'telefone']
    readonly_fields = ['data_cadastro']
    ordering = ['-data_cadastro']

    def total_pedidos(self, obj):
        count = obj.pedido_set.count()
        if count > 0:
            url = reverse('admin:pedidos_pedido_changelist') + f'?comprador__id__exact={obj.id}'
            return format_html('<a href="{}">{} pedidos</a>', url, count)
        return '0 pedidos'
    total_pedidos.short_description = 'Total de Pedidos'


class ItemPedidoInline(admin.TabularInline):
    """Inline para exibir e editar itens do pedido"""
    model = ItemPedido
    extra = 0
    fields = ['produto', 'tamanho', 'quantidade', 'preco_unitario', 'subtotal_display']
    readonly_fields = ['subtotal_display']
    
    def subtotal_display(self, obj):
        if obj.id:
            return f'R$ {obj.subtotal:.2f}'
        return '-'
    subtotal_display.short_description = 'Subtotal'


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [ItemPedidoInline]
    list_display = [
        'id', 
        'comprador_link', 
        'resumo_pedido', 
        'total_display',
        'forma_pagamento_display',
        'status_display_admin',
        'status_mercadopago',
        'data_pedido'
    ]
    
    list_filter = [
        'status_pagamento',
        'produto',
        'tamanho',
        'forma_pagamento',
        'data_pedido',
        'data_atualizacao',
        PedidosOrfaosFilter,
        PedidosComDadosVaziosFilter
    ]
    
    search_fields = [
        'comprador__nome',
        'comprador__email',
        'external_reference',
        'payment_id',
        'merchant_order_id'
    ]
    
    readonly_fields = [
        'data_pedido', 
        'data_atualizacao',
        'external_reference',
        'status_mercadopago',
        'link_mercadopago'
    ]
    
    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('comprador', 'produto', 'tamanho', 'preco', 'forma_pagamento')
        }),
        ('Dados Mercado Pago / PayPal', {
            'fields': (
                'external_reference', 
                'payment_id', 
                'preference_id', 
                'merchant_order_id',
                'status_mercadopago',
                'link_mercadopago'
            ),
            'classes': ('collapse',)
        }),
        ('Status e Controle', {
            'fields': ('status_pagamento', 'observacoes', 'data_pedido', 'data_atualizacao')
        })
    )
    
    actions = ['consultar_status_mp', 'marcar_como_aprovado', 'marcar_como_cancelado', 'sincronizar_estoque', 'confirmar_pagamento_presencial', 'enviar_email_confirmacao']
    
    def comprador_link(self, obj):
        url = reverse('admin:pedidos_comprador_change', args=[obj.comprador.id])
        return format_html('<a href="{}">{}</a>', url, obj.comprador.nome)
    comprador_link.short_description = 'Comprador'
    
    def resumo_pedido(self, obj):
        """Mostra resumo dos itens do pedido"""
        # Indicador de sistema
        sistema_icon = '🆕' if obj.usa_novo_sistema else '📊'
        
        if obj.itens.exists():
            # Nova estrutura com múltiplos itens
            itens = obj.itens.all()
            if itens.count() == 1:
                item = itens.first()
                return f"{sistema_icon} {item.get_produto_display()} ({item.tamanho}) x{item.quantidade}"
            else:
                return f"{sistema_icon} {itens.count()} itens - {sum(item.quantidade for item in itens)} produtos"
        else:
            # Pedido antigo - estrutura legada
            return f"{sistema_icon} {obj.get_produto_display()} ({obj.tamanho})"
    resumo_pedido.short_description = 'Produtos'
    
    def total_display(self, obj):
        """Mostra o total do pedido"""
        total = obj.total_pedido
        if obj.forma_pagamento == 'pix':
            # Mostrar valor com desconto
            total_sem_desconto = total / Decimal('0.95')
            return format_html(
                '<span style="color: green;"><s>R$ {}</s><br/>R$ {}</span>',
                f'{total_sem_desconto:.2f}', f'{total:.2f}'
            )
        return f'R$ {total:.2f}'
    total_display.short_description = 'Total'
    
    def forma_pagamento_display(self, obj):
        icons = {
            'pix': '⚡',
            '2x': '💳',
            '4x': '💳',
            'paypal': '🅿️',
            'credit_card': '💳',
            'debit_card': '💳',
            'ticket': '🎫',
            'bank_transfer': '🏦',
            'account_money': '💰',
        }
        icon = icons.get(obj.forma_pagamento, '💰')
        return f'{icon} {obj.get_forma_pagamento_display()}'
    forma_pagamento_display.short_description = 'Pagamento'
    
    def status_display_admin(self, obj):
        colors = {
            'pending': '#ffc107',     # amarelo
            'approved': '#28a745',    # verde
            'in_process': '#17a2b8',  # azul
            'rejected': '#dc3545',    # vermelho
            'cancelled': '#6c757d',   # cinza
            'refunded': '#fd7e14',    # laranja
        }
        color = colors.get(obj.status_pagamento, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status_display
        )
    status_display_admin.short_description = 'Status'
    
    def status_mercadopago(self, obj):
        """Campo readonly para exibir consulta ao MP"""
        if not obj.payment_id:
            return "Payment ID não disponível"
        return format_html(
            '<button type="button" onclick="consultarMP(\'{}\')">🔄 Consultar MP</button>',
            obj.payment_id
        )
    status_mercadopago.short_description = 'Status no MP'
    
    def link_mercadopago(self, obj):
        """Link direto para o pagamento no painel do MP/PayPal"""
        if obj.payment_id:
            if obj.forma_pagamento == 'paypal':
                # Link para PayPal (Transaction ID)
                url_paypal = f"https://www.paypal.com/activity/payment/{obj.payment_id}"
                return format_html(
                    '<a href="{}" target="_blank" style="background: #0070ba; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; display: inline-block;">🔗 Ver no PayPal</a>',
                    url_paypal
                )
            else:
                # Link para Mercado Pago
                url_activities = f"https://www.mercadopago.com.br/activities/{obj.payment_id}"
                return format_html(
                    '<a href="{}" target="_blank" style="background: #009EE3; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; display: inline-block;">🔗 Ver no MP</a>',
                    url_activities
                )
        return "Payment ID não disponível"
    link_mercadopago.short_description = 'Link Pagamento'
    
    # Actions personalizadas
    def consultar_status_mp(self, request, queryset):
        """Action melhorada para consultar status no Mercado Pago via payment_id ou external_reference"""
        import requests
        from django.conf import settings
        import json
        
        updated = 0
        errors = 0
        found_payments = 0
        
        # Token do Mercado Pago (deve estar configurado no settings)
        mp_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', os.environ.get('MERCADOPAGO_ACCESS_TOKEN'))
        
        if not mp_token:
            self.message_user(request, 'Token do Mercado Pago não configurado!', level='ERROR')
            return
        
        for pedido in queryset:
            try:
                payment_data = None
                method_used = None
                
                # Método 1: Consultar por payment_id (se disponível)
                if pedido.payment_id:
                    try:
                        response = requests.get(
                            f'https://api.mercadopago.com/v1/payments/{pedido.payment_id}',
                            headers={'Authorization': f'Bearer {mp_token}'}
                        )
                        
                        if response.status_code == 200:
                            payment_data = response.json()
                            method_used = f'payment_id: {pedido.payment_id}'
                        else:
                            self.message_user(
                                request, 
                                f'Pedido #{pedido.id}: Payment ID {pedido.payment_id} não encontrado (HTTP {response.status_code})',
                                level='WARNING'
                            )
                    except Exception as e:
                        self.message_user(
                            request, 
                            f'Pedido #{pedido.id}: Erro ao consultar payment_id: {str(e)}',
                            level='WARNING'
                        )
                
                # Método 2: Buscar por external_reference (se payment_id falhou ou não existe)
                if not payment_data and pedido.external_reference:
                    try:
                        # Buscar pagamentos por external_reference
                        search_url = 'https://api.mercadopago.com/v1/payments/search'
                        search_params = {
                            'external_reference': pedido.external_reference,
                            'limit': 50  # MP permite até 50 resultados
                        }
                        
                        search_response = requests.get(
                            search_url,
                            headers={'Authorization': f'Bearer {mp_token}'},
                            params=search_params
                        )
                        
                        if search_response.status_code == 200:
                            search_data = search_response.json()
                            results = search_data.get('results', [])
                            
                            if results:
                                # Pegar o pagamento mais recente
                                payment_data = results[0]
                                method_used = f'external_reference: {pedido.external_reference}'
                                
                                # Salvar payment_id se não existia
                                if not pedido.payment_id and payment_data.get('id'):
                                    pedido.payment_id = str(payment_data['id'])
                                    found_payments += 1
                                    self.message_user(
                                        request, 
                                        f'Pedido #{pedido.id}: Payment ID encontrado e salvo: {payment_data["id"]}',
                                        level='SUCCESS'
                                    )
                            else:
                                self.message_user(
                                    request, 
                                    f'Pedido #{pedido.id}: Nenhum pagamento encontrado com external_reference: {pedido.external_reference}',
                                    level='WARNING'
                                )
                        else:
                            self.message_user(
                                request, 
                                f'Pedido #{pedido.id}: Erro na busca por external_reference (HTTP {search_response.status_code})',
                                level='WARNING'
                            )
                    except Exception as e:
                        self.message_user(
                            request, 
                            f'Pedido #{pedido.id}: Erro ao buscar por external_reference: {str(e)}',
                            level='WARNING'
                        )
                
                # Processar dados do pagamento se encontrado
                if payment_data:
                    novo_status = payment_data.get('status', pedido.status_pagamento)
                    
                    # Atualizar campos extras se disponíveis
                    if not pedido.merchant_order_id and payment_data.get('order', {}).get('id'):
                        pedido.merchant_order_id = str(payment_data['order']['id'])
                    
                    # Atualizar status se mudou
                    if novo_status != pedido.status_pagamento:
                        pedido.status_pagamento = novo_status
                        pedido.save()
                        updated += 1
                        self.message_user(
                            request, 
                            f'Pedido #{pedido.id}: {pedido.status_pagamento} → {novo_status} (via {method_used})',
                            level='SUCCESS'
                        )
                    else:
                        pedido.save()  # Salvar payment_id ou outros campos atualizados
                        self.message_user(
                            request, 
                            f'Pedido #{pedido.id}: Status mantido ({novo_status}) (via {method_used})',
                            level='INFO'
                        )
                else:
                    # Nenhum método funcionou
                    if not pedido.payment_id and not pedido.external_reference:
                        message = f'Pedido #{pedido.id}: Sem payment_id nem external_reference para consultar'
                    elif pedido.forma_pagamento == 'presencial':
                        message = f'Pedido #{pedido.id}: Pagamento presencial - não consultável no MP'
                    else:
                        message = f'Pedido #{pedido.id}: Pagamento não encontrado no Mercado Pago'
                    
                    self.message_user(request, message, level='WARNING')
                    errors += 1
                    
            except Exception as e:
                errors += 1
                self.message_user(
                    request, 
                    f'Erro geral ao processar pedido #{pedido.id}: {str(e)}',
                    level='ERROR'
                )
        
        # Resumo final
        total_processed = queryset.count()
        self.message_user(
            request, 
            f'📊 Processados: {total_processed} pedidos | ✅ Atualizados: {updated} | 🔍 Payment IDs encontrados: {found_payments} | ❌ Erros/Avisos: {errors}',
            level='SUCCESS' if errors == 0 else 'INFO'
        )
    
    consultar_status_mp.short_description = "🔄 Consultar status no Mercado Pago"
    
    def marcar_como_aprovado(self, request, queryset):
        updated = queryset.update(status_pagamento='approved')
        self.message_user(request, f'{updated} pedidos marcados como aprovados.')
    marcar_como_aprovado.short_description = "✅ Marcar como aprovado"
    
    def marcar_como_cancelado(self, request, queryset):
        """Marca pedidos como cancelados e devolve estoque se necessário"""
        from django.db import transaction
        
        processados = 0
        estoque_devolvido = 0
        erros = 0
        
        for pedido in queryset:
            try:
                with transaction.atomic():
                    # Verificar se estoque foi decrementado e pode ser devolvido
                    if pedido.estoque_decrementado:
                        # Processar devolução de estoque
                        if pedido.usa_novo_sistema and pedido.produto_tamanho:
                            # Pedido simples (produto_tamanho)
                            if pedido.produto_tamanho.incrementar_estoque(1):
                                pedido.estoque_decrementado = False
                                estoque_devolvido += 1
                                self.message_user(
                                    request,
                                    f'Estoque devolvido para {pedido.produto_tamanho}',
                                    level='SUCCESS'
                                )
                        elif pedido.itens.exists():
                            # Pedido com múltiplos itens
                            for item in pedido.itens.all():
                                if item.produto_tamanho:
                                    item.produto_tamanho.incrementar_estoque(item.quantidade)
                            pedido.estoque_decrementado = False
                            estoque_devolvido += 1
                            self.message_user(
                                request,
                                f'Estoque devolvido para pedido #{pedido.id} ({pedido.itens.count()} itens)',
                                level='SUCCESS'
                            )
                    
                    # Marcar como cancelado
                    pedido.status_pagamento = 'cancelled'
                    pedido.save()
                    processados += 1
                    
            except Exception as e:
                erros += 1
                self.message_user(
                    request,
                    f'Erro ao cancelar pedido #{pedido.id}: {str(e)}',
                    level='ERROR'
                )
        
        # Mensagem final
        mensagem = f'{processados} pedidos cancelados'
        if estoque_devolvido > 0:
            mensagem += f' ({estoque_devolvido} tiveram estoque devolvido)'
        if erros > 0:
            mensagem += f' - {erros} erros'
        
        self.message_user(request, mensagem, level='SUCCESS' if erros == 0 else 'WARNING')
    marcar_como_cancelado.short_description = "🚫 Cancelar pedidos (e devolver estoque)"
    
    def sincronizar_estoque(self, request, queryset):
        """Sincroniza estoque para pedidos aprovados"""
        from django.db import transaction
        
        processados = 0
        erros = 0
        
        # Filtrar pedidos aprovados OU pedidos presenciais que não tiveram estoque decrementado
        from django.db.models import Q
        pedidos = queryset.filter(
            Q(status_pagamento='approved') | Q(forma_pagamento='presencial'),
            estoque_decrementado=False
        )
        
        if not pedidos.exists():
            self.message_user(
                request,
                'Nenhum pedido elegível para sincronização de estoque',
                level='WARNING'
            )
            return
        
        for pedido in pedidos:
            try:
                with transaction.atomic():
                    if pedido.usa_novo_sistema and pedido.produto_tamanho:
                        # Decrementar estoque do produto_tamanho
                        if pedido.produto_tamanho.decrementar_estoque(
                            quantidade=1,
                            pedido=pedido,
                            usuario=request.user.username if request.user.is_authenticated else 'admin',
                            observacao=f'Sincronização de estoque - Pedido #{pedido.id}',
                            origem='sincronizar_estoque_admin'
                        ):
                            pedido.estoque_decrementado = True
                            pedido.save()
                            processados += 1
                        else:
                            erros += 1
                            self.message_user(
                                request,
                                f'Pedido #{pedido.id}: Estoque insuficiente',
                                level='ERROR'
                            )
                    elif pedido.itens.exists():
                        # Processar itens do pedido
                        sucesso = True
                        for item in pedido.itens.all():
                            if item.produto_tamanho:
                                if not item.produto_tamanho.decrementar_estoque(
                                    quantidade=item.quantidade,
                                    pedido=pedido,
                                    usuario=request.user.username if request.user.is_authenticated else 'admin',
                                    observacao=f'Sincronização de estoque - Pedido #{pedido.id} - Item: {item.get_produto_display()} ({item.tamanho})',
                                    origem='sincronizar_estoque_admin'
                                ):
                                    sucesso = False
                                    break
                        
                        if sucesso:
                            pedido.estoque_decrementado = True
                            pedido.save()
                            processados += 1
                        else:
                            erros += 1
                            self.message_user(
                                request,
                                f'Pedido #{pedido.id}: Estoque insuficiente em algum item',
                                level='ERROR'
                            )
            except Exception as e:
                erros += 1
                self.message_user(
                    request,
                    f'Erro ao processar pedido #{pedido.id}: {str(e)}',
                    level='ERROR'
                )
        
        # Resumo
        if processados:
            self.message_user(
                request,
                f'✅ {processados} pedidos tiveram estoque sincronizado',
                level='SUCCESS'
            )
        if erros:
            self.message_user(
                request,
                f'❌ {erros} pedidos com erro',
                level='ERROR'
            )
    sincronizar_estoque.short_description = "📦 Sincronizar estoque"
    
    def confirmar_pagamento_presencial(self, request, queryset):
        """Confirma pagamento presencial e aprova pedidos"""
        # Filtrar apenas pedidos presenciais pendentes
        pedidos = queryset.filter(
            forma_pagamento='presencial',
            status_pagamento='pending'
        )
        
        if not pedidos.exists():
            self.message_user(
                request,
                'Nenhum pedido presencial pendente selecionado',
                level='WARNING'
            )
            return
        
        # Atualizar status
        updated = pedidos.update(
            status_pagamento='approved',
            observacoes=models.F('observacoes') + '\n\nPagamento presencial confirmado pelo admin.'
        )
        
        self.message_user(
            request,
            f'✅ {updated} pedidos presenciais confirmados e aprovados',
            level='SUCCESS'
        )
        
        # Sincronizar estoque automaticamente
        self.sincronizar_estoque(request, pedidos)
    confirmar_pagamento_presencial.short_description = "💰 Confirmar pagamento presencial"

    def enviar_email_confirmacao(self, request, queryset):
        """Envia email de confirmação para os pedidos selecionados"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        enviados = 0
        erros = 0
        
        for pedido in queryset:
            try:
                # Verificar se comprador tem email
                if not pedido.comprador.email:
                    self.message_user(
                        request,
                        f'Pedido #{pedido.id}: Comprador sem email cadastrado',
                        level='WARNING'
                    )
                    erros += 1
                    continue
                
                # Preparar dados para o template
                context = {
                    'pedido': pedido,
                    'comprador': pedido.comprador,
                    'itens': pedido.itens.all() if pedido.itens.exists() else [],
                    'total': pedido.total_pedido,
                    'usa_novo_sistema': pedido.usa_novo_sistema,
                }
                
                # Template HTML do email
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Confirmação do Pedido - ONE WAY 2025</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                        .content {{ background: #f8f9fa; padding: 20px; border: 1px solid #ddd; }}
                        .footer {{ background: #343a40; color: white; padding: 15px; text-align: center; border-radius: 0 0 5px 5px; }}
                        .item {{ background: white; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
                        .total {{ font-size: 1.2em; font-weight: bold; color: #007bff; }}
                        .status {{ padding: 5px 10px; border-radius: 3px; color: white; }}
                        .approved {{ background: #28a745; }}
                        .pending {{ background: #ffc107; color: black; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎯 ONE WAY 2025</h1>
                            <p>Confirmação do seu Pedido #{pedido.id}</p>
                        </div>
                        
                        <div class="content">
                            <h2>Olá, {pedido.comprador.nome}!</h2>
                            <p>Seu pedido foi processado com sucesso. Confira os detalhes abaixo:</p>
                            
                            <h3>📦 Itens do Pedido:</h3>
                """
                
                # Adicionar itens
                if pedido.itens.exists():
                    # Sistema novo - múltiplos itens
                    for item in pedido.itens.all():
                        html_message += f"""
                            <div class="item">
                                <strong>{item.get_produto_display()}</strong><br/>
                                <small>Tamanho: {item.tamanho} | Quantidade: {item.quantidade} | Preço unitário: R$ {item.preco_unitario:.2f}</small><br/>
                                <span class="total">Subtotal: R$ {item.subtotal:.2f}</span>
                            </div>
                        """
                else:
                    # Sistema legado - pedido único
                    html_message += f"""
                        <div class="item">
                            <strong>{pedido.get_produto_display()}</strong><br/>
                            <small>Tamanho: {pedido.tamanho}</small><br/>
                            <span class="total">Valor: R$ {pedido.preco:.2f}</span>
                        </div>
                    """
                
                # Informações de pagamento
                status_class = 'approved' if pedido.status_pagamento == 'approved' else 'pending'
                status_text = 'Aprovado ✅' if pedido.status_pagamento == 'approved' else 'Pendente ⏳'
                
                html_message += f"""
                            <h3>💳 Informações de Pagamento:</h3>
                            <div class="item">
                                <strong>Método:</strong> {pedido.get_forma_pagamento_display()}<br/>
                                <strong>Status:</strong> <span class="status {status_class}">{status_text}</span><br/>
                                <strong>Total:</strong> <span class="total">R$ {pedido.total_pedido:.2f}</span>
                """
                
                # Adicionar desconto PIX se aplicável
                if pedido.forma_pagamento == 'pix':
                    total_sem_desconto = pedido.total_pedido / Decimal('0.95')
                    html_message += f"""<br/>
                                <small style="color: green;">💰 Desconto PIX aplicado! De R$ {total_sem_desconto:.2f} por R$ {pedido.total_pedido:.2f}</small>
                    """
                
                html_message += """
                            </div>
                """
                
                # Instruções específicas por método de pagamento
                if pedido.forma_pagamento == 'presencial':
                    html_message += f"""
                            <div class="item" style="border-left-color: #ffc107;">
                                <h4>📍 Pagamento Presencial</h4>
                                <p><strong>Importante:</strong> Você tem até <strong>48 horas</strong> após este email para efetuar o pagamento na igreja.</p>
                                <p><strong>Número do Pedido:</strong> #{pedido.id}</p>
                                <p><strong>External Reference:</strong> {pedido.external_reference}</p>
                                <p>Apresente esse número na igreja para confirmar seu pagamento.</p>
                            </div>
                    """
                elif pedido.status_pagamento == 'approved':
                    html_message += """
                            <div class="item" style="border-left-color: #28a745;">
                                <h4>✅ Pagamento Confirmado</h4>
                                <p>Seu pagamento foi aprovado! Seus produtos serão entregues no evento.</p>
                            </div>
                    """
                
                html_message += f"""
                        </div>
                        
                        <div class="footer">
                            <p><strong>ONE WAY 2025</strong></p>
                            <p>31 de julho - 2 de agosto de 2025</p>
                            <p>Este é um email automático, não responda.</p>
                            <p><small>Pedido gerado em: {pedido.data_pedido.strftime('%d/%m/%Y às %H:%M')}</small></p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Texto simples como fallback
                text_message = f"""
                ONE WAY 2025 - Confirmação do Pedido #{pedido.id}
                
                Olá, {pedido.comprador.nome}!
                
                Seu pedido foi processado com sucesso.
                """
                
                if pedido.itens.exists():
                    text_message += "\n\nItens do Pedido:\n"
                    for item in pedido.itens.all():
                        text_message += f"- {item.get_produto_display()} ({item.tamanho}) x{item.quantidade} - R$ {item.subtotal:.2f}\n"
                else:
                    text_message += f"\nProduto: {pedido.get_produto_display()} ({pedido.tamanho}) - R$ {pedido.preco:.2f}\n"
                
                text_message += f"""
                Método de Pagamento: {pedido.get_forma_pagamento_display()}
                Status: {status_text}
                Total: R$ {pedido.total_pedido:.2f}
                
                ONE WAY 2025
                31 de julho - 2 de agosto de 2025
                """
                
                # Assunto do email
                assunto = f"Confirmação do Pedido #{pedido.id} - ONE WAY 2025"
                
                # Enviar email
                send_mail(
                    subject=assunto,
                    message=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[pedido.comprador.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                enviados += 1
                self.message_user(
                    request,
                    f'Email enviado para {pedido.comprador.nome} ({pedido.comprador.email})',
                    level='SUCCESS'
                )
                
            except Exception as e:
                erros += 1
                self.message_user(
                    request,
                    f'Erro ao enviar email para pedido #{pedido.id}: {str(e)}',
                    level='ERROR'
                )
        
        # Resumo final
        if enviados > 0:
            self.message_user(
                request,
                f'✅ {enviados} email(s) de confirmação enviado(s) com sucesso!',
                level='SUCCESS'
            )
        if erros > 0:
            self.message_user(
                request,
                f'❌ {erros} erro(s) ao enviar emails',
                level='ERROR'
            )
    
    enviar_email_confirmacao.short_description = "📧 Enviar email de confirmação"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('comprador')

    class Media:
        js = ('admin/js/consultar_mp.js',)
        css = {
            'all': ('admin/css/pedidos_admin.css',)
        }

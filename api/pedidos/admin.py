from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import Comprador, Pedido, ItemPedido, Produto, ProdutoTamanho
import requests
from django.conf import settings
import os


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
        elif obj.estoque <= 5:
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


@admin.register(ProdutoTamanho)
class ProdutoTamanhoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tamanho', 'estoque_display', 'disponivel_display', 'acoes']
    list_filter = ['produto', 'tamanho', 'disponivel']
    search_fields = ['produto__nome']
    list_editable = []  # Removido para usar ações customizadas
    
    def estoque_display(self, obj):
        """Exibe o estoque com cores"""
        if obj.estoque == 0:
            color = 'red'
            emoji = '❌'
        elif obj.estoque <= 5:
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
        'data_atualizacao'
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
    
    actions = ['consultar_status_mp', 'marcar_como_aprovado', 'marcar_como_cancelado', 'sincronizar_estoque', 'confirmar_pagamento_presencial']
    
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
        """Action para consultar status no Mercado Pago"""
        import requests
        from django.conf import settings
        
        updated = 0
        errors = 0
        
        # Token do Mercado Pago (deve estar configurado no settings)
        mp_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', os.environ.get('MERCADOPAGO_ACCESS_TOKEN'))
        
        if not mp_token:
            self.message_user(request, 'Token do Mercado Pago não configurado!', level='ERROR')
            return
        
        for pedido in queryset:
            if pedido.payment_id:
                try:
                    # Consultar API do Mercado Pago
                    response = requests.get(
                        f'https://api.mercadopago.com/v1/payments/{pedido.payment_id}',
                        headers={'Authorization': f'Bearer {mp_token}'}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        novo_status = data.get('status', pedido.status_pagamento)
                        
                        # Atualizar status se mudou
                        if novo_status != pedido.status_pagamento:
                            pedido.status_pagamento = novo_status
                            pedido.save()
                            updated += 1
                            self.message_user(
                                request, 
                                f'Pedido #{pedido.id}: {pedido.status_pagamento} → {novo_status}',
                                level='SUCCESS'
                            )
                        else:
                            self.message_user(
                                request, 
                                f'Pedido #{pedido.id}: Status mantido ({novo_status})',
                                level='INFO'
                            )
                    else:
                        errors += 1
                        self.message_user(
                            request, 
                            f'Erro ao consultar pedido #{pedido.id}: HTTP {response.status_code}',
                            level='ERROR'
                        )
                except Exception as e:
                    errors += 1
                    self.message_user(
                        request, 
                        f'Erro ao consultar pedido #{pedido.id}: {str(e)}',
                        level='ERROR'
                    )
        
        # Resumo final
        if updated:
            self.message_user(request, f'✅ {updated} pedidos atualizados no total.', level='SUCCESS')
        if errors:
            self.message_user(request, f'❌ {errors} erros durante a consulta.', level='ERROR')
    
    consultar_status_mp.short_description = "🔄 Consultar status no Mercado Pago"
    
    def marcar_como_aprovado(self, request, queryset):
        updated = queryset.update(status_pagamento='approved')
        self.message_user(request, f'{updated} pedidos marcados como aprovados.')
    marcar_como_aprovado.short_description = "✅ Marcar como aprovado"
    
    def marcar_como_cancelado(self, request, queryset):
        updated = queryset.update(status_pagamento='cancelled')
        self.message_user(request, f'{updated} pedidos marcados como cancelados.')
    marcar_como_cancelado.short_description = "🚫 Marcar como cancelado"
    
    def sincronizar_estoque(self, request, queryset):
        """Sincroniza estoque para pedidos aprovados"""
        from django.db import transaction
        
        processados = 0
        erros = 0
        
        # Filtrar apenas pedidos aprovados que não tiveram estoque decrementado
        pedidos = queryset.filter(
            status_pagamento='approved',
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
                        if pedido.produto_tamanho.decrementar_estoque(1):
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
                                if not item.produto_tamanho.decrementar_estoque(item.quantidade):
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('comprador')

    class Media:
        js = ('admin/js/consultar_mp.js',)
        css = {
            'all': ('admin/css/pedidos_admin.css',)
        }

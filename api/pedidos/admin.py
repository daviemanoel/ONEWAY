from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import Comprador, Pedido, ItemPedido
import requests
from django.conf import settings
import os


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
    
    actions = ['consultar_status_mp', 'marcar_como_aprovado', 'marcar_como_cancelado']
    
    def comprador_link(self, obj):
        url = reverse('admin:pedidos_comprador_change', args=[obj.comprador.id])
        return format_html('<a href="{}">{}</a>', url, obj.comprador.nome)
    comprador_link.short_description = 'Comprador'
    
    def resumo_pedido(self, obj):
        """Mostra resumo dos itens do pedido"""
        if obj.itens.exists():
            # Nova estrutura com múltiplos itens
            itens = obj.itens.all()
            if itens.count() == 1:
                item = itens.first()
                return f"{item.get_produto_display()} ({item.tamanho}) x{item.quantidade}"
            else:
                return f"{itens.count()} itens - {sum(item.quantidade for item in itens)} produtos"
        else:
            # Pedido antigo - estrutura legada
            return f"{obj.get_produto_display()} ({obj.tamanho})"
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('comprador')

    class Media:
        js = ('admin/js/consultar_mp.js',)
        css = {
            'all': ('admin/css/pedidos_admin.css',)
        }

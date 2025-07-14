from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Comprador, Pedido
import requests
from django.conf import settings


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


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'comprador_link', 
        'produto_display', 
        'tamanho', 
        'preco_final',
        'forma_pagamento_display',
        'status_display_admin',
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
        ('Dados Mercado Pago', {
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
    
    def produto_display(self, obj):
        return obj.get_produto_display()
    produto_display.short_description = 'Produto'
    
    def preco_final(self, obj):
        valor = obj.valor_com_desconto
        if obj.forma_pagamento == 'pix' and valor < obj.preco:
            return format_html(
                '<span style="color: green;"><s>R$ {:.2f}</s><br/>R$ {:.2f}</span>',
                obj.preco, valor
            )
        return f'R$ {valor:.2f}'
    preco_final.short_description = 'Preço Final'
    
    def forma_pagamento_display(self, obj):
        icons = {
            'pix': '⚡',
            '2x': '💳',
            '4x': '💳',
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
        """Link direto para o pagamento no painel do MP"""
        if obj.payment_id:
            return format_html(
                '<a href="https://www.mercadopago.com.br/activities/detail/{}" target="_blank">🔗 Ver no MP</a>',
                obj.payment_id
            )
        return "Payment ID não disponível"
    link_mercadopago.short_description = 'Link MP'
    
    # Actions personalizadas
    def consultar_status_mp(self, request, queryset):
        """Action para consultar status no Mercado Pago"""
        updated = 0
        for pedido in queryset:
            if pedido.payment_id:
                # Aqui seria implementada a consulta à API do MP
                # Por ora, apenas simular
                self.message_user(request, f'Consultando pedido {pedido.id}...')
                updated += 1
        
        if updated:
            self.message_user(request, f'{updated} pedidos consultados no Mercado Pago.')
        else:
            self.message_user(request, 'Nenhum pedido tinha Payment ID para consulta.')
    
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

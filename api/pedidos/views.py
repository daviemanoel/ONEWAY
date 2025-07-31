from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
import requests
import json
import os
from django.conf import settings
from .models import Comprador, Pedido, ItemPedido
from .serializers import (
    CompradorSerializer, 
    PedidoSerializer, 
    CriarPedidoSerializer,
    AtualizarStatusSerializer,
    ItemPedidoSerializer
)


class CompradorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para visualizar compradores (somente leitura)"""
    queryset = Comprador.objects.all()
    serializer_class = CompradorSerializer
    authentication_classes = [TokenAuthentication]
    
    permission_classes = [IsAuthenticated]


class ItemPedidoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar itens de pedido"""
    queryset = ItemPedido.objects.all()
    serializer_class = ItemPedidoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class PedidoViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gerenciar pedidos"""
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    authentication_classes = [TokenAuthentication]
    
    permission_classes = [IsAuthenticated]
    
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


@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def consultar_mp_admin(request):
    """Endpoint para consultar status MP via admin interface"""
    try:
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return JsonResponse({
                'success': False,
                'error': 'Payment ID é obrigatório'
            })
        
        # Buscar pedido no banco
        try:
            pedido = Pedido.objects.get(payment_id=payment_id)
        except Pedido.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Pedido com payment_id {payment_id} não encontrado'
            })
        
        # Token do Mercado Pago
        mp_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', os.environ.get('MERCADOPAGO_ACCESS_TOKEN'))
        
        if not mp_token:
            return JsonResponse({
                'success': False,
                'error': 'Token do Mercado Pago não configurado'
            })
        
        # Consultar API do Mercado Pago
        response = requests.get(
            f'https://api.mercadopago.com/v1/payments/{payment_id}',
            headers={'Authorization': f'Bearer {mp_token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            mp_data = response.json()
            novo_status = mp_data.get('status', pedido.status_pagamento)
            status_detail = mp_data.get('status_detail', '')
            
            # Atualizar status se mudou
            status_mudou = False
            if novo_status != pedido.status_pagamento:
                pedido.status_pagamento = novo_status
                pedido.save()
                status_mudou = True
            
            # Mapear status para display
            status_display_map = {
                'pending': 'Pendente',
                'approved': 'Aprovado',
                'in_process': 'Em processamento',
                'rejected': 'Rejeitado',
                'cancelled': 'Cancelado',
                'refunded': 'Estornado',
            }
            
            return JsonResponse({
                'success': True,
                'pedido_id': pedido.id,
                'payment_id': payment_id,
                'status_anterior': pedido.status_pagamento if not status_mudou else '',
                'novo_status': novo_status,
                'status_display': status_display_map.get(novo_status, novo_status),
                'status_detail': status_detail,
                'status_mudou': status_mudou,
                'detalhes': {
                    'transaction_amount': mp_data.get('transaction_amount'),
                    'payment_method_id': mp_data.get('payment_method_id'),
                    'date_created': mp_data.get('date_created'),
                    'date_approved': mp_data.get('date_approved'),
                }
            })
        
        elif response.status_code == 404:
            return JsonResponse({
                'success': False,
                'error': f'Payment {payment_id} não encontrado no Mercado Pago'
            })
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Erro na API do MP: HTTP {response.status_code}'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido na requisição'
        })
    
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'Timeout na consulta ao Mercado Pago'
        })
    
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro de conexão: {str(e)}'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })


@action(detail=False, methods=['get'])
def pedidos_incompletos(self, request):
    """Lista pedidos que podem estar incompletos (sem dados MP quando deveriam ter)"""
    from django.db.models import Q
    
    # Formas de pagamento que requerem dados MP
    pagamentos_com_gateway = ['pix', '2x', '4x', 'paypal', 'paypal_3x', 'mercadopago']
    
    # Buscar pedidos com forma de pagamento via gateway mas sem dados MP
    pedidos_problematicos = Pedido.objects.filter(
        Q(forma_pagamento__in=pagamentos_com_gateway) &
        (Q(payment_id__isnull=True) | Q(payment_id__exact='') |
         Q(external_reference__isnull=True) | Q(external_reference__exact=''))
    ).select_related('comprador').order_by('-data_pedido')
    
    # Buscar também pedidos antigos sem status atualizado há muito tempo
    from django.utils import timezone
    from datetime import timedelta
    
    limite_tempo = timezone.now() - timedelta(hours=2)
    pedidos_antigos_pendentes = Pedido.objects.filter(
        forma_pagamento__in=pagamentos_com_gateway,
        status_pagamento='pending',
        data_pedido__lt=limite_tempo
    ).select_related('comprador').order_by('-data_pedido')
    
    # Serializar os dados
    problematicos_data = []
    for pedido in pedidos_problematicos:
        problematicos_data.append({
            'id': pedido.id,
            'comprador': pedido.comprador.nome,
            'email': pedido.comprador.email,
            'produto': pedido.get_produto_display(),
            'tamanho': pedido.tamanho,
            'forma_pagamento': pedido.get_forma_pagamento_display(),
            'external_reference': pedido.external_reference,
            'payment_id': pedido.payment_id,
            'status_pagamento': pedido.get_status_pagamento_display(),
            'data_pedido': pedido.data_pedido.strftime('%d/%m/%Y %H:%M'),
            'problema': 'Dados MP ausentes'
        })
    
    antigos_data = []
    for pedido in pedidos_antigos_pendentes:
        antigos_data.append({
            'id': pedido.id,
            'comprador': pedido.comprador.nome,
            'email': pedido.comprador.email,
            'produto': pedido.get_produto_display(),
            'tamanho': pedido.tamanho,
            'forma_pagamento': pedido.get_forma_pagamento_display(),
            'external_reference': pedido.external_reference,
            'payment_id': pedido.payment_id,
            'status_pagamento': pedido.get_status_pagamento_display(),
            'data_pedido': pedido.data_pedido.strftime('%d/%m/%Y %H:%M'),
            'problema': f'Pendente há mais de 2h'
        })
    
    return Response({
        'pedidos_sem_dados_mp': problematicos_data,
        'pedidos_antigos_pendentes': antigos_data,
        'total_problematicos': len(problematicos_data),
        'total_antigos': len(antigos_data),
        'resumo': {
            'total_problemas': len(problematicos_data) + len(antigos_data),
            'tipos_problema': ['Dados MP ausentes', 'Pendente há mais de 2h']
        }
    })

from django.http import HttpResponse, JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
import io
import sys

@csrf_exempt
@staff_member_required
def setup_estoque_view(request):
    """
    Dashboard administrativo centralizado para todas as ações manuais do sistema
    Acesse: https://api.oneway.mevamfranca.com.br/api/setup-estoque/
    REQUER: Autenticação como staff member
    """
    if request.method == 'POST':
        # Executar comando via AJAX
        return execute_command_ajax(request)
    
    # GET - Mostrar dashboard
    from .models import ProdutoTamanho, Pedido
    
    # Estatísticas atuais
    from django.db.models import Q
    produtos_esgotados = ProdutoTamanho.objects.filter(estoque=0).count()
    produtos_baixo_estoque = ProdutoTamanho.objects.filter(estoque__gt=0, estoque__lte=2).count()
    # Pedidos que precisam sincronizar estoque: aprovados OU presenciais
    pedidos_pendentes = Pedido.objects.filter(
        Q(status_pagamento='approved') | Q(forma_pagamento='presencial'),
        estoque_decrementado=False
    ).count()
    pedidos_presenciais = Pedido.objects.filter(forma_pagamento='presencial', status_pagamento='pending').count()
    
    html_response = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Administrativo - ONEWAY</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                line-height: 1.6;
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            .header {{
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 30px;
            }}
            
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .stat-card {{
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
            }}
            
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            
            .stat-number.danger {{ color: #e74c3c; }}
            .stat-number.warning {{ color: #f39c12; }}
            .stat-number.success {{ color: #27ae60; }}
            .stat-number.info {{ color: #3498db; }}
            
            .sections {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 25px;
            }}
            
            .section {{
                background: rgba(255, 255, 255, 0.95);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}
            
            .section h2 {{
                font-size: 1.4em;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #f1f1f1;
                color: #2c3e50;
            }}
            
            .btn {{
                display: block;
                width: 100%;
                padding: 12px 20px;
                margin: 10px 0;
                border: none;
                border-radius: 8px;
                font-size: 1em;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            
            .btn.danger {{
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                color: white;
            }}
            
            .btn.primary {{
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
            }}
            
            .btn.success {{
                background: linear-gradient(135deg, #27ae60, #229954);
                color: white;
            }}
            
            .btn.warning {{
                background: linear-gradient(135deg, #f39c12, #e67e22);
                color: white;
            }}
            
            .btn.secondary {{
                background: linear-gradient(135deg, #95a5a6, #7f8c8d);
                color: white;
            }}
            
            .logs {{
                background: #2c3e50;
                color: #ecf0f1;
                padding: 20px;
                border-radius: 10px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                max-height: 400px;
                overflow-y: auto;
                margin-top: 20px;
                display: none;
                position: relative;
            }}
            
            .logs-controls {{
                position: sticky;
                top: 0;
                background: #34495e;
                margin: -20px -20px 15px -20px;
                padding: 10px 20px;
                border-radius: 10px 10px 0 0;
                border-bottom: 1px solid #4a6278;
            }}
            
            .logs-btn {{
                background: #e74c3c;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.8em;
                margin-right: 10px;
            }}
            
            .logs-btn.success {{
                background: #27ae60;
            }}
            
            .logs-btn:hover {{
                opacity: 0.8;
            }}
            
            .loading {{
                display: none;
                text-align: center;
                padding: 20px;
            }}
            
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            .links {{
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                margin-top: 30px;
                text-align: center;
            }}
            
            .links a {{
                display: inline-block;
                margin: 0 15px;
                padding: 10px 20px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                transition: all 0.3s ease;
            }}
            
            .links a:hover {{
                transform: scale(1.05);
            }}
            
            .description {{
                color: #7f8c8d;
                font-size: 0.9em;
                margin-top: 5px;
                line-height: 1.4;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Dashboard Administrativo</h1>
                <p>Sistema de Controle de Estoque - ONE WAY 2025</p>
                <p style="color: #7f8c8d; margin-top: 10px;">Logado como: <strong>{request.user.username}</strong></p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number danger">{produtos_esgotados}</div>
                    <div class="stat-label">Produtos Esgotados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number warning">{produtos_baixo_estoque}</div>
                    <div class="stat-label">Estoque Baixo (&lt; 2)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number info">{pedidos_pendentes}</div>
                    <div class="stat-label">Pedidos p/ Processar</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number warning">{pedidos_presenciais}</div>
                    <div class="stat-label">Pagamentos Presenciais</div>
                </div>
            </div>
            
            <div class="sections">
                <div class="section">
                    <h2>🔄 Operações de Estoque</h2>
                    <button class="btn danger" onclick="executeCommand('reset_estoque', '--confirmar')">
                        🔄 Reset Completo do Estoque
                    </button>
                    <div class="description">Restaura estoque original e marca pedidos para reprocessamento</div>
                    
                    <button class="btn primary" onclick="executeCommand('sincronizar_estoque')">
                        📦 Sincronizar Estoque
                    </button>
                    <div class="description">Processa pedidos aprovados + presenciais e decrementa estoque</div>
                    
                    <button class="btn success" onclick="executeCommand('sincronizar_estoque', '--gerar-json')">
                        📦 Sincronizar + Gerar JSON
                    </button>
                    <div class="description">Sincroniza estoque e gera products.json atualizado</div>
                    
                    <button class="btn success" onclick="executeCommand('setup_estoque_simples')">
                        🚀 Setup Inicial
                    </button>
                    <div class="description">Configura produtos e estoque inicial no sistema</div>
                </div>
                
                <div class="section">
                    <h2>📄 Geração de Arquivos</h2>
                    <button class="btn primary" onclick="executeCommand('gerar_products_json')">
                        📄 Gerar Products.json
                    </button>
                    <div class="description">Atualiza products.json com dados atuais do estoque</div>
                    
                    <button class="btn success" onclick="executeCommand('migrar_produtos')">
                        📦 Migrar Produtos do JSON
                    </button>
                    <div class="description">Importa produtos do products.json para o Django (somente novos)</div>
                    
                    <a href="/api/gerar-products-json/" target="_blank" class="btn success">
                        📥 Download JSON Atual
                    </a>
                    <div class="description">Baixa o products.json gerado mais recentemente</div>
                </div>
                
                <div class="section">
                    <h2>🔧 Manutenção</h2>
                    <button class="btn warning" onclick="executeCommand('associar_pedidos_legacy')">
                        🔗 Associar Pedidos Legacy
                    </button>
                    <div class="description">Conecta pedidos antigos ao novo sistema de estoque</div>
                    
                    <button class="btn secondary" onclick="executeCommand('criar_token_api')">
                        🔑 Criar Token API
                    </button>
                    <div class="description">Gera novo token para comunicação Django ↔ Node.js</div>
                </div>
                
                <div class="section">
                    <h2>📊 Relatórios e Diagnóstico</h2>
                    <a href="/api/relatorio-vendas/" target="_blank" class="btn success">
                        📈 Relatório de Vendas
                    </a>
                    <div class="description">Visualiza quantidade vendida por produto e tamanho</div>
                    
                    <button class="btn primary" onclick="executeCommand('sincronizar_estoque', '--dry-run')">
                        🔍 Simular Sincronização
                    </button>
                    <div class="description">Testa sincronização sem alterar dados</div>
                    
                    <button class="btn warning" onclick="executeCommand('reset_estoque', '--dry-run')">
                        🔍 Simular Reset
                    </button>
                    <div class="description">Testa reset sem alterar dados</div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Executando comando... Por favor, aguarde.</p>
            </div>
            
            <div class="logs" id="logs">
                <div class="logs-controls">
                    <button class="logs-btn" onclick="fecharLogs()">❌ Fechar Logs</button>
                    <button class="logs-btn success" onclick="recarregarPagina()">🔄 Recarregar Página</button>
                    <span style="float: right; font-size: 0.8em; color: #bdc3c7;">Logs ficam visíveis até você fechar</span>
                </div>
                <div id="logs-content"></div>
            </div>
            
            <div class="links">
                <a href="/admin" target="_blank">🔧 Django Admin</a>
                <a href="https://oneway.mevamfranca.com.br" target="_blank">🌐 Site ONEWAY</a>
                <a href="https://api.oneway.mevamfranca.com.br/api/pedidos/" target="_blank">📊 API Pedidos</a>
            </div>
        </div>
        
        <script>
            async function executeCommand(command, args = '') {{
                const loading = document.getElementById('loading');
                const logs = document.getElementById('logs');
                
                // Mostrar loading
                loading.style.display = 'block';
                logs.style.display = 'none';
                document.getElementById('logs-content').innerHTML = '';
                
                try {{
                    const formData = new FormData();
                    formData.append('command', command);
                    formData.append('args', args);
                    
                    const response = await fetch('/api/setup-estoque/', {{
                        method: 'POST',
                        body: formData,
                        headers: {{
                            'X-CSRFToken': getCookie('csrftoken')
                        }}
                    }});
                    
                    const result = await response.text();
                    
                    // Ocultar loading e mostrar logs
                    loading.style.display = 'none';
                    logs.style.display = 'block';
                    document.getElementById('logs-content').innerHTML = result;
                    
                    // Scroll para os logs
                    logs.scrollIntoView({{ behavior: 'smooth' }});
                    
                    // Logs permanecem visíveis - não recarregar automaticamente
                    
                }} catch (error) {{
                    loading.style.display = 'none';
                    logs.style.display = 'block';
                    document.getElementById('logs-content').innerHTML = '<span style="color: #e74c3c;">❌ Erro: ' + error.message + '</span>';
                }}
            }}
            
            function getCookie(name) {{
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {{
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {{
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }}
                    }}
                }}
                return cookieValue;
            }}
            
            function fecharLogs() {{
                const logs = document.getElementById('logs');
                logs.style.display = 'none';
            }}
            
            function recarregarPagina() {{
                window.location.reload();
            }}
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html_response, content_type='text/html')


@csrf_exempt
@staff_member_required
def execute_command_ajax(request):
    """
    Executa comandos Django via AJAX para o dashboard administrativo
    POST /api/setup-estoque/ com command e args
    """
    if request.method != 'POST':
        return HttpResponse('❌ Método não permitido', status=405)
    
    command = request.POST.get('command', '')
    args_str = request.POST.get('args', '')
    
    if not command:
        return HttpResponse('❌ Comando não especificado', status=400)
    
    # Lista de comandos permitidos por segurança
    allowed_commands = [
        'reset_estoque',
        'sincronizar_estoque', 
        'setup_estoque_simples',
        'migrar_produtos',
        'gerar_products_json',
        'associar_pedidos_legacy',
        'criar_token_api'
    ]
    
    if command not in allowed_commands:
        return HttpResponse(f'❌ Comando não permitido: {command}', status=403)
    
    # Capturar output do comando
    output_buffer = io.StringIO()
    
    try:
        # Redirecionar stdout para capturar logs
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        
        # Preparar argumentos do comando
        args_list = []
        if args_str:
            args_list = args_str.split(' ')
            args_list = [arg for arg in args_list if arg]  # Remove strings vazias
        
        # Executar o comando
        call_command(command, *args_list)
        
        # Restaurar stdout
        sys.stdout = old_stdout
        
        # Pegar o output
        output = output_buffer.getvalue()
        
        # Formatar output para HTML
        output_html = output.replace('\n', '<br>').replace(' ', '&nbsp;')
        
        # Adicionar cores baseado no conteúdo
        output_html = output_html.replace('✅', '<span style="color: #27ae60;">✅</span>')
        output_html = output_html.replace('❌', '<span style="color: #e74c3c;">❌</span>')
        output_html = output_html.replace('⚠️', '<span style="color: #f39c12;">⚠️</span>')
        output_html = output_html.replace('🔄', '<span style="color: #3498db;">🔄</span>')
        output_html = output_html.replace('📦', '<span style="color: #9b59b6;">📦</span>')
        output_html = output_html.replace('🚀', '<span style="color: #e67e22;">🚀</span>')
        
        return HttpResponse(output_html, content_type='text/html')
        
    except Exception as e:
        # Restaurar stdout em caso de erro
        sys.stdout = old_stdout
        
        error_msg = f'❌ Erro ao executar comando "{command}": {str(e)}'
        return HttpResponse(error_msg, content_type='text/html', status=500)
    
    finally:
        output_buffer.close()


@csrf_exempt
def validar_estoque_view(request):
    """
    Endpoint para validar estoque de um produto específico
    GET /api/validar-estoque/?product_size_id=123
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    product_size_id = request.GET.get('product_size_id')
    
    if not product_size_id:
        return JsonResponse({
            'error': 'product_size_id é obrigatório'
        }, status=400)
    
    try:
        from .models import ProdutoTamanho
        
        produto_tamanho = ProdutoTamanho.objects.select_related('produto').get(
            id=product_size_id
        )
        
        return JsonResponse({
            'product_size_id': produto_tamanho.id,
            'produto': {
                'id': produto_tamanho.produto.id,
                'nome': produto_tamanho.produto.nome,
                'preco': float(produto_tamanho.produto.preco),
                'json_key': produto_tamanho.produto.json_key
            },
            'tamanho': produto_tamanho.tamanho,
            'estoque': produto_tamanho.estoque,
            'disponivel': produto_tamanho.disponivel,
            'pode_comprar': produto_tamanho.esta_disponivel,
            'status': 'disponivel' if produto_tamanho.esta_disponivel else 'indisponivel'
        })
        
    except ProdutoTamanho.DoesNotExist:
        return JsonResponse({
            'error': 'Produto/tamanho não encontrado'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'error': f'Erro interno: {str(e)}'
        }, status=500)


@csrf_exempt  
def estoque_multiplo_view(request):
    """
    Endpoint para validar estoque de múltiplos produtos
    POST /api/estoque-multiplo/
    Body: {"items": [{"product_size_id": 123, "quantidade": 2}, ...]}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        import json
        from .models import ProdutoTamanho
        
        data = json.loads(request.body)
        items = data.get('items', [])
        
        if not items:
            return JsonResponse({
                'error': 'Lista de items é obrigatória'
            }, status=400)
        
        resultado = {
            'items': [],
            'pode_processar': True,
            'total_valor': 0,
            'erros': []
        }
        
        for item in items:
            product_size_id = item.get('product_size_id')
            quantidade = item.get('quantidade', 1)
            
            if not product_size_id:
                resultado['erros'].append('product_size_id é obrigatório em todos os items')
                continue
            
            try:
                produto_tamanho = ProdutoTamanho.objects.select_related('produto').get(
                    id=product_size_id
                )
                
                # Validar estoque
                estoque_suficiente = produto_tamanho.estoque >= quantidade
                pode_comprar = produto_tamanho.disponivel and estoque_suficiente
                
                item_resultado = {
                    'product_size_id': produto_tamanho.id,
                    'produto_nome': produto_tamanho.produto.nome,
                    'tamanho': produto_tamanho.tamanho,
                    'quantidade_solicitada': quantidade,
                    'estoque_disponivel': produto_tamanho.estoque,
                    'preco_unitario': float(produto_tamanho.produto.preco),
                    'subtotal': float(produto_tamanho.produto.preco * quantidade),
                    'pode_comprar': pode_comprar,
                    'status': 'ok' if pode_comprar else 'sem_estoque'
                }
                
                if pode_comprar:
                    resultado['total_valor'] += item_resultado['subtotal']
                else:
                    resultado['pode_processar'] = False
                    item_resultado['erro'] = f'Estoque insuficiente. Disponível: {produto_tamanho.estoque}, Solicitado: {quantidade}'
                
                resultado['items'].append(item_resultado)
                
            except ProdutoTamanho.DoesNotExist:
                resultado['erros'].append(f'Produto com ID {product_size_id} não encontrado')
                resultado['pode_processar'] = False
        
        return JsonResponse(resultado)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'error': f'Erro interno: {str(e)}'
        }, status=500)


@csrf_exempt
def gerar_products_json_view(request):
    """
    Endpoint para gerar products.json atualizado via HTTP
    GET /api/gerar-products-json/
    """
    if request.method != 'GET':
        return HttpResponse('Método não permitido', status=405)
    
    output_buffer = io.StringIO()
    
    try:
        # Capturar output do comando
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        
        call_command('gerar_products_json')
        
        sys.stdout = old_stdout
        output = output_buffer.getvalue()
        
        # Retornar como HTML
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Geração Products.JSON</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: monospace; background: #1e1e1e; color: #00ff00; padding: 20px; }}
                pre {{ white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <h1>📄 Geração Products.JSON - ONEWAY</h1>
            <pre>{output}</pre>
            <hr>
            <p><a href="/admin" target="_blank">🔗 Django Admin</a></p>
            <p><a href="/api/setup-estoque/" target="_blank">🔗 Setup Estoque</a></p>
        </body>
        </html>
        """
        
        return HttpResponse(html_response, content_type='text/html')
        
    except Exception as e:
        sys.stdout = old_stdout
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erro - Geração JSON</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: monospace; background: #1e1e1e; color: #ff4444; padding: 20px; }}
            </style>
        </head>
        <body>
            <h1>❌ Erro na Geração do Products.JSON</h1>
            <pre>{str(e)}</pre>
            <p><a href="javascript:history.back()">⬅️ Voltar</a></p>
        </body>
        </html>
        """
        
        return HttpResponse(error_html, content_type='text/html', status=500)
    
    finally:
        output_buffer.close()


@csrf_exempt
def decrementar_estoque_view(request):
    """
    Endpoint para decrementar estoque imediatamente (pagamento presencial)
    POST /api/decrementar-estoque/
    Body: {"items": [{"product_size_id": 1, "quantidade": 2}, ...], "pedido_id": 123}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    # Verificar autenticação por token
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return JsonResponse({'error': 'Token de autorização obrigatório'}, status=401)
    
    try:
        import json
        from django.db import transaction
        from .models import ProdutoTamanho, Pedido
        
        data = json.loads(request.body)
        items = data.get('items', [])
        pedido_id = data.get('pedido_id')  # Opcional
        
        # Buscar pedido se fornecido
        pedido_obj = None
        if pedido_id:
            try:
                pedido_obj = Pedido.objects.get(id=pedido_id)
            except Pedido.DoesNotExist:
                pass
        
        if not items:
            return JsonResponse({
                'error': 'Lista de items é obrigatória'
            }, status=400)
        
        resultado = {
            'success': True,
            'items_processados': [],
            'erros': []
        }
        
        with transaction.atomic():
            for item in items:
                product_size_id = item.get('product_size_id')
                quantidade = item.get('quantidade', 1)
                
                if not product_size_id:
                    resultado['erros'].append('product_size_id é obrigatório em todos os items')
                    continue
                
                try:
                    produto_tamanho = ProdutoTamanho.objects.select_related('produto').get(
                        id=product_size_id
                    )
                    
                    # Verificar se há estoque suficiente
                    if produto_tamanho.estoque < quantidade:
                        resultado['success'] = False
                        resultado['erros'].append(
                            f'{produto_tamanho}: Estoque insuficiente (disponível: {produto_tamanho.estoque}, solicitado: {quantidade})'
                        )
                        continue
                    
                    # Decrementar estoque
                    if produto_tamanho.decrementar_estoque(
                        quantidade=quantidade,
                        pedido=pedido_obj,
                        usuario='api_pagamento_presencial',
                        observacao=f'Pagamento presencial - Pedido #{pedido_obj.id if pedido_obj else "N/A"}',
                        origem='decrementar_estoque_view'
                    ):
                        resultado['items_processados'].append({
                            'product_size_id': produto_tamanho.id,
                            'produto_nome': produto_tamanho.produto.nome,
                            'tamanho': produto_tamanho.tamanho,
                            'quantidade_decrementada': quantidade,
                            'estoque_restante': produto_tamanho.estoque,
                            'ainda_disponivel': produto_tamanho.disponivel
                        })
                    else:
                        resultado['success'] = False
                        resultado['erros'].append(f'{produto_tamanho}: Falha ao decrementar estoque')
                
                except ProdutoTamanho.DoesNotExist:
                    resultado['success'] = False
                    resultado['erros'].append(f'Produto com ID {product_size_id} não encontrado')
            
            # Se houve erros, fazer rollback
            if not resultado['success']:
                raise Exception('Rollback devido a erros')
            
            # Se foi fornecido pedido_id e o decremento foi bem-sucedido, marcar flag
            if pedido_id and resultado['success']:
                try:
                    pedido = Pedido.objects.get(id=pedido_id)
                    pedido.estoque_decrementado = True
                    pedido.save()
                    resultado['pedido_atualizado'] = True
                except Pedido.DoesNotExist:
                    resultado['erro_pedido'] = f'Pedido {pedido_id} não encontrado'
        
        return JsonResponse(resultado)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }, status=500)


@staff_member_required
def relatorio_vendas_view(request):
    """
    Relatório de vendas mostrando quantidade vendida por produto e tamanho
    GET /api/relatorio-vendas/
    """
    from django.db.models import Sum, Count, Q
    from .models import ItemPedido, Pedido
    
    # Buscar apenas pedidos aprovados ou presenciais confirmados
    pedidos_validos = Q(status_pagamento='approved') | (Q(forma_pagamento='presencial') & Q(status_pagamento='approved'))
    
    # Agrupar por produto e tamanho, somando as quantidades
    vendas = ItemPedido.objects.filter(
        pedido__in=Pedido.objects.filter(pedidos_validos)
    ).values(
        'produto', 'tamanho'
    ).annotate(
        quantidade_vendida=Sum('quantidade'),
        total_pedidos=Count('pedido', distinct=True)
    ).order_by('produto', 'tamanho')
    
    # Calcular totais gerais
    total_geral = 0
    vendas_por_produto = {}
    
    for venda in vendas:
        produto_nome = dict(ItemPedido.PRODUTOS_CHOICES).get(venda['produto'], venda['produto'])
        
        if produto_nome not in vendas_por_produto:
            vendas_por_produto[produto_nome] = {
                'tamanhos': {},
                'total': 0
            }
        
        vendas_por_produto[produto_nome]['tamanhos'][venda['tamanho']] = {
            'quantidade': venda['quantidade_vendida'],
            'pedidos': venda['total_pedidos']
        }
        vendas_por_produto[produto_nome]['total'] += venda['quantidade_vendida']
        total_geral += venda['quantidade_vendida']
    
    # Gerar HTML do relatório
    html_response = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relatório de Vendas - ONEWAY</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                line-height: 1.6;
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}
            
            h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-align: center;
            }}
            
            .data-hora {{
                text-align: center;
                color: #7f8c8d;
                margin-bottom: 30px;
            }}
            
            .resumo {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            
            .resumo h2 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            
            .total-geral {{
                font-size: 3em;
                font-weight: bold;
                color: #27ae60;
                margin: 10px 0;
            }}
            
            .produtos {{
                margin-bottom: 30px;
            }}
            
            .produto-card {{
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }}
            
            .produto-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #f0f0f0;
            }}
            
            .produto-nome {{
                font-size: 1.3em;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            .produto-total {{
                font-size: 1.2em;
                font-weight: bold;
                color: #3498db;
            }}
            
            .tamanhos {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }}
            
            .tamanho-box {{
                background: #f8f9fa;
                padding: 10px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #e9ecef;
            }}
            
            .tamanho-label {{
                font-size: 0.9em;
                color: #6c757d;
                margin-bottom: 5px;
            }}
            
            .tamanho-qtd {{
                font-size: 1.5em;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            .botoes {{
                text-align: center;
                margin-top: 30px;
            }}
            
            .btn {{
                display: inline-block;
                padding: 12px 25px;
                margin: 0 10px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                transition: all 0.3s ease;
                font-weight: 500;
            }}
            
            .btn:hover {{
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            
            .btn.print {{
                background: linear-gradient(135deg, #27ae60, #229954);
            }}
            
            @media print {{
                body {{
                    background: white;
                    padding: 0;
                }}
                .container {{
                    box-shadow: none;
                    padding: 20px;
                }}
                .botoes {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Relatório de Vendas</h1>
            <div class="data-hora">
                {timezone.now().strftime('%d/%m/%Y às %H:%M:%S')}
            </div>
            
            <div class="resumo">
                <h2>Resumo Geral</h2>
                <div class="total-geral">{total_geral}</div>
                <div>Unidades Vendidas</div>
            </div>
            
            <div class="produtos">
    """
    
    # Adicionar cada produto
    for produto_nome, dados in sorted(vendas_por_produto.items()):
        html_response += f"""
                <div class="produto-card">
                    <div class="produto-header">
                        <div class="produto-nome">{produto_nome}</div>
                        <div class="produto-total">Total: {dados['total']} unidades</div>
                    </div>
                    <div class="tamanhos">
        """
        
        # Adicionar tamanhos
        for tamanho in ['P', 'M', 'G', 'GG', 'UNICO']:
            if tamanho in dados['tamanhos']:
                qtd = dados['tamanhos'][tamanho]['quantidade']
                html_response += f"""
                        <div class="tamanho-box">
                            <div class="tamanho-label">Tamanho {tamanho}</div>
                            <div class="tamanho-qtd">{qtd}</div>
                        </div>
                """
        
        html_response += """
                    </div>
                </div>
        """
    
    html_response += """
            </div>
            
            <div class="botoes">
                <a href="#" onclick="window.print(); return false;" class="btn print">🖨️ Imprimir Relatório</a>
                <a href="/api/setup-estoque/" class="btn">⬅️ Voltar ao Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html_response, content_type='text/html')

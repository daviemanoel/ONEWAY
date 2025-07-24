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


from django.http import HttpResponse, JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
import io
import sys

@csrf_exempt
def setup_estoque_view(request):
    """
    Endpoint HTTP para executar setup do sistema de estoque
    Acesse: https://api.oneway.mevamfranca.com.br/api/setup-estoque/
    """
    if request.method != 'GET':
        return HttpResponse('Método não permitido. Use GET.', status=405)
    
    # Capturar output do comando
    output_buffer = io.StringIO()
    
    try:
        # Redirecionar stdout para capturar logs
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        
        # Executar o comando simplificado
        call_command('setup_estoque_simples')
        
        # Restaurar stdout
        sys.stdout = old_stdout
        
        # Pegar o output
        output = output_buffer.getvalue()
        
        # Retornar como HTML formatado
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Setup Sistema de Estoque</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: monospace; background: #1e1e1e; color: #00ff00; padding: 20px; }}
                .success {{ color: #00ff00; }}
                .error {{ color: #ff4444; }}
                .warning {{ color: #ffaa00; }}
                .info {{ color: #4488ff; }}
                pre {{ white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <h1>🚀 Setup Sistema de Estoque - ONEWAY</h1>
            <pre class="success">{output}</pre>
            <hr>
            <p><a href="/admin" target="_blank">🔗 Abrir Django Admin</a></p>
            <p><a href="https://oneway.mevamfranca.com.br" target="_blank">🔗 Abrir Site</a></p>
        </body>
        </html>
        """
        
        return HttpResponse(html_response, content_type='text/html')
        
    except Exception as e:
        # Restaurar stdout em caso de erro
        sys.stdout = old_stdout
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erro - Setup Estoque</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: monospace; background: #1e1e1e; color: #ff4444; padding: 20px; }}
            </style>
        </head>
        <body>
            <h1>❌ Erro no Setup do Sistema de Estoque</h1>
            <pre>{str(e)}</pre>
            <p><a href="javascript:history.back()">⬅️ Voltar</a></p>
        </body>
        </html>
        """
        
        return HttpResponse(error_html, content_type='text/html', status=500)
    
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
                    if produto_tamanho.decrementar_estoque(quantidade):
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

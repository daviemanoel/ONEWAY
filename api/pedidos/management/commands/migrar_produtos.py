from django.core.management.base import BaseCommand
from django.db import transaction
from pedidos.models import Produto, ProdutoTamanho
import json
import os


class Command(BaseCommand):
    help = 'Migra produtos do products.json para os models Django'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a migração sem salvar no banco',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Caminho para o products.json
        json_path = os.path.join(os.path.dirname(__file__), '../../../../web/products.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {json_path}'))
            return
        
        # Carregar dados do JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        produtos_data = data.get('products', {})
        
        if not produtos_data:
            self.stdout.write(self.style.ERROR('Nenhum produto encontrado no JSON'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Encontrados {len(produtos_data)} produtos no JSON'))
        
        # Mapear os produtos para ordem de exibição
        ordem_map = {
            'camiseta-marrom': 1,
            'camiseta-jesus': 2,
            'camiseta-oneway-branca': 3,
            'camiseta-the-way': 4,
        }
        
        produtos_criados = 0
        tamanhos_criados = 0
        produtos_atualizados = 0
        tamanhos_atualizados = 0
        
        try:
            with transaction.atomic():
                for json_key, produto_data in produtos_data.items():
                    self.stdout.write(f"\nProcessando produto: {json_key}")
                    
                    # Preparar dados do produto
                    slug = json_key
                    nome = produto_data.get('title', '')
                    preco = produto_data.get('price', 0)
                    preco_custo = produto_data.get('preco_custo', 0)
                    ordem = ordem_map.get(json_key, 999)
                    
                    # Criar ou atualizar produto
                    produto, criado = Produto.objects.update_or_create(
                        json_key=json_key,
                        defaults={
                            'nome': nome,
                            'slug': slug,
                            'preco': preco,
                            'preco_custo': preco_custo,
                            'ativo': True,
                            'ordem': ordem,
                        }
                    )
                    
                    if criado:
                        produtos_criados += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✅ Produto criado: {nome}"))
                    else:
                        produtos_atualizados += 1
                        self.stdout.write(self.style.WARNING(f"  🔄 Produto atualizado: {nome}"))
                    
                    # Processar tamanhos
                    sizes_data = produto_data.get('sizes', {})
                    
                    for tamanho, tamanho_data in sizes_data.items():
                        estoque = tamanho_data.get('qtda_estoque', 0)
                        disponivel = tamanho_data.get('available', True)
                        
                        # Criar ou atualizar tamanho
                        produto_tamanho, criado = ProdutoTamanho.objects.update_or_create(
                            produto=produto,
                            tamanho=tamanho,
                            defaults={
                                'estoque': estoque,
                                'disponivel': disponivel,
                            }
                        )
                        
                        if criado:
                            tamanhos_criados += 1
                            self.stdout.write(f"    ✅ Tamanho {tamanho}: estoque={estoque}")
                        else:
                            tamanhos_atualizados += 1
                            self.stdout.write(f"    🔄 Tamanho {tamanho}: estoque={estoque}")
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - Nenhuma alteração foi salva'))
                    raise Exception('Dry run - rollback')
        
        except Exception as e:
            if dry_run and str(e) == 'Dry run - rollback':
                pass
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Erro durante migração: {str(e)}'))
                raise
        
        # Resumo final
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('RESUMO DA MIGRAÇÃO:'))
        self.stdout.write(self.style.SUCCESS(f'  Produtos criados: {produtos_criados}'))
        self.stdout.write(self.style.SUCCESS(f'  Produtos atualizados: {produtos_atualizados}'))
        self.stdout.write(self.style.SUCCESS(f'  Tamanhos criados: {tamanhos_criados}'))
        self.stdout.write(self.style.SUCCESS(f'  Tamanhos atualizados: {tamanhos_atualizados}'))
        self.stdout.write(self.style.SUCCESS('='*50))
        
        # Validar integridade
        total_produtos = Produto.objects.count()
        total_tamanhos = ProdutoTamanho.objects.count()
        
        self.stdout.write(f'\nTotal de produtos no banco: {total_produtos}')
        self.stdout.write(f'Total de tamanhos no banco: {total_tamanhos}')
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Migração concluída com sucesso!'))
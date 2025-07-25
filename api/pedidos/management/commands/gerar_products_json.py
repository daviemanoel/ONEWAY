from django.core.management.base import BaseCommand
from pedidos.models import Produto, ProdutoTamanho
import json
import os


class Command(BaseCommand):
    help = 'Gera products.json atualizado com product_size_id para integração frontend'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='products_updated.json',
            help='Nome do arquivo de saída (padrão: products_updated.json)',
        )
    
    def handle(self, *args, **options):
        output_file = options.get('output', 'products_updated.json')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📄 GERAÇÃO DO PRODUCTS.JSON ATUALIZADO'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        try:
            # Mapeamento de imagens corretas
            image_map = {
                'camiseta-marrom': './img/camisetas/camiseta_marrom.jpeg',
                'camiseta-jesus': './img/camisetas/Camiseta_jesus.jpeg',
                'camiseta-oneway-branca': './img/camisetas/Camiseta_onewayBranca.jpeg',
                'camiseta-the-way': './img/camisetas/Camiseta_theway.jpeg',
            }
            
            # Mapeamento de imagens extras (se existirem)
            images_map = {
                'camiseta-marrom': [
                    './img/camisetas/camiseta_marrom.jpeg',
                    './img/camisetas/camiseta_marrom-2.jpeg'
                ]
            }
            
            # Mapeamento de vídeos (se existirem)
            video_map = {
                'camiseta-marrom': './videos/camiseta-marrom-preview.mp4'
            }
            
            # Estrutura base do products.json
            products_data = {"products": {}}
            
            # Buscar todos os produtos ordenados (o método esta_disponivel valida se está ativo)
            produtos = Produto.objects.all().order_by('ordem', 'nome')
            
            if not produtos.exists():
                self.stdout.write(self.style.ERROR('❌ Nenhum produto ativo encontrado'))
                return
            
            self.stdout.write(self.style.NOTICE(f'📦 Processando {produtos.count()} produtos...'))
            
            for produto in produtos:
                self.stdout.write(f'\n  🔄 Processando: {produto.nome}')
                
                # Buscar tamanhos do produto
                tamanhos = produto.tamanhos.all().order_by('tamanho')
                
                if not tamanhos.exists():
                    self.stdout.write(f'    ⚠️  Produto sem tamanhos - pulando')
                    continue
                
                # Construir sizes dict
                sizes = {}
                for tamanho in tamanhos:
                    sizes[tamanho.tamanho] = {
                        "product_size_id": tamanho.id,  # ✨ NOVO CAMPO PRINCIPAL
                        "available": tamanho.esta_disponivel,  # Usa método que valida produto.ativo
                        "qtda_estoque": tamanho.estoque,
                        # Campos legacy preservados
                        "stripe_link": None,
                        "id_stripe": f"prod_{produto.json_key}_{tamanho.tamanho.lower()}"
                    }
                    
                    status_icon = "✅" if tamanho.esta_disponivel else "❌"
                    self.stdout.write(f'    {status_icon} {tamanho.tamanho}: {tamanho.estoque} unidades (ID: {tamanho.id})')
                
                # Construir produto completo
                produto_data = {
                    "id": str(produto.id),  # ID numérico do produto
                    "title": produto.nome,
                    "price": float(produto.preco),
                    "preco_custo": float(produto.preco_custo),
                    "image": image_map.get(produto.json_key, f"./img/camisetas/{produto.json_key}.jpeg"),
                    "sizes": sizes
                }
                
                # Adicionar campos extras se existirem
                if produto.json_key in images_map:
                    produto_data["images"] = images_map[produto.json_key]
                
                if produto.json_key in video_map:
                    produto_data["video"] = video_map[produto.json_key]
                
                products_data["products"][produto.json_key] = produto_data
            
            # Salvar arquivo JSON
            output_content = json.dumps(products_data, indent=2, ensure_ascii=False)
            
            # Tentar salvar no diretório atual (Railway)
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                output_path = os.path.abspath(output_file)
            except:
                # Fallback para /tmp se não conseguir escrever
                output_path = f'/tmp/{output_file}'
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)
            
            # Estatísticas
            total_produtos = len(products_data["products"])
            total_tamanhos = sum(len(p["sizes"]) for p in products_data["products"].values())
            total_estoque = 0
            produtos_disponiveis = 0
            
            for produto_data in products_data["products"].values():
                tem_estoque = False
                for size_data in produto_data["sizes"].values():
                    total_estoque += size_data["qtda_estoque"]
                    if size_data["available"]:
                        tem_estoque = True
                if tem_estoque:
                    produtos_disponiveis += 1
            
            # Resultado final
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('✅ PRODUCTS.JSON GERADO COM SUCESSO!'))
            self.stdout.write(self.style.SUCCESS('='*60))
            
            self.stdout.write(self.style.SUCCESS(f'\n📊 ESTATÍSTICAS:'))
            self.stdout.write(f'   • Produtos processados: {total_produtos}')
            self.stdout.write(f'   • Produtos disponíveis: {produtos_disponiveis}')
            self.stdout.write(f'   • Total de tamanhos: {total_tamanhos}')
            self.stdout.write(f'   • Total de estoque: {total_estoque} unidades')
            
            self.stdout.write(self.style.SUCCESS(f'\n📁 ARQUIVO GERADO:'))
            self.stdout.write(f'   {output_path}')
            
            self.stdout.write(self.style.SUCCESS(f'\n🔑 PRINCIPAIS MUDANÇAS:'))
            self.stdout.write('   • Campo "product_size_id" adicionado em cada tamanho')
            self.stdout.write('   • IDs numéricos do Django para validação de estoque')
            self.stdout.write('   • Estoque em tempo real do banco de dados')
            self.stdout.write('   • Compatibilidade mantida com campos existentes')
            
            self.stdout.write(self.style.SUCCESS('\n💡 PRÓXIMOS PASSOS:'))
            self.stdout.write('   1. Substituir products.json original por este arquivo')
            self.stdout.write('   2. Atualizar server.js para usar product_size_id')
            self.stdout.write('   3. Modificar frontend JavaScript')
            self.stdout.write('   4. Testar integração completa')
            
            self.stdout.write(self.style.SUCCESS('\n' + '='*60 + '\n'))
            
            # Mostrar preview do JSON
            self.stdout.write(self.style.NOTICE('📋 PREVIEW DO ARQUIVO (primeiras linhas):'))
            preview_lines = output_content.split('\n')[:20]
            for line in preview_lines:
                self.stdout.write(f'   {line}')
            
            if len(preview_lines) >= 20:
                self.stdout.write('   ...')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro ao gerar products.json: {str(e)}'))
            raise
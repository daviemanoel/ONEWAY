from django.core.management.base import BaseCommand
from django.db import transaction
from pedidos.models import Produto, ProdutoTamanho, Pedido
from decimal import Decimal


class Command(BaseCommand):
    help = 'Reset completo do estoque - restaura valores originais e permite reprocessamento'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula o reset sem salvar no banco',
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma que deseja executar o reset (obrigatório)',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        confirmar = options.get('confirmar', False)
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('🔄 RESET COMPLETO DO SISTEMA DE ESTOQUE'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
        
        if not confirmar and not dry_run:
            self.stdout.write(
                self.style.ERROR(
                    '⚠️  ATENÇÃO: Esta operação vai RESETAR TODO O ESTOQUE!\n'
                    '   Use --confirmar para executar ou --dry-run para simular.\n'
                    '   Exemplo: python manage.py reset_estoque --confirmar'
                )
            )
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY RUN - Nenhuma alteração será salva\n'))
        
        # Estatísticas iniciais
        pedidos_decrementados = Pedido.objects.filter(estoque_decrementado=True).count()
        produtos_total = Produto.objects.count()
        tamanhos_total = ProdutoTamanho.objects.count()
        
        self.stdout.write(self.style.NOTICE('📊 SITUAÇÃO ATUAL:'))
        self.stdout.write(f'   • Produtos cadastrados: {produtos_total}')
        self.stdout.write(f'   • Tamanhos cadastrados: {tamanhos_total}')
        self.stdout.write(f'   • Pedidos com estoque decrementado: {pedidos_decrementados}')
        
        # Mostrar estoque atual
        self.stdout.write(self.style.NOTICE('\n📦 ESTOQUE ATUAL:'))
        for produto in Produto.objects.filter(ativo=True).order_by('ordem'):
            estoque_total = produto.estoque_total
            self.stdout.write(f'   • {produto.nome}: {estoque_total} unidades')
            for tamanho in produto.tamanhos.all().order_by('tamanho'):
                status = '✅' if tamanho.disponivel and tamanho.estoque > 0 else '❌'
                self.stdout.write(f'     - {tamanho.tamanho}: {tamanho.estoque} {status}')
        
        # Dados do estoque original (mesmos valores do setup_estoque_simples.py)
        estoque_original = {
            'camiseta-marrom': {
                'P': {'estoque': 8, 'disponivel': True},
                'M': {'estoque': 17, 'disponivel': True},
                'G': {'estoque': 17, 'disponivel': True},
                'GG': {'estoque': 8, 'disponivel': True},
            },
            'camiseta-jesus': {
                'P': {'estoque': 5, 'disponivel': True},
                'M': {'estoque': 10, 'disponivel': True},
                'G': {'estoque': 10, 'disponivel': True},
                'GG': {'estoque': 5, 'disponivel': True},
            },
            'camiseta-oneway-branca': {
                'P': {'estoque': 5, 'disponivel': True},
                'M': {'estoque': 10, 'disponivel': True},
                'G': {'estoque': 10, 'disponivel': True},
                'GG': {'estoque': 5, 'disponivel': True},
            },
            'camiseta-the-way': {
                'P': {'estoque': 5, 'disponivel': True},
                'M': {'estoque': 10, 'disponivel': True},
                'G': {'estoque': 10, 'disponivel': True},
                'GG': {'estoque': 5, 'disponivel': True},
            }
        }
        
        try:
            with transaction.atomic():
                self.stdout.write(self.style.SUCCESS(f'\n🔄 INICIANDO RESET...\n'))
                
                # 1. Resetar estoque para valores originais
                self.stdout.write(self.style.NOTICE('📦 Restaurando estoque original...'))
                
                produtos_resetados = 0
                tamanhos_resetados = 0
                
                for produto in Produto.objects.filter(ativo=True):
                    if produto.json_key in estoque_original:
                        estoque_produto = estoque_original[produto.json_key]
                        
                        for tamanho_obj in produto.tamanhos.all():
                            if tamanho_obj.tamanho in estoque_produto:
                                dados_tamanho = estoque_produto[tamanho_obj.tamanho]
                                
                                # Armazenar valores antigos para log
                                estoque_antigo = tamanho_obj.estoque
                                disponivel_antigo = tamanho_obj.disponivel
                                
                                if not dry_run:
                                    tamanho_obj.estoque = dados_tamanho['estoque']
                                    tamanho_obj.disponivel = dados_tamanho['disponivel']
                                    tamanho_obj.save()
                                
                                self.stdout.write(
                                    f'  ✅ {produto.nome} ({tamanho_obj.tamanho}): '
                                    f'{estoque_antigo} → {dados_tamanho["estoque"]}'
                                )
                                tamanhos_resetados += 1
                        
                        produtos_resetados += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠️  Produto {produto.nome} ({produto.json_key}) não encontrado no estoque original'
                            )
                        )
                
                # 2. Marcar todos os pedidos para reprocessamento
                self.stdout.write(self.style.NOTICE('\n🔄 Marcando pedidos para reprocessamento...'))
                
                if not dry_run:
                    pedidos_resetados = Pedido.objects.filter(
                        estoque_decrementado=True
                    ).update(estoque_decrementado=False)
                else:
                    pedidos_resetados = pedidos_decrementados
                
                self.stdout.write(f'  ✅ {pedidos_resetados} pedidos marcados para reprocessamento')
                
                # Rollback se for dry run
                if dry_run:
                    raise Exception('Dry run - rollback')
                
        except Exception as e:
            if dry_run and str(e) == 'Dry run - rollback':
                pass
            else:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ Erro durante reset: {str(e)}')
                )
                raise
        
        # 3. Mostrar estoque após reset
        self.stdout.write(self.style.SUCCESS(f'\n📦 ESTOQUE APÓS RESET:'))
        estoque_total_apos = 0
        for produto in Produto.objects.filter(ativo=True).order_by('ordem'):
            estoque_produto = produto.estoque_total
            estoque_total_apos += estoque_produto
            self.stdout.write(f'   • {produto.nome}: {estoque_produto} unidades')
            for tamanho in produto.tamanhos.all().order_by('tamanho'):
                status = '✅' if tamanho.disponivel and tamanho.estoque > 0 else '❌'
                self.stdout.write(f'     - {tamanho.tamanho}: {tamanho.estoque} {status}')
        
        # 4. Resumo final
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('📋 RESUMO DO RESET:'))
        self.stdout.write(self.style.SUCCESS(f'  ✅ Produtos processados: {produtos_resetados}'))
        self.stdout.write(self.style.SUCCESS(f'  ✅ Tamanhos resetados: {tamanhos_resetados}'))
        self.stdout.write(self.style.SUCCESS(f'  ✅ Pedidos para reprocessar: {pedidos_resetados}'))
        self.stdout.write(self.style.SUCCESS(f'  📦 Estoque total restaurado: {estoque_total_apos} unidades'))
        
        # Próximos passos
        self.stdout.write(self.style.NOTICE(f'\n🚀 PRÓXIMOS PASSOS:'))
        self.stdout.write('  1. Execute: python manage.py sincronizar_estoque --gerar-json')
        self.stdout.write('  2. Isso irá reprocessar todos os pedidos aprovados')
        self.stdout.write('  3. O estoque será decrementado novamente conforme os pedidos')
        
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('✅ Reset concluído com sucesso!'))
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  IMPORTANTE: Execute a sincronização de estoque para reprocessar os pedidos!'
                )
            )
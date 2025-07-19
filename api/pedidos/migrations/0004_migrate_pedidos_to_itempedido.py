# Generated manually to migrate existing pedidos to ItemPedido structure

from django.db import migrations


def migrate_pedidos_to_itempedido(apps, schema_editor):
    """Converte cada pedido existente em um pedido com 1 ItemPedido"""
    Pedido = apps.get_model('pedidos', 'Pedido')
    ItemPedido = apps.get_model('pedidos', 'ItemPedido')
    
    # Para cada pedido existente
    for pedido in Pedido.objects.all():
        # Criar um ItemPedido com os dados do pedido
        ItemPedido.objects.create(
            pedido=pedido,
            produto=pedido.produto,
            tamanho=pedido.tamanho,
            quantidade=1,  # Pedidos antigos sempre tinham quantidade 1
            preco_unitario=pedido.preco
        )
        print(f"Migrado pedido #{pedido.id} - {pedido.produto} ({pedido.tamanho})")


def reverse_migration(apps, schema_editor):
    """Reverter a migração (remover todos os ItemPedido)"""
    ItemPedido = apps.get_model('pedidos', 'ItemPedido')
    ItemPedido.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0003_itempedido'),
    ]

    operations = [
        migrations.RunPython(
            migrate_pedidos_to_itempedido, 
            reverse_migration
        ),
    ]
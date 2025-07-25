# Generated by Django 4.2.16 on 2025-07-24 11:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0005_produto_pedido_estoque_decrementado_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MovimentacaoEstoque",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("entrada", "Entrada"),
                            ("saida", "Saída"),
                            ("ajuste", "Ajuste"),
                            ("reset", "Reset"),
                            ("setup", "Setup Inicial"),
                        ],
                        max_length=20,
                        verbose_name="Tipo de Movimentação",
                    ),
                ),
                (
                    "quantidade",
                    models.IntegerField(
                        help_text="Quantidade movimentada (positiva para entrada, negativa para saída)",
                        verbose_name="Quantidade",
                    ),
                ),
                (
                    "estoque_anterior",
                    models.IntegerField(
                        help_text="Quantidade de estoque antes da movimentação",
                        verbose_name="Estoque Anterior",
                    ),
                ),
                (
                    "estoque_posterior",
                    models.IntegerField(
                        help_text="Quantidade de estoque após a movimentação",
                        verbose_name="Estoque Posterior",
                    ),
                ),
                (
                    "data_movimentacao",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data da Movimentação"
                    ),
                ),
                (
                    "usuario",
                    models.CharField(
                        blank=True,
                        help_text="Usuário ou sistema que executou a movimentação",
                        max_length=100,
                        verbose_name="Usuário",
                    ),
                ),
                (
                    "observacao",
                    models.TextField(
                        blank=True,
                        help_text="Detalhes adicionais sobre a movimentação",
                        verbose_name="Observação",
                    ),
                ),
                (
                    "origem",
                    models.CharField(
                        blank=True,
                        help_text="Sistema/comando que originou a movimentação (ex: pagamento_presencial, sincronizacao)",
                        max_length=50,
                        verbose_name="Origem",
                    ),
                ),
                (
                    "pedido",
                    models.ForeignKey(
                        blank=True,
                        help_text="Pedido que gerou esta movimentação (se aplicável)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="pedidos.pedido",
                        verbose_name="Pedido Relacionado",
                    ),
                ),
                (
                    "produto_tamanho",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="movimentacoes",
                        to="pedidos.produtotamanho",
                        verbose_name="Produto/Tamanho",
                    ),
                ),
            ],
            options={
                "verbose_name": "Movimentação de Estoque",
                "verbose_name_plural": "Movimentações de Estoque",
                "ordering": ["-data_movimentacao"],
                "indexes": [
                    models.Index(
                        fields=["produto_tamanho", "-data_movimentacao"],
                        name="pedidos_mov_produto_334e53_idx",
                    ),
                    models.Index(
                        fields=["tipo", "-data_movimentacao"],
                        name="pedidos_mov_tipo_38f0c2_idx",
                    ),
                    models.Index(
                        fields=["pedido"], name="pedidos_mov_pedido__0e311c_idx"
                    ),
                ],
            },
        ),
    ]

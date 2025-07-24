from django.apps import AppConfig
import os


class PedidosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pedidos"
    
    def ready(self):
        """Executado quando o Django inicializar"""
        # Só executar em produção (Railway)
        if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
            self.setup_estoque_automatico()
    
    def setup_estoque_automatico(self):
        """Setup automático do sistema de estoque no deploy"""
        try:
            from django.core.management import call_command
            import sys
            
            # Evitar execução múltipla durante migrations ou outros comandos
            if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
                print("🚀 Executando setup automático do sistema de estoque...")
                call_command('setup_estoque')
                print("✅ Setup automático concluído!")
        except Exception as e:
            print(f"⚠️  Erro no setup automático: {e}")
            # Não falhar o deploy por causa disso
            pass

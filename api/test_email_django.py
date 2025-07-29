#!/usr/bin/env python3
"""
Teste rápido do sistema de email Django
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/Users/davisilva/projetos/oneway/ONEWAY/api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneway_admin.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def testar_email_django():
    """
    Testa envio de email via Django
    """
    print("🧪 TESTE DE EMAIL DJANGO")
    print("=" * 40)
    
    # Configurações atuais
    print(f"📧 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"🔌 EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"🔒 EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"👤 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"📨 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🔑 EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'NÃO CONFIGURADO'}")
    
    # Verificar se está configurado
    if not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ EMAIL_HOST_PASSWORD não está configurado!")
        print("Configure a variável de ambiente EMAIL_HOST_PASSWORD")
        return False
    
    # Email de teste
    email_destino = input("\n📮 Digite o email de destino para teste: ").strip()
    
    if not email_destino:
        print("❌ Email não fornecido.")
        return False
    
    try:
        print(f"\n📤 Enviando email de teste para: {email_destino}")
        
        # Template de teste
        assunto = "🧪 Teste do Sistema de Email - ONE WAY 2025"
        
        mensagem_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Teste Email - ONE WAY 2025</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f8f9fa; padding: 20px; border: 1px solid #ddd; }}
                .footer {{ background: #343a40; color: white; padding: 15px; text-align: center; border-radius: 0 0 5px 5px; }}
                .success {{ color: #28a745; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 ONE WAY 2025</h1>
                    <p>Teste do Sistema de Email</p>
                </div>
                
                <div class="content">
                    <h2>✅ Sistema Funcionando!</h2>
                    <p>Este é um email de teste para verificar se o sistema de notificações está funcionando corretamente.</p>
                    
                    <h3>📋 Configurações Testadas:</h3>
                    <ul>
                        <li><strong>Servidor SMTP:</strong> {settings.EMAIL_HOST}:{settings.EMAIL_PORT}</li>
                        <li><strong>SSL:</strong> {'Ativo' if settings.EMAIL_USE_SSL else 'Inativo'}</li>
                        <li><strong>Usuário:</strong> {settings.EMAIL_HOST_USER}</li>
                        <li><strong>Django Backend:</strong> Configurado</li>
                    </ul>
                    
                    <p class="success">🎉 Se você está recebendo este email, o sistema está pronto para uso!</p>
                </div>
                
                <div class="footer">
                    <p><strong>Sistema de Notificações - ONE WAY 2025</strong></p>
                    <p>Email enviado em: {__import__('datetime').datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mensagem_texto = f"""
        TESTE DO SISTEMA DE EMAIL - ONE WAY 2025
        
        ✅ Sistema Funcionando!
        
        Este é um email de teste para verificar se o sistema de notificações está funcionando corretamente.
        
        Configurações Testadas:
        - Servidor SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
        - SSL: {'Ativo' if settings.EMAIL_USE_SSL else 'Inativo'}
        - Usuário: {settings.EMAIL_HOST_USER}
        - Django Backend: Configurado
        
        🎉 Se você está recebendo este email, o sistema está pronto para uso!
        
        Sistema de Notificações - ONE WAY 2025
        Email enviado em: {__import__('datetime').datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
        """
        
        # Enviar email
        send_mail(
            subject=assunto,
            message=mensagem_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_destino],
            html_message=mensagem_html,
            fail_silently=False,
        )
        
        print("✅ Email enviado com sucesso!")
        print(f"📬 Verifique a caixa de entrada de: {email_destino}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False

if __name__ == "__main__":
    # Configurar senha via environment ANTES de importar Django
    os.environ['EMAIL_HOST_PASSWORD'] = '!*Oneway25_'  # Usar a senha testada
    
    # Recarregar configurações do Django após definir environment
    from django.conf import settings
    settings._wrapped = None  # Forçar recarga das configurações
    
    # Executar teste
    sucesso = testar_email_django()
    
    if sucesso:
        print("\n🎉 SISTEMA DE EMAIL FUNCIONANDO!")
        print("✅ Agora você pode usar a action no Django Admin")
    else:
        print("\n❌ Sistema precisa de ajustes")
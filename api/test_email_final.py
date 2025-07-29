#!/usr/bin/env python3
"""
Teste final do sistema de email
"""

import os
import sys

# CONFIGURAR SENHA ANTES DE IMPORTAR DJANGO
os.environ['EMAIL_HOST_PASSWORD'] = '!*Oneway25_'

# Configurar path e Django
sys.path.append('/Users/davisilva/projetos/oneway/ONEWAY/api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneway_admin.settings')

import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def main():
    print("🧪 TESTE FINAL DO SISTEMA DE EMAIL")
    print("=" * 40)
    
    print(f"📧 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"🔌 EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"🔒 EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"👤 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"📨 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🔑 EMAIL_HOST_PASSWORD: {'✅ Configurado' if settings.EMAIL_HOST_PASSWORD else '❌ Não configurado'}")
    
    if not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ Senha não carregada!")
        return
    
    # Email de destino para teste (EDITE AQUI)
    email_destino = "oneway@mevamfranca.com.br"  # MUDE PARA SEU EMAIL
    
    print(f"\n📮 Enviando teste para: {email_destino}")
    print("💡 Para mudar o email, edite a linha 41 do arquivo")
    
    if not email_destino:
        print("❌ Email não fornecido.")
        return
    
    try:
        print(f"\n📤 Enviando email de teste para: {email_destino}")
        
        # Email de teste simples
        send_mail(
            subject="🧪 Teste Sistema Email - ONE WAY 2025",
            message="Se você está recebendo este email, o sistema está funcionando! ✅",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_destino],
            html_message="""
            <h2>🧪 Teste Sistema Email - ONE WAY 2025</h2>
            <p><strong>Se você está recebendo este email, o sistema está funcionando!</strong> ✅</p>
            <p>Agora você pode usar a action <strong>"📧 Enviar email de confirmação"</strong> no Django Admin.</p>
            """,
            fail_silently=False,
        )
        
        print("✅ Email enviado com sucesso!")
        print(f"📬 Verifique a caixa de entrada de: {email_destino}")
        print("\n🎉 SISTEMA PRONTO PARA USO!")
        print("✅ Vá para o Django Admin e teste a action 'Enviar email de confirmação'")
        
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        print(f"🔍 Tipo do erro: {type(e).__name__}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script simples para testar SMTP - Edite as credenciais diretamente no código
"""

import smtplib

def teste_smtp_direto():
    """
    EDITE ESTAS VARIÁVEIS COM AS CREDENCIAIS REAIS:
    """
    email = "oneway@mevamfranca.com.br"
    senha = "!*Oneway25_"  # ← EDITAR AQUI
    
    # Se não editou a senha, parar
    if senha == "COLOQUE_A_SENHA_AQUI":
        print("❌ EDITE A SENHA NO ARQUIVO test_smtp_simple.py LINHA 12")
        return
    
    # Configurações para testar (em ordem de preferência)
    configs = [
        ("email-ssl.com.br", 465, "SSL"),
        ("email-ssl.com.br", 587, "TLS"), 
        ("smtplw.com.br", 465, "SSL"),
        ("smtplw.com.br", 587, "TLS"),
    ]
    
    print("🚀 TESTANDO SMTP LOCAWEB...")
    print(f"📧 Email: {email}")
    print("=" * 40)
    
    for servidor, porta, tipo in configs:
        print(f"\n🔍 Testando {servidor}:{porta} ({tipo})...")
        
        try:
            if tipo == "SSL":
                smtp = smtplib.SMTP_SSL(servidor, porta)
            else:
                smtp = smtplib.SMTP(servidor, porta)
                smtp.starttls()
            
            smtp.login(email, senha)
            smtp.quit()
            
            print("✅ FUNCIONOU!")
            print(f"🎉 Use: {servidor}:{porta} com {tipo}")
            print("\n📋 CONFIGURAÇÃO DJANGO:")
            print(f"EMAIL_HOST = '{servidor}'")
            print(f"EMAIL_PORT = {porta}")
            print(f"EMAIL_USE_SSL = {tipo == 'SSL'}")
            print(f"EMAIL_USE_TLS = {tipo == 'TLS'}")
            print(f"EMAIL_HOST_USER = '{email}'")
            print("EMAIL_HOST_PASSWORD = '[SENHA]'")
            return
            
        except smtplib.SMTPAuthenticationError:
            print("❌ Usuário/senha incorretos")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    print("\n❌ Nenhuma configuração funcionou!")
    print("🔍 Verifique senha e configurações da Locaweb")

if __name__ == "__main__":
    teste_smtp_direto()
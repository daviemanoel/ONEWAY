#!/usr/bin/env python3
"""
Script para testar credenciais SMTP da Locaweb
Uso: python test_smtp.py
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def testar_conexao_smtp(servidor, porta, email, senha, usar_ssl=True):
    """
    Testa conexão SMTP com os parâmetros fornecidos
    """
    print(f"\n🔍 Testando: {servidor}:{porta} ({'SSL' if usar_ssl else 'TLS'})")
    print(f"👤 Email: {email}")
    
    try:
        if usar_ssl:
            server = smtplib.SMTP_SSL(servidor, porta)
        else:
            server = smtplib.SMTP(servidor, porta)
            server.starttls()
        
        # Tentar fazer login
        server.login(email, senha)
        
        print("✅ Conexão SMTP funcionando!")
        print(f"📧 Servidor: {servidor}:{porta}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("❌ Erro de autenticação:")
        print(f"🔑 Usuário ou senha incorretos: {e}")
        return False
        
    except smtplib.SMTPServerDisconnected as e:
        print("❌ Servidor desconectou:")
        print(f"🔌 Problema de conexão: {e}")
        return False
        
    except Exception as e:
        print("❌ Erro geral na conexão SMTP:")
        print(f"🔍 Detalhes: {e}")
        return False

def enviar_email_teste(servidor, porta, email, senha, email_destino, usar_ssl=True):
    """
    Envia email de teste se a conexão funcionar
    """
    print(f"\n📧 Tentando enviar email de teste para: {email_destino}")
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email_destino
        msg['Subject'] = "Teste SMTP ONE WAY 2025"
        
        # Corpo do email
        corpo = """
        <h2>🎯 Teste SMTP ONE WAY 2025</h2>
        <p>Este é um email de teste para verificar a configuração SMTP.</p>
        <ul>
            <li><strong>Servidor:</strong> {servidor}:{porta}</li>
            <li><strong>Email:</strong> {email}</li>
            <li><strong>Data:</strong> {data}</li>
        </ul>
        <p>Se você está recebendo este email, a configuração está funcionando! ✅</p>
        """.format(
            servidor=servidor,
            porta=porta, 
            email=email,
            data=__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        )
        
        msg.attach(MIMEText(corpo, 'html', 'utf-8'))
        
        # Conectar e enviar
        if usar_ssl:
            server = smtplib.SMTP_SSL(servidor, porta)
        else:
            server = smtplib.SMTP(servidor, porta)
            server.starttls()
            
        server.login(email, senha)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email de teste enviado com sucesso!")
        return True
        
    except Exception as e:
        print("❌ Erro ao enviar email de teste:")
        print(f"🔍 Detalhes: {e}")
        return False

def main():
    """
    Função principal para testar configurações SMTP da Locaweb
    """
    print("🚀 TESTE DE CONFIGURAÇÃO SMTP - ONE WAY 2025")
    print("=" * 50)
    
    # Configurações para testar
    email = "oneway@mevamfranca.com.br"
    
    # VOCÊ PRECISA INSERIR A SENHA AQUI
    senha = input("🔑 Digite a senha do email oneway@mevamfranca.com.br: ").strip()
    
    if not senha:
        print("❌ Senha não fornecida. Saindo...")
        return
    
    # Servidores Locaweb para testar
    configuracoes = [
        ("email-ssl.com.br", 465, True),   # SSL
        ("email-ssl.com.br", 587, False),  # TLS
        ("smtplw.com.br", 465, True),      # SSL alternativo
        ("smtplw.com.br", 587, False),     # TLS alternativo
    ]
    
    print(f"\n📋 Testando {len(configuracoes)} configurações...")
    
    configuracao_funcionando = None
    
    for servidor, porta, usar_ssl in configuracoes:
        if testar_conexao_smtp(servidor, porta, email, senha, usar_ssl):
            configuracao_funcionando = (servidor, porta, usar_ssl)
            break
        print()  # Linha em branco entre testes
    
    if configuracao_funcionando:
        servidor, porta, usar_ssl = configuracao_funcionando
        
        print("\n" + "=" * 50)
        print("🎉 CONFIGURAÇÃO SMTP ENCONTRADA!")
        print(f"📧 Servidor: {servidor}")
        print(f"🔌 Porta: {porta}")
        print(f"🔒 SSL: {'Sim' if usar_ssl else 'Não (TLS)'}")
        print(f"👤 Email: {email}")
        
        # Perguntar se quer enviar email de teste
        enviar_teste = input("\n📧 Enviar email de teste? (s/N): ").strip().lower()
        
        if enviar_teste in ['s', 'sim', 'y', 'yes']:
            email_destino = input("📮 Email de destino para teste: ").strip()
            if email_destino:
                enviar_email_teste(servidor, porta, email, senha, email_destino, usar_ssl)
        
        print("\n🔧 CONFIGURAÇÃO PARA DJANGO:")
        print(f"EMAIL_HOST = '{servidor}'")
        print(f"EMAIL_PORT = {porta}")
        print(f"EMAIL_USE_SSL = {usar_ssl}")
        print(f"EMAIL_USE_TLS = {not usar_ssl}")
        print(f"EMAIL_HOST_USER = '{email}'")
        print("EMAIL_HOST_PASSWORD = '[SENHA]'")
        
    else:
        print("\n❌ Nenhuma configuração funcionou!")
        print("🔍 Verifique:")
        print("  - Senha do email")
        print("  - Configurações da Locaweb")
        print("  - Conexão com internet")

if __name__ == "__main__":
    main()
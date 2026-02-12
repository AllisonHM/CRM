"""
Script interativo para configurar e testar o email do sistema de recuperação de senha
"""
from flask import Flask
from flask_mail import Mail, Message
import sys

def configurar_email():
    """Configura o email interativamente"""
    print("=" * 70)
    print("🔧 CONFIGURADOR DE EMAIL - CRM")
    print("=" * 70)
    print()
    
    # Escolher provedor
    print("Escolha seu provedor de email:")
    print("1. Gmail")
    print("2. Outlook/Hotmail")
    print("3. Outro (manual)")
    print()
    
    escolha = input("Digite o número (1-3): ").strip()
    
    if escolha == '1':
        print("\n📧 GMAIL SELECIONADO")
        print("\n⚠️  IMPORTANTE: Você precisa criar uma SENHA DE APP!")
        print("1. Acesse: https://myaccount.google.com/security")
        print("2. Ative 'Verificação em duas etapas'")
        print("3. Procure por 'Senhas de app'")
        print("4. Crie uma senha de app para 'Vitriun CRM'")
        print("5. Copie a senha gerada (16 caracteres)\n")
        
        email = input("Digite seu email do Gmail: ").strip()
        senha = input("Digite a SENHA DE APP (não a senha normal): ").strip()
        
        config = {
            'MAIL_SERVER': 'smtp.gmail.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': email,
            'MAIL_PASSWORD': senha,
            'MAIL_DEFAULT_SENDER': email
        }
    
    elif escolha == '2':
        print("\n📧 OUTLOOK/HOTMAIL SELECIONADO")
        email = input("Digite seu email do Outlook/Hotmail: ").strip()
        senha = input("Digite sua senha: ").strip()
        
        config = {
            'MAIL_SERVER': 'smtp.office365.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': email,
            'MAIL_PASSWORD': senha,
            'MAIL_DEFAULT_SENDER': email
        }
    
    else:
        print("\n📧 CONFIGURAÇÃO MANUAL")
        servidor = input("Servidor SMTP (ex: smtp.gmail.com): ").strip()
        porta = input("Porta (ex: 587): ").strip()
        email = input("Email: ").strip()
        senha = input("Senha: ").strip()
        
        config = {
            'MAIL_SERVER': servidor,
            'MAIL_PORT': int(porta),
            'MAIL_USE_TLS': True,
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': email,
            'MAIL_PASSWORD': senha,
            'MAIL_DEFAULT_SENDER': email
        }
    
    return config

def testar_email(config):
    """Testa as configurações de email"""
    print("\n" + "=" * 70)
    print("🧪 TESTANDO CONFIGURAÇÕES DE EMAIL")
    print("=" * 70)
    
    try:
        # Cria app Flask temporário
        app = Flask(__name__)
        app.config.update(config)
        mail = Mail(app)
        
        email_destino = input("\nDigite um email para receber o teste (Enter para usar o mesmo): ").strip()
        if not email_destino:
            email_destino = config['MAIL_USERNAME']
        
        print(f"\n📤 Enviando email de teste para: {email_destino}")
        print("⏳ Aguarde...")
        
        with app.app_context():
            msg = Message(
                subject='🧪 Teste - Vitriun CRM',
                recipients=[email_destino]
            )
            msg.html = """
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #4a90e2;">✅ Configuração de Email Funcionando!</h2>
                    <p>Se você recebeu este email, significa que o sistema de recuperação de senha está configurado corretamente.</p>
                    <p><strong>Próximos passos:</strong></p>
                    <ol>
                        <li>Copie as configurações exibidas no console</li>
                        <li>Cole no arquivo CRM.py (linhas 33-39)</li>
                        <li>Reinicie o servidor Flask</li>
                        <li>Teste o sistema de recuperação de senha</li>
                    </ol>
                    <hr>
                    <p style="color: #999; font-size: 12px;">Vitriun CRM - Email de Teste</p>
                </body>
            </html>
            """
            mail.send(msg)
        
        print("\n✅ EMAIL ENVIADO COM SUCESSO!")
        print(f"📬 Verifique a caixa de entrada de: {email_destino}")
        print("   (Confira também a pasta de SPAM)")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO AO ENVIAR EMAIL:")
        print(f"   {str(e)}")
        print(f"\n   Tipo do erro: {type(e).__name__}")
        
        # Sugestões baseadas no erro
        erro_str = str(e)
        if 'Authentication' in erro_str or 'Username and Password' in erro_str:
            print("\n💡 SUGESTÃO:")
            print("   - Verifique se o email e senha estão corretos")
            if 'gmail' in config['MAIL_SERVER']:
                print("   - Para Gmail, use SENHA DE APP, não a senha normal!")
                print("   - Link: https://myaccount.google.com/security")
        elif 'getaddrinfo' in erro_str or 'Name or service' in erro_str:
            print("\n💡 SUGESTÃO:")
            print("   - Verifique sua conexão com a internet")
            print("   - Confirme se o servidor SMTP está correto")
        elif 'Connection refused' in erro_str:
            print("\n💡 SUGESTÃO:")
            print("   - Verifique se a porta está correta")
            print("   - Tente porta 465 com SSL em vez de 587 com TLS")
            print("   - Verifique seu firewall")
        
        return False

def gerar_codigo_config(config):
    """Gera o código para colar no CRM.py"""
    print("\n" + "=" * 70)
    print("📝 CÓDIGO PARA COLAR NO CRM.py")
    print("=" * 70)
    print("\nProcure por estas linhas no arquivo CRM.py (aproximadamente linha 33-39):")
    print("\n# ------------------- CONFIGURAÇÕES DE EMAIL -------------------")
    print("app.config['MAIL_SERVER'] = 'smtp.gmail.com'")
    print("app.config['MAIL_PORT'] = 587")
    print("...")
    print("\nE substitua por:\n")
    
    print("# ------------------- CONFIGURAÇÕES DE EMAIL -------------------")
    print(f"app.config['MAIL_SERVER'] = '{config['MAIL_SERVER']}'")
    print(f"app.config['MAIL_PORT'] = {config['MAIL_PORT']}")
    print(f"app.config['MAIL_USE_TLS'] = {config['MAIL_USE_TLS']}")
    if config.get('MAIL_USE_SSL'):
        print(f"app.config['MAIL_USE_SSL'] = {config['MAIL_USE_SSL']}")
    print(f"app.config['MAIL_USERNAME'] = '{config['MAIL_USERNAME']}'")
    print(f"app.config['MAIL_PASSWORD'] = '{config['MAIL_PASSWORD']}'")
    print(f"app.config['MAIL_DEFAULT_SENDER'] = '{config['MAIL_DEFAULT_SENDER']}'")
    
    print("\n" + "=" * 70)

def main():
    """Função principal"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "🔧 CONFIGURADOR DE EMAIL - CRM" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Configurar
    config = configurar_email()
    
    # Testar
    if testar_email(config):
        print("\n" + "🎉" * 35)
        gerar_codigo_config(config)
        print("\n✅ CONFIGURAÇÃO CONCLUÍDA!")
        print("\n📋 Próximos passos:")
        print("   1. Copie o código acima")
        print("   2. Cole no arquivo CRM.py")
        print("   3. Reinicie o servidor Flask")
        print("   4. Teste a recuperação de senha em: http://localhost:5000/login")
        return True
    else:
        print("\n❌ Teste falhou. Revise as configurações e tente novamente.")
        print("\n🔄 Quer tentar novamente?")
        retry = input("Digite 's' para sim: ").strip().lower()
        if retry == 's':
            return main()
        return False

if __name__ == '__main__':
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

"""
Script específico para configurar e testar Gmail no sistema de recuperação de senha
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

def testar_conexao_gmail(email, senha):
    """Testa conexão com Gmail passo a passo"""
    print("\n" + "=" * 70)
    print("🔍 DIAGNÓSTICO DE CONEXÃO COM GMAIL")
    print("=" * 70)
    
    # Teste 1: Verificar credenciais
    print("\n1️⃣ Verificando credenciais...")
    if not email or not senha:
        print("   ❌ Email ou senha vazios!")
        return False
    
    if '@gmail.com' not in email.lower():
        print("   ⚠️ Email não parece ser do Gmail!")
        resposta = input("   Continuar mesmo assim? (s/n): ")
        if resposta.lower() != 's':
            return False
    
    if len(senha) != 16 or ' ' in senha:
        print("   ⚠️ A senha de app do Gmail tem exatamente 16 caracteres SEM ESPAÇOS!")
        print("   ⚠️ Você digitou uma senha com", len(senha), "caracteres")
        print("   💡 Copie a senha de app e cole removendo todos os espaços")
    
    print("   ✅ Formato das credenciais OK")
    
    # Teste 2: Conexão SMTP com TLS (porta 587)
    print("\n2️⃣ Testando conexão SMTP (porta 587 com TLS)...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        print("   ✅ Conectado ao servidor Gmail")
        
        print("\n3️⃣ Iniciando TLS...")
        server.starttls()
        print("   ✅ TLS iniciado com sucesso")
        
        print("\n4️⃣ Autenticando...")
        server.login(email, senha)
        print("   ✅ Autenticação bem-sucedida!")
        
        print("\n5️⃣ Enviando email de teste...")
        
        # Criar email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '✅ Teste Vitriun CRM - Gmail OK'
        msg['From'] = email
        msg['To'] = email
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #4CAF50;">✅ Configuração do Gmail Funcionando!</h2>
                <p>Parabéns! Seu Gmail está configurado corretamente.</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Servidor:</strong> smtp.gmail.com:587</p>
                <p><strong>Status:</strong> Conexão e autenticação OK</p>
                <hr>
                <p style="color: #999; font-size: 12px;">Vitriun CRM - Email de Teste</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        server.send_message(msg)
        
        print("   ✅ Email enviado com sucesso!")
        print(f"\n   📬 Verifique a caixa de entrada de: {email}")
        print("      (Pode estar na pasta SPAM na primeira vez)")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ ERRO DE AUTENTICAÇÃO!")
        print(f"   Detalhes: {e}")
        print("\n   🔧 SOLUÇÕES:")
        print("   1. Certifique-se de usar SENHA DE APP, não sua senha normal")
        print("   2. Verifique se a senha está correta (copie sem espaços)")
        print("   3. Confirme que a verificação em 2 etapas está ativa")
        print("   4. Link para criar: https://myaccount.google.com/apppasswords")
        return False
        
    except smtplib.SMTPException as e:
        print(f"   ❌ ERRO SMTP: {e}")
        return False
        
    except ConnectionRefusedError:
        print("   ❌ Conexão recusada!")
        print("   🔧 Verifique seu firewall ou tente porta 465 (SSL)")
        return False
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        print(f"   Tipo: {type(e).__name__}")
        return False

def testar_conexao_ssl_gmail(email, senha):
    """Tenta conexão alternativa com SSL (porta 465)"""
    print("\n" + "=" * 70)
    print("🔍 TESTE ALTERNATIVO: SSL na porta 465")
    print("=" * 70)
    
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=10)
        print("   ✅ Conectado via SSL")
        
        server.login(email, senha)
        print("   ✅ Autenticação bem-sucedida via SSL!")
        
        # Criar email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '✅ Teste Vitriun CRM - Gmail SSL OK'
        msg['From'] = email
        msg['To'] = email
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #4CAF50;">✅ Gmail SSL Funcionando!</h2>
                <p>Sua configuração funcionou com SSL (porta 465).</p>
                <p><strong>Use esta configuração no CRM.py:</strong></p>
                <pre>
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = '{email}'
app.config['MAIL_PASSWORD'] = 'sua_senha_app'
                </pre>
                <hr>
                <p style="color: #999; font-size: 12px;">Vitriun CRM - Email de Teste</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        server.send_message(msg)
        
        print("   ✅ Email enviado via SSL!")
        print(f"\n   📬 Verifique: {email}")
        
        server.quit()
        return True, 465
        
    except Exception as e:
        print(f"   ❌ Falhou: {e}")
        return False, None

def main():
    """Função principal"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "📧 CONFIGURADOR GMAIL - VITRIUN CRM" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    print("⚠️  IMPORTANTE: Configure um EMAIL DEDICADO para o Vitriun CRM!")
    print()
    print("🎯 RECOMENDAÇÕES:")
    print("   Opção 1: Crie um Gmail NOVO para o CRM")
    print("            Exemplo: vitriuncrm@gmail.com ou noreply@seudominio.com")
    print()
    print("   Opção 2: Use um serviço profissional (RECOMENDADO)")
    print("            - SendGrid: 100 emails/dia grátis")
    print("            - Mailgun: Confiável e profissional")
    print()
    print("📝 Se for usar Gmail, crie uma SENHA DE APP:")
    print("   1. Crie/use uma conta Gmail SEPARADA (não sua pessoal)")
    print("   2. Acesse: https://myaccount.google.com/security")
    print("   3. Ative 'Verificação em duas etapas'")
    print("   4. Procure 'Senhas de app'")
    print("   5. Selecione 'Outro' → Digite: Vitriun CRM")
    print("   6. COPIE a senha gerada (16 caracteres)")
    print()
    print("🔗 Link: https://myaccount.google.com/apppasswords")
    print()
    print("⚠️  NUNCA use seu email pessoal! Crie um email específico para o CRM.")
    print()
    
    input("Pressione ENTER quando tiver a senha de app pronta...")
    print()
    
    email = input("📧 Digite seu email do Gmail: ").strip()
    print()
    print("🔑 Digite a senha de app (COLE aqui - 16 caracteres):")
    print("   💡 Dica: Remova todos os espaços da senha!")
    senha = input("   Senha: ").strip().replace(' ', '')
    
    # Teste com TLS (padrão)
    sucesso_tls = testar_conexao_gmail(email, senha)
    
    if not sucesso_tls:
        print("\n" + "🔄" * 35)
        print("\n💡 A porta 587 não funcionou. Vamos tentar a porta 465 com SSL...")
        input("Pressione ENTER para continuar...")
        
        sucesso_ssl, porta = testar_conexao_ssl_gmail(email, senha)
        
        if sucesso_ssl:
            print("\n" + "🎉" * 35)
            print("\n✅ CONFIGURAÇÃO FUNCIONOU COM SSL!")
            print("\n📝 Cole este código no CRM.py (linhas 33-39):\n")
            print("# ------------------- CONFIGURAÇÕES DE EMAIL -------------------")
            print(f"app.config['MAIL_SERVER'] = 'smtp.gmail.com'")
            print(f"app.config['MAIL_PORT'] = 465")
            print(f"app.config['MAIL_USE_TLS'] = False")
            print(f"app.config['MAIL_USE_SSL'] = True")
            print(f"app.config['MAIL_USERNAME'] = '{email}'")
            print(f"app.config['MAIL_PASSWORD'] = '{senha}'")
            print(f"app.config['MAIL_DEFAULT_SENDER'] = '{email}'")
            return True
    else:
        print("\n" + "🎉" * 35)
        print("\n✅ CONFIGURAÇÃO FUNCIONOU COM TLS!")
        print("\n📝 Cole este código no CRM.py (linhas 33-39):\n")
        print("# ------------------- CONFIGURAÇÕES DE EMAIL -------------------")
        print(f"app.config['MAIL_SERVER'] = 'smtp.gmail.com'")
        print(f"app.config['MAIL_PORT'] = 587")
        print(f"app.config['MAIL_USE_TLS'] = True")
        print(f"app.config['MAIL_USERNAME'] = '{email}'")
        print(f"app.config['MAIL_PASSWORD'] = '{senha}'")
        print(f"app.config['MAIL_DEFAULT_SENDER'] = '{email}'")
        return True
    
    print("\n" + "=" * 70)
    print("❌ NENHUMA CONFIGURAÇÃO FUNCIONOU")
    print("=" * 70)
    print("\n🔧 Checklist:")
    print("   ☐ Verificação em 2 etapas está ATIVA?")
    print("   ☐ Você criou uma senha de APP (não usou sua senha normal)?")
    print("   ☐ A senha tem 16 caracteres sem espaços?")
    print("   ☐ Sua internet está funcionando?")
    print("   ☐ Seu firewall está bloqueando Python?")
    print()
    print("🔄 Quer tentar novamente?")
    retry = input("Digite 's' para sim: ").strip().lower()
    if retry == 's':
        return main()
    
    return False

if __name__ == '__main__':
    try:
        sucesso = main()
        if sucesso:
            print("\n" + "=" * 70)
            print("📋 PRÓXIMOS PASSOS:")
            print("=" * 70)
            print("1. Copie o código acima")
            print("2. Cole no arquivo CRM.py (substitua as linhas 33-39)")
            print("3. Salve o arquivo")
            print("4. Reinicie o servidor Flask")
            print("5. Teste em: http://localhost:5000/login → 'Esqueci minha senha'")
            print("=" * 70)
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelado.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

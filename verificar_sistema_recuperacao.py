"""
Script de teste para verificar se o sistema de recuperação de senha
está configurado corretamente
"""
import sys
import os

def verificar_instalacao():
    """Verifica se todas as dependências estão instaladas"""
    print("=" * 70)
    print("VERIFICAÇÃO DO SISTEMA DE RECUPERAÇÃO DE SENHA")
    print("=" * 70 + "\n")
    
    erros = []
    avisos = []
    sucesso = []
    
    # 1. Verificar Flask-Mail
    try:
        from flask_mail import Mail, Message
        sucesso.append("✅ Flask-Mail instalado")
    except ImportError:
        erros.append("❌ Flask-Mail não está instalado. Execute: pip install Flask-Mail")
    
    # 2. Verificar models.py
    try:
        from models import UsuarioCRM
        from sqlalchemy import inspect
        
        # Simula a verificação dos campos (sem conectar ao banco)
        sucesso.append("✅ Modelo UsuarioCRM carregado")
    except Exception as e:
        erros.append(f"❌ Erro ao carregar models.py: {e}")
    
    # 3. Verificar templates
    templates_esperados = [
        'templates/login.html',
        'templates/esqueci_senha.html',
        'templates/resetar_senha.html'
    ]
    
    for template in templates_esperados:
        if os.path.exists(template):
            sucesso.append(f"✅ Template encontrado: {template}")
        else:
            erros.append(f"❌ Template não encontrado: {template}")
    
    # 4. Verificar configurações no CRM.py
    try:
        with open('CRM.py', 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
            if 'from flask_mail import Mail, Message' in conteudo:
                sucesso.append("✅ Import do Flask-Mail no CRM.py")
            else:
                erros.append("❌ Import do Flask-Mail não encontrado no CRM.py")
            
            if 'MAIL_SERVER' in conteudo:
                sucesso.append("✅ Configurações de email no CRM.py")
                
                if 'seu_email@gmail.com' in conteudo:
                    avisos.append("⚠️  Você ainda precisa configurar suas credenciais de email!")
            else:
                erros.append("❌ Configurações de email não encontradas no CRM.py")
            
            if 'def enviar_email_recuperacao' in conteudo:
                sucesso.append("✅ Função enviar_email_recuperacao() criada")
            else:
                erros.append("❌ Função enviar_email_recuperacao() não encontrada")
            
            if '@app.route(\'/esqueci-senha\'' in conteudo:
                sucesso.append("✅ Rota /esqueci-senha criada")
            else:
                erros.append("❌ Rota /esqueci-senha não encontrada")
            
            if '@app.route(\'/resetar-senha/<token>\'' in conteudo:
                sucesso.append("✅ Rota /resetar-senha/<token> criada")
            else:
                erros.append("❌ Rota /resetar-senha/<token> não encontrada")
    
    except Exception as e:
        erros.append(f"❌ Erro ao verificar CRM.py: {e}")
    
    # 5. Verificar banco de dados
    try:
        import psycopg2
        conn = psycopg2.connect(
            database='crm',
            user='postgres',
            password='Amovoce123@',
            host='localhost',
            port=1222
        )
        cur = conn.cursor()
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuario_crm' 
            AND column_name IN ('reset_token', 'reset_token_expira');
        """)
        
        colunas = [row[0] for row in cur.fetchall()]
        
        if 'reset_token' in colunas:
            sucesso.append("✅ Coluna reset_token criada no banco")
        else:
            erros.append("❌ Coluna reset_token não encontrada no banco")
        
        if 'reset_token_expira' in colunas:
            sucesso.append("✅ Coluna reset_token_expira criada no banco")
        else:
            erros.append("❌ Coluna reset_token_expira não encontrada no banco")
        
        conn.close()
    except Exception as e:
        avisos.append(f"⚠️  Não foi possível verificar o banco de dados: {e}")
    
    # Exibir resultados
    print("\n📊 RESUMO DA VERIFICAÇÃO:\n")
    
    if sucesso:
        print("✅ SUCESSOS:")
        for item in sucesso:
            print(f"   {item}")
    
    if avisos:
        print("\n⚠️  AVISOS:")
        for item in avisos:
            print(f"   {item}")
    
    if erros:
        print("\n❌ ERROS:")
        for item in erros:
            print(f"   {item}")
    
    # Status final
    print("\n" + "=" * 70)
    if erros:
        print("❌ VERIFICAÇÃO FALHOU - Corrija os erros acima")
        print("=" * 70)
        return False
    elif avisos:
        print("⚠️  VERIFICAÇÃO PARCIAL - Confira os avisos acima")
        print("=" * 70)
        print("\n📝 PRÓXIMOS PASSOS:")
        print("   1. Configure suas credenciais de email no CRM.py")
        print("   2. Reinicie o servidor Flask")
        print("   3. Teste o sistema de recuperação de senha")
        return True
    else:
        print("✅ VERIFICAÇÃO COMPLETA - Sistema pronto!")
        print("=" * 70)
        return True

if __name__ == '__main__':
    try:
        resultado = verificar_instalacao()
        sys.exit(0 if resultado else 1)
    except Exception as e:
        print(f"\n❌ Erro durante verificação: {e}")
        sys.exit(1)

"""
Script para limpar mensagens duplicadas no banco de dados
Normaliza todos os números de telefone nas mensagens existentes
"""
import psycopg2
import re

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'port': 1222,
    'database': 'crm',
    'user': 'postgres',
    'password': 'Amovoce123@'
}

def normalize_phone(phone):
    """
    Normaliza número removendo caracteres não-numéricos.
    Para números brasileiros com celular, garante 13 dígitos (com 9 extra).
    Formato: 55 (país) + DD (DDD) + 9XXXXXXXX (celular)
    """
    if not phone:
        return ''
    
    numero = re.sub(r'\D', '', str(phone))
    
    # Se é número brasileiro (começa com 55) e tem 12 dígitos
    if numero.startswith('55') and len(numero) == 12:
        # Primeiro dígito do celular (após o DDD)
        primeiro_digito_celular = numero[4] if len(numero) > 4 else ''
        
        # Se começa com 9, adiciona OUTRO 9 (padrão atual é 99...)
        # Números de celular no Brasil têm 9 dígitos: 9XXXX-XXXX
        if primeiro_digito_celular == '9':
            numero = numero[:4] + '9' + numero[4:]
            print(f"    🔧 Ajustado de 12 para 13 dígitos: {numero}")
    
    return numero

def limpar_duplicatas():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔍 Buscando todas as mensagens...")
        
        # Buscar todas as mensagens
        cursor.execute("SELECT id, numero FROM whatsapp_mensagem ORDER BY recebido_em DESC")
        mensagens = cursor.fetchall()
        
        print(f"📊 Total de mensagens: {len(mensagens)}")
        
        # Normalizar números
        atualizadas = 0
        for msg_id, numero in mensagens:
            print(f"  📱 Original: '{numero}' (len={len(numero)})")
            numero_norm = normalize_phone(numero)
            print(f"  ✅ Normalizado: '{numero_norm}' (len={len(numero_norm)})")
            if numero != numero_norm:
                cursor.execute(
                    "UPDATE whatsapp_mensagem SET numero = %s WHERE id = %s",
                    (numero_norm, msg_id)
                )
                atualizadas += 1
                print(f"  💾 Atualizado!")
            print()
        
        conn.commit()
        print(f"✅ {atualizadas} números normalizados!")
        
        # Mostrar estatísticas de conversas únicas
        cursor.execute("""
            SELECT numero, COUNT(*) as total 
            FROM whatsapp_mensagem 
            GROUP BY numero 
            HAVING COUNT(*) > 1 
            ORDER BY total DESC
        """)
        
        duplicatas = cursor.fetchall()
        
        if duplicatas:
            print(f"\n📋 Números com múltiplas mensagens (conversas):")
            for numero, total in duplicatas[:10]:
                print(f"  - {numero}: {total} mensagens")
        
        cursor.execute("SELECT COUNT(DISTINCT numero) FROM whatsapp_mensagem")
        total_conversas = cursor.fetchone()[0]
        print(f"\n✅ Total de conversas únicas: {total_conversas}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    limpar_duplicatas()

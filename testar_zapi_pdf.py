"""
Script para testar envio de PDF direto via Z-API
"""
import requests
import base64
import sys
import os

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from CRM import app
from models import UsuarioCRM

def testar_envio_pdf():
    """Testa envio de PDF via Z-API"""
    
    print("\n" + "="*60)
    print("📤 TESTE DE ENVIO DE PDF VIA Z-API")
    print("="*60)
    
    # Pegar credenciais do usuário
    with app.app_context():
        usuario = UsuarioCRM.query.filter_by(email='allisonhaut@gmail.com').first()
        
        if not usuario or not usuario.api_instance or not usuario.api_token:
            print("❌ Erro: Usuário não encontrado ou sem credenciais Z-API")
            return
        
        print(f"✅ Usuário: {usuario.nome}")
        print(f"✅ Instance: {usuario.api_instance[:15]}...")
        print(f"✅ Token: {usuario.api_token[:15]}...")
    
    # Criar um PDF de teste simples
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Teste de PDF) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000262 00000 n\n0000000341 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n435\n%%EOF"
    
    pdf_b64 = base64.b64encode(pdf_content).decode('utf-8')
    
    print(f"\n📄 PDF criado ({len(pdf_content)} bytes)")
    print(f"📦 Base64 ({len(pdf_b64)} chars)")
    
    # Número de teste (AJUSTE AQUI PARA SEU NÚMERO)
    numero_teste = input("\n📞 Digite o número para teste (formato: 5547999999999): ").strip()
    
    if not numero_teste:
        print("❌ Número não fornecido")
        return
    
    # Preparar payload - Z-API usa send-file-base64 para documentos
    url = f"https://api.z-api.io/instances/{usuario.api_instance}/token/{usuario.api_token}/send-file-base64"
    
    payload = {
        "phone": numero_teste,
        "base64": pdf_b64,
        "fileName": "teste_zapi.pdf",
        "caption": "Teste de PDF"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"\n🌐 URL: {url[:80]}...")
    print(f"📋 Payload keys: {list(payload.keys())}")
    print(f"📱 Número destino: {numero_teste}")
    print(f"📏 Tamanho base64: {len(pdf_b64)} chars")
    print(f"🔢 Primeiros 50 chars: {pdf_b64[:50]}")
    print(f"\n📤 Enviando requisição...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\n📥 Status Code: {response.status_code}")
        print(f"📦 Resposta completa:")
        print(response.text)
        print("=" * 60)
        
        # Tentar parsear JSON
        try:
            resp_json = response.json()
            print(f"\n📋 JSON parseado:")
            for key, value in resp_json.items():
                print(f"   {key}: {value}")
                
            # Verificar se tem erro mesmo com status 200
            if 'error' in resp_json:
                print(f"\n⚠️ ATENÇÃO: Resposta contém erro!")
                print(f"   Erro: {resp_json.get('error')}")
            elif resp_json.get('success') == False:
                print(f"\n⚠️ ATENÇÃO: success = False")
            elif response.status_code == 200:
                print("\n✅ SUCESSO! Verifique seu WhatsApp.")
                if 'messageId' in resp_json:
                    print(f"📱 MessageID: {resp_json['messageId']}")
        except:
            if response.status_code == 200:
                print("\n✅ SUCESSO (não foi possível parsear JSON)")
            else:
                print("\n❌ ERRO e não foi possível parsear JSON")
        
        if response.status_code != 200:
            print("\n❌ ERRO no envio!")
            
    except Exception as e:
        print(f"\n❌ EXCEÇÃO: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    testar_envio_pdf()

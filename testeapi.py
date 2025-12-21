import requests

# Suas credenciais
instance = "3E70C9784E1060A6F423AE9094E04006"
token = "E4E83715DE9F517EFB9A28CA"
client_token = "Fc5c052a80080460b823a2e506d4d6167S"

# URL da API
url = f"https://api.z-api.io/instances/{instance}/token/{token}/send-text"

# Headers com client-token
headers = {
    'client-token': client_token,
    'Content-Type': 'application/json'
}

# Dados da mensagem
data = {
    "phone": "5547999471874",  # Número que vai receber a mensagem
    "message": "Teste Z-API"
}

# Fazendo a requisição
response = requests.post(url, json=data, headers=headers)
print(f"Status code: {response.status_code}")
print(f"Resposta da API: {response.text}")

import requests

s = requests.Session()
s.post('http://127.0.0.1:5000/login', data={'email': 'allisonhaut@gmail.com', 'senha': 'Amovoce123@'}, allow_redirects=True)

r = s.get('http://127.0.0.1:5000/canais/contato/foto?phone=5547999471874')
print('foto status:', r.status_code, 'body:', r.text[:200])

r2 = s.post('http://127.0.0.1:5000/canais/conversa/5547999471874/marcar_lida')
print('marcar_lida status:', r2.status_code, 'body:', r2.text[:200])
# tasks.py
from celery import Celery
import requests
import os

celery = Celery('tasks', broker=os.getenv('REDIS_URL'))

instance = "3E70C9784E1060A6F423AE9094E04006"
token = "E4E83715DE9F517EFB9A28CA"
client_token = "Fc5c052a80080460b823a2e506d4d6167S"

# Headers com client-token
headers = {
    'client-token': client_token,
    'Content-Type': 'application/json'
}

ZAPI_URL = os.getenv('https://api.z-api.io/instances/{instance}/token/{token}/send-text')  # endpoint Z-API
ZAPI_TOKEN = os.getenv('E4E83715DE9F517EFB9A28CA')

@celery.task(bind=True, max_retries=3)
def enviar_whatsapp(self, empresa_id, numero, texto):
    try:
        payload = {"number": numero, "message": texto}
        headers = {"Authorization": f"Bearer {ZAPI_TOKEN}", "Content-Type": "application/json"}
        r = requests.post(ZAPI_URL + "/sendMessage", json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise self.retry(exc=e, countdown=10)

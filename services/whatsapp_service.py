"""
WhatsApp Service - Lógica de negócio do WhatsApp e Z-API
"""
from typing import Optional, Dict, Any, Tuple
import requests
import os
from datetime import datetime

from models import WhatsAppMensagem, UsuarioCRM
from database_rls import db
from utils.exceptions import ExternalAPIError, DatabaseError, safe_commit
from utils.logger import setup_logger, log_api_call, mask_sensitive_data
from config.constants import DEFAULT_DELAY_SECONDS, MIN_DELAY_SECONDS, MAX_DELAY_SECONDS

logger = setup_logger(__name__)


class WhatsAppService:
    """Service para integração com Z-API"""
    
    @staticmethod
    def enviar_mensagem_texto(
        numero: str,
        mensagem: str,
        usuario_crm: UsuarioCRM,
        delay_message: Optional[float] = None,
        delay_typing: Optional[float] = None,
        edit_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto via Z-API
        
        Args:
            numero: Telefone destino (apenas dígitos)
            mensagem: Texto da mensagem
            usuario_crm: Usuário CRM com credenciais
            delay_message: Delay antes da próxima mensagem (1-15s)
            delay_typing: Segundos exibindo "Digitando..."
            edit_message_id: ID da mensagem para editar
        
        Returns:
            Dicionário com resposta da API
        
        Raises:
            ExternalAPIError: Se falha na comunicação
        """
        # Validar credenciais
        if not usuario_crm.api_instance or not usuario_crm.api_token:
            logger.error(f"Usuário {usuario_crm.id} sem credenciais Z-API configuradas")
            return {
                "status": "Erro",
                "detalhe": "Credenciais Z-API não configuradas. Configure em Configurações."
            }
        
        # Validar delays
        if delay_message:
            delay_message = max(MIN_DELAY_SECONDS, min(delay_message, MAX_DELAY_SECONDS))
        if delay_typing:
            delay_typing = max(MIN_DELAY_SECONDS, min(delay_typing, MAX_DELAY_SECONDS))
        
        # Preparar payload
        payload = {
            "phone": numero,
            "message": mensagem
        }
        
        if delay_message:
            payload["delayMessage"] = int(delay_message)
        if delay_typing:
            payload["delayTyping"] = int(delay_typing)
        if edit_message_id:
            payload["messageId"] = edit_message_id
        
        # Endpoint
        endpoint = "edit-text" if edit_message_id else "send-text"
        url = f"https://api.z-api.io/instances/{usuario_crm.api_instance}/token/{usuario_crm.api_token}/{endpoint}"
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        if usuario_crm.api_client_token:
            headers['client-token'] = usuario_crm.api_client_token
        
        # Fazer chamada
        try:
            logger.info(f"Enviando mensagem Z-API para {mask_sensitive_data(numero)}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response_data = response.json()
            
            # Log da resposta
            log_api_call(logger, "Z-API", endpoint, response_data)
            
            if response.status_code == 200:
                return {
                    "status": "Sucesso",
                    "detalhe": response.text
                }
            else:
                logger.warning(f"Z-API retornou erro: {response.status_code} - {response.text}")
                return {
                    "status": "Erro",
                    "detalhe": response.text
                }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout ao enviar mensagem Z-API")
            raise ExternalAPIError("Z-API", "Timeout na requisição", 504)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem Z-API: {str(e)}")
            raise ExternalAPIError("Z-API", f"Erro de comunicação: {str(e)}", 503)
        
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem: {str(e)}")
            raise ExternalAPIError("Z-API", f"Erro inesperado: {str(e)}", 500)
    
    @staticmethod
    def enviar_arquivo_url(
        numero: str,
        file_url: str,
        filename: str,
        usuario_crm: UsuarioCRM,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia arquivo via URL usando Z-API
        
        Args:
            numero: Telefone destino
            file_url: URL pública do arquivo
            filename: Nome do arquivo
            usuario_crm: Usuário com credenciais
            caption: Legenda opcional
        
        Returns:
            Resposta da API
        """
        if not usuario_crm.api_instance or not usuario_crm.api_token:
            return {
                "status": "Erro",
                "detalhe": "Credenciais Z-API não configuradas"
            }
        
        # Verificar se URL é localhost
        if 'localhost' in file_url or '127.0.0.1' in file_url:
            logger.warning(f"Tentativa de enviar arquivo localhost: {file_url}")
            return {
                "status": "Erro",
                "detalhe": "Z-API não pode acessar URLs localhost. Use ngrok ou hospede em servidor público."
            }
        
        payload = {
            "phone": numero,
            "url": file_url,
            "fileName": filename
        }
        
        if caption:
            payload["caption"] = caption
        
        url = f"https://api.z-api.io/instances/{usuario_crm.api_instance}/token/{usuario_crm.api_token}/send-link-file"
        
        headers = {'Content-Type': 'application/json'}
        if usuario_crm.api_client_token:
            headers['client-token'] = usuario_crm.api_client_token
        
        try:
            logger.info(f"Enviando arquivo via URL Z-API: {filename}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            log_api_call(logger, "Z-API", "send-link-file", response_data)
            
            if response.status_code == 200:
                return {"status": "Sucesso", "detalhe": response.text}
            else:
                return {"status": "Erro", "detalhe": response.text}
                
        except Exception as e:
            logger.error(f"Erro ao enviar arquivo: {str(e)}")
            raise ExternalAPIError("Z-API", str(e))
    
    @staticmethod
    def salvar_mensagem_db(
        usuario_crm_id: int,
        numero: str,
        texto: str,
        remetente: str,
        zapi_message_id: Optional[str] = None
    ) -> WhatsAppMensagem:
        """
        Salva mensagem no banco de dados
        
        Args:
            usuario_crm_id: ID do usuário
            numero: Número do WhatsApp
            texto: Texto da mensagem
            remetente: 'Cliente' ou 'Empresa'
            zapi_message_id: ID da mensagem no Z-API
        
        Returns:
            Mensagem salva
        """
        mensagem = WhatsAppMensagem(
            usuario_crm_id=usuario_crm_id,
            numero=numero,
            texto=texto,
            remetente=remetente,
            recebido_em=datetime.utcnow(),
            zapi_message_id=zapi_message_id
        )
        
        try:
            with safe_commit(db.session, "salvar mensagem WhatsApp"):
                db.session.add(mensagem)
            
            logger.info(f"Mensagem WhatsApp salva: {mask_sensitive_data(numero)}")
            
            return mensagem
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {str(e)}")
            raise
    
    @staticmethod
    def configurar_webhook(
        usuario_crm: UsuarioCRM,
        public_url: str
    ) -> Dict[str, Any]:
        """
        Configura webhooks do Z-API
        
        Args:
            usuario_crm: Usuário com credenciais
            public_url: URL pública do webhook
        
        Returns:
            Resultado da configuração
        """
        if not usuario_crm.api_instance or not usuario_crm.api_token:
            raise ExternalAPIError("Z-API", "Credenciais não configuradas")
        
        base_url = f"https://api.z-api.io/instances/{usuario_crm.api_instance}/token/{usuario_crm.api_token}"
        
        headers = {'Content-Type': 'application/json'}
        if usuario_crm.api_client_token:
            headers['client-token'] = usuario_crm.api_client_token
        
        webhook_received_url = f"{public_url}/canais/webhook/received"
        webhook_delivery_url = f"{public_url}/canais/webhook/delivery"
        
        try:
            # Configurar webhook de mensagens recebidas
            resp_recv = requests.put(
                f"{base_url}/update-webhook-received",
                json={"value": webhook_received_url},
                headers=headers,
                timeout=10
            )
            
            # Configurar webhook de delivery
            resp_deliv = requests.put(
                f"{base_url}/update-webhook-delivery",
                json={"value": webhook_delivery_url},
                headers=headers,
                timeout=10
            )
            
            if resp_recv.status_code == 200 and resp_deliv.status_code == 200:
                logger.info("Webhooks Z-API configurados com sucesso")
                return {
                    "status": "ok",
                    "webhook_received": webhook_received_url,
                    "webhook_delivery": webhook_delivery_url
                }
            else:
                erros = []
                if resp_recv.status_code != 200:
                    erros.append(f"received: {resp_recv.status_code}")
                if resp_deliv.status_code != 200:
                    erros.append(f"delivery: {resp_deliv.status_code}")
                
                raise ExternalAPIError("Z-API", " | ".join(erros))
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao configurar webhooks: {str(e)}")
            raise ExternalAPIError("Z-API", str(e))

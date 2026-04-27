"""
Mesa Service - Lógica de negócio de mesas de negócio
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, time
from sqlalchemy.orm import joinedload

from models import MesaNegocio, Cliente
from database_rls import db
from utils.validators import validate_mesa_data, ValidationError
from utils.exceptions import DatabaseError, ResourceNotFoundError, safe_commit
from utils.logger import setup_logger, log_database_operation

logger = setup_logger(__name__)


class MesaService:
    """Service para operações de mesa de negócio"""
    
    @staticmethod
    def criar_mesa(data: Dict[str, Any], cliente_id: int, usuario_crm_id: int) -> MesaNegocio:
        """
        Cria nova mesa de negócio
        
        Args:
            data: Dados da mesa
            cliente_id: ID do cliente
            usuario_crm_id: ID do usuário CRM
        
        Returns:
            Mesa criada
        """
        # Validar dados
        validated_data = validate_mesa_data(data)
        
        # Verificar se cliente existe
        from services.cliente_service import ClienteService
        cliente = ClienteService.get_cliente_por_id(cliente_id, usuario_crm_id)
        
        # Calcular próximo número da mesa
        proximo_numero = MesaService._get_proximo_numero(usuario_crm_id)
        
        # Criar mesa
        agora = datetime.now()
        mesa = MesaNegocio(
            usuario_crm_id=usuario_crm_id,
            cliente_id=cliente_id,
            numero=proximo_numero,
            data_registro=agora.date(),
            hora_registro=agora.time(),
            **validated_data
        )
        
        # Processar produtos_quantidades se fornecido
        if 'produtos_quantidades' in data:
            import json
            try:
                mesa.produtos_quantidades = json.loads(data['produtos_quantidades']) if isinstance(data['produtos_quantidades'], str) else data['produtos_quantidades']
            except:
                mesa.produtos_quantidades = {}
        
        # Salvar
        try:
            with safe_commit(db.session, "criar mesa"):
                db.session.add(mesa)
            
            log_database_operation(logger, "CREATE", "MesaNegocio", mesa.id)
            logger.info(f"Mesa criada: #{mesa.numero} - Cliente: {cliente.nome}")
            
            return mesa
            
        except Exception as e:
            logger.error(f"Erro ao criar mesa: {str(e)}")
            raise
    
    @staticmethod
    def atualizar_mesa(mesa_id: int, data: Dict[str, Any], usuario_crm_id: Optional[int] = None) -> MesaNegocio:
        """
        Atualiza mesa existente
        
        Args:
            mesa_id: ID da mesa
            data: Dados a atualizar
            usuario_crm_id: ID do usuário
        
        Returns:
            Mesa atualizada
        """
        mesa = MesaService.get_mesa_por_id(mesa_id, usuario_crm_id)
        
        # Validar dados (parcialmente)
        validated_data = validate_mesa_data(data)
        
        # Atualizar campos
        for key, value in validated_data.items():
            setattr(mesa, key, value)
        
        try:
            with safe_commit(db.session, "atualizar mesa"):
                pass
            
            log_database_operation(logger, "UPDATE", "MesaNegocio", mesa.id)
            logger.info(f"Mesa atualizada: #{mesa.numero}")
            
            return mesa
            
        except Exception as e:
            logger.error(f"Erro ao atualizar mesa {mesa_id}: {str(e)}")
            raise
    
    @staticmethod
    def atualizar_situacao(mesa_id: int, nova_situacao: str, usuario_crm_id: Optional[int] = None) -> MesaNegocio:
        """
        Atualiza apenas a situação da mesa
        
        Args:
            mesa_id: ID da mesa
            nova_situacao: Nova situação
            usuario_crm_id: ID do usuário
        
        Returns:
            Mesa atualizada
        """
        from utils.validators import Validator
        from config.constants import SituacaoMesa
        
        # Validar situação
        situacoes_validas = [s.value for s in SituacaoMesa]
        nova_situacao = Validator.choice(nova_situacao, 'situacao', situacoes_validas)
        
        mesa = MesaService.get_mesa_por_id(mesa_id, usuario_crm_id)
        mesa.situacao = nova_situacao
        
        try:
            with safe_commit(db.session, "atualizar situação da mesa"):
                pass
            
            logger.info(f"Situação da mesa #{mesa.numero} atualizada para: {nova_situacao}")
            
            return mesa
            
        except Exception as e:
            logger.error(f"Erro ao atualizar situação da mesa {mesa_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_mesa_por_id(mesa_id: int, usuario_crm_id: Optional[int] = None) -> MesaNegocio:
        """
        Busca mesa por ID
        
        Args:
            mesa_id: ID da mesa
            usuario_crm_id: ID do usuário (filtro opcional)
        
        Returns:
            Mesa encontrada
        """
        query = MesaNegocio.query.options(joinedload(MesaNegocio.cliente))
        
        if usuario_crm_id:
            query = query.filter_by(usuario_crm_id=usuario_crm_id)
        
        mesa = query.get(mesa_id)
        
        if not mesa:
            raise ResourceNotFoundError("Mesa de Negócio", mesa_id)
        
        return mesa
    
    @staticmethod
    def listar_mesas(
        usuario_crm_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        situacao: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[MesaNegocio], int]:
        """
        Lista mesas com filtros e paginação
        
        Args:
            usuario_crm_id: Filtro por usuário
            cliente_id: Filtro por cliente
            situacao: Filtro por situação
            page: Página atual
            per_page: Itens por página
        
        Returns:
            Tupla (mesas, total)
        """
        query = MesaNegocio.query.options(joinedload(MesaNegocio.cliente))
        
        if usuario_crm_id:
            query = query.filter_by(usuario_crm_id=usuario_crm_id)
        
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        
        if situacao:
            query = query.filter_by(situacao=situacao)
        
        # Ordenar por data/hora decrescente
        query = query.order_by(MesaNegocio.data_registro.desc(), MesaNegocio.hora_registro.desc())
        
        total = query.count()
        mesas = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return mesas, total
    
    @staticmethod
    def deletar_mesa(mesa_id: int, usuario_crm_id: int) -> None:
        """
        Deleta uma mesa
        
        Args:
            mesa_id: ID da mesa
            usuario_crm_id: ID do usuário
        """
        mesa = MesaService.get_mesa_por_id(mesa_id, usuario_crm_id)
        
        try:
            with safe_commit(db.session, "deletar mesa"):
                db.session.delete(mesa)
            
            log_database_operation(logger, "DELETE", "MesaNegocio", mesa_id)
            logger.info(f"Mesa deletada: #{mesa.numero}")
            
        except Exception as e:
            logger.error(f"Erro ao deletar mesa {mesa_id}: {str(e)}")
            raise
    
    @staticmethod
    def _get_proximo_numero(usuario_crm_id: int) -> int:
        """
        Calcula o próximo número de mesa para o usuário
        
        Args:
            usuario_crm_id: ID do usuário
        
        Returns:
            Próximo número disponível
        """
        ultimo_numero = db.session.query(db.func.max(MesaNegocio.numero)).filter_by(
            usuario_crm_id=usuario_crm_id
        ).scalar() or 0
        
        return ultimo_numero + 1
    
    @staticmethod
    def calcular_estatisticas(usuario_crm_id: int) -> Dict[str, Any]:
        """
        Calcula estatísticas de mesas
        
        Args:
            usuario_crm_id: ID do usuário
        
        Returns:
            Dicionário com estatísticas
        """
        mesas = MesaNegocio.query.filter_by(usuario_crm_id=usuario_crm_id).all()
        
        total = len(mesas)
        em_negociacao = len([m for m in mesas if m.situacao == 'Em negociação'])
        ganhas = len([m for m in mesas if m.situacao == 'Ganho'])
        perdidas = len([m for m in mesas if m.situacao == 'Perdido'])
        
        valor_total_ganhas = sum(m.valor_total or 0 for m in mesas if m.situacao == 'Ganho')
        valor_total_em_negociacao = sum(m.valor_total or 0 for m in mesas if m.situacao == 'Em negociação')
        
        taxa_conversao = (ganhas / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'em_negociacao': em_negociacao,
            'ganhas': ganhas,
            'perdidas': perdidas,
            'valor_ganho': valor_total_ganhas,
            'valor_em_negociacao': valor_total_em_negociacao,
            'taxa_conversao': round(taxa_conversao, 2)
        }

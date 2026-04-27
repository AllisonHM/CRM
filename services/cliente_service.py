"""
Cliente Service - Lógica de negócio relacionada a clientes
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

from models import Cliente, MesaNegocio, Ocorrencia
from database_rls import db
from utils.validators import validate_cliente_data, ValidationError
from utils.exceptions import DatabaseError, ResourceNotFoundError, safe_commit
from utils.logger import setup_logger, log_database_operation

logger = setup_logger(__name__)


class ClienteService:
    """Service para operações de cliente"""
    
    @staticmethod
    def criar_cliente(data: Dict[str, Any], usuario_crm_id: int) -> Cliente:
        """
        Cria um novo cliente
        
        Args:
            data: Dados do cliente
            usuario_crm_id: ID do usuário CRM proprietário
        
        Returns:
            Cliente criado
        
        Raises:
            ValidationError: Se dados inválidos
            DatabaseError: Se erro ao salvar
        """
        # Validar dados
        validated_data = validate_cliente_data(data, is_update=False)
        
        # Criar cliente
        cliente = Cliente(
            usuario_crm_id=usuario_crm_id,
            **validated_data
        )
        
        # Salvar no banco
        try:
            with safe_commit(db.session, "criar cliente"):
                db.session.add(cliente)
            
            log_database_operation(logger, "CREATE", "Cliente", cliente.id)
            logger.info(f"Cliente criado com sucesso: {cliente.nome} (ID: {cliente.id})")
            
            return cliente
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {str(e)}")
            raise
    
    @staticmethod
    def atualizar_cliente(cliente_id: int, data: Dict[str, Any], usuario_crm_id: int) -> Cliente:
        """
        Atualiza um cliente existente
        
        Args:
            cliente_id: ID do cliente
            data: Dados a atualizar
            usuario_crm_id: ID do usuário CRM (para verificação de permissão)
        
        Returns:
            Cliente atualizado
        
        Raises:
            ResourceNotFoundError: Se cliente não encontrado
            ValidationError: Se dados inválidos
            DatabaseError: Se erro ao salvar
        """
        cliente = ClienteService.get_cliente_por_id(cliente_id, usuario_crm_id)
        
        # Validar dados
        validated_data = validate_cliente_data(data, is_update=True)
        
        # Atualizar campos
        for key, value in validated_data.items():
            setattr(cliente, key, value)
        
        # Salvar
        try:
            with safe_commit(db.session, "atualizar cliente"):
                pass  # Cliente já está no session
            
            log_database_operation(logger, "UPDATE", "Cliente", cliente.id)
            logger.info(f"Cliente atualizado: {cliente.nome} (ID: {cliente.id})")
            
            return cliente
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cliente {cliente_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_cliente_por_id(cliente_id: int, usuario_crm_id: Optional[int] = None) -> Cliente:
        """
        Busca cliente por ID
        
        Args:
            cliente_id: ID do cliente
            usuario_crm_id: ID do usuário (para filtro de tenant, opcional)
        
        Returns:
            Cliente encontrado
        
        Raises:
            ResourceNotFoundError: Se não encontrado
        """
        query = Cliente.query
        
        if usuario_crm_id:
            query = query.filter_by(usuario_crm_id=usuario_crm_id)
        
        cliente = query.get(cliente_id)
        
        if not cliente:
            raise ResourceNotFoundError("Cliente", cliente_id)
        
        return cliente
    
    @staticmethod
    def listar_clientes(
        usuario_crm_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 50,
        search: Optional[str] = None,
        tipo_pessoa: Optional[str] = None
    ) -> Tuple[List[Cliente], int]:
        """
        Lista clientes com paginação e filtros
        
        Args:
            usuario_crm_id: Filtro por usuário
            page: Página atual
            per_page: Itens por página
            search: Termo de busca (nome, telefone, email)
            tipo_pessoa: Filtro por tipo de pessoa
        
        Returns:
            Tupla (lista de clientes, total de registros)
        """
        query = Cliente.query
        
        # Filtro por usuário
        if usuario_crm_id:
            query = query.filter_by(usuario_crm_id=usuario_crm_id)
        
        # Filtro de busca
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Cliente.nome.ilike(search_term),
                    Cliente.telefone.ilike(search_term),
                    Cliente.email.ilike(search_term)
                )
            )
        
        # Filtro por tipo
        if tipo_pessoa:
            query = query.filter_by(tipo_pessoa=tipo_pessoa)
        
        # Ordenar por nome
        query = query.order_by(Cliente.nome.asc())
        
        # Paginar
        total = query.count()
        clientes = query.offset((page - 1) * per_page).limit(per_page).all()
        
        log_database_operation(logger, "READ", "Cliente", f"page {page}")
        
        return clientes, total
    
    @staticmethod
    def get_cliente_com_relacionamentos(cliente_id: int, usuario_crm_id: Optional[int] = None) -> Cliente:
        """
        Busca cliente com mesas e ocorrências (eager loading)
        
        Args:
            cliente_id: ID do cliente
            usuario_crm_id: ID do usuário (para filtro)
        
        Returns:
            Cliente com relacionamentos carregados
        """
        query = Cliente.query.options(
            joinedload(Cliente.mesas),
            joinedload(Cliente.ocorrencias)
        )
        
        if usuario_crm_id:
            query = query.filter_by(usuario_crm_id=usuario_crm_id)
        
        cliente = query.get(cliente_id)
        
        if not cliente:
            raise ResourceNotFoundError("Cliente", cliente_id)
        
        return cliente
    
    @staticmethod
    def deletar_cliente(cliente_id: int, usuario_crm_id: int) -> None:
        """
        Deleta um cliente
        
        Args:
            cliente_id: ID do cliente
            usuario_crm_id: ID do usuário (para verificação)
        
        Raises:
            ResourceNotFoundError: Se não encontrado
            DatabaseError: Se erro ao deletar
        """
        cliente = ClienteService.get_cliente_por_id(cliente_id, usuario_crm_id)
        
        try:
            with safe_commit(db.session, "deletar cliente"):
                db.session.delete(cliente)
            
            log_database_operation(logger, "DELETE", "Cliente", cliente_id)
            logger.info(f"Cliente deletado: ID {cliente_id}")
            
        except Exception as e:
            logger.error(f"Erro ao deletar cliente {cliente_id}: {str(e)}")
            raise
    
    @staticmethod
    def buscar_por_telefone(telefone: str, usuario_crm_id: Optional[int] = None) -> Optional[Cliente]:
        """
        Busca cliente por telefone
        
        Args:
            telefone: Número de telefone
            usuario_crm_id: ID do usuário (filtro opcional)
        
        Returns:
            Cliente encontrado ou None
        """
        query = Cliente.query.filter_by(telefone=telefone)
        
        if usuario_crm_id:
            query = query.filter_by(usuario_crm_id=usuario_crm_id)
        
        return query.first()
    
    @staticmethod
    def atualizar_nps(cliente_id: int, nota: int, comentario: Optional[str] = None, usuario_crm_id: Optional[int] = None) -> Cliente:
        """
        Atualiza nota NPS do cliente
        
        Args:
            cliente_id: ID do cliente
            nota: Nota de 0 a 10
            comentario: Comentário opcional
            usuario_crm_id: ID do usuário
        
        Returns:
            Cliente atualizado
        """
        from utils.validators import Validator
        
        # Validar nota
        nota = Validator.nps_score(nota)
        
        cliente = ClienteService.get_cliente_por_id(cliente_id, usuario_crm_id)
        
        cliente.nps_nota = nota
        cliente.nps_data = datetime.utcnow()
        cliente.nps_comentario = comentario
        cliente.aguardando_nps = False
        
        try:
            with safe_commit(db.session, "atualizar NPS"):
                pass
            
            logger.info(f"NPS atualizado para cliente {cliente_id}: nota {nota}")
            
            return cliente
            
        except Exception as e:
            logger.error(f"Erro ao atualizar NPS do cliente {cliente_id}: {str(e)}")
            raise

"""
Testes do ClienteService
"""
import pytest
from datetime import datetime, date
from services import ClienteService
from utils import ValidationError
from utils.exceptions import ResourceNotFoundError


class TestClienteService:
    """Testes do serviço de clientes"""
    
    def test_criar_cliente_valido(self, db_session, usuario_teste):
        """Testa criação de cliente com dados válidos"""
        data = {
            'nome': 'João Silva',
            'telefone': '11987654321',
            'email': 'joao@example.com',
            'tipo_pessoa': 'Física',
            'renda': 5000.00
        }
        
        cliente = ClienteService.criar_cliente(data, usuario_teste.id)
        
        assert cliente.id is not None
        assert cliente.nome == 'João Silva'
        assert cliente.telefone == '11987654321'
        assert cliente.email == 'joao@example.com'
        assert cliente.usuario_crm_id == usuario_teste.id
    
    def test_criar_cliente_telefone_invalido(self, usuario_teste):
        """Testa validação de telefone inválido"""
        data = {
            'nome': 'João Silva',
            'telefone': '123',  # Muito curto
            'tipo_pessoa': 'Física'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ClienteService.criar_cliente(data, usuario_teste.id)
        
        assert exc_info.value.field == 'telefone'
    
    def test_criar_cliente_email_invalido(self, usuario_teste):
        """Testa validação de email inválido"""
        data = {
            'nome': 'João Silva',
            'telefone': '11987654321',
            'email': 'email-invalido',
            'tipo_pessoa': 'Física'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ClienteService.criar_cliente(data, usuario_teste.id)
        
        assert exc_info.value.field == 'email'
    
    def test_buscar_cliente_por_id(self, db_session, cliente_teste, usuario_teste):
        """Testa busca de cliente por ID"""
        cliente = ClienteService.get_cliente_por_id(cliente_teste.id, usuario_teste.id)
        
        assert cliente.id == cliente_teste.id
        assert cliente.nome == cliente_teste.nome
    
    def test_buscar_cliente_inexistente(self, usuario_teste):
        """Testa busca de cliente que não existe"""
        with pytest.raises(ResourceNotFoundError):
            ClienteService.get_cliente_por_id(99999, usuario_teste.id)
    
    def test_listar_clientes_com_paginacao(self, db_session, usuario_teste):
        """Testa listagem de clientes com paginação"""
        # Criar 5 clientes
        for i in range(5):
            ClienteService.criar_cliente({
                'nome': f'Cliente {i}',
                'telefone': f'1198765432{i}',
                'tipo_pessoa': 'Física'
            }, usuario_teste.id)
        
        # Buscar primeira página (3 itens)
        clientes, total = ClienteService.listar_clientes(
            usuario_crm_id=usuario_teste.id,
            page=1,
            per_page=3
        )
        
        assert len(clientes) == 3
        assert total == 5
    
    def test_buscar_por_telefone(self, db_session, cliente_teste, usuario_teste):
        """Testa busca por telefone"""
        cliente = ClienteService.buscar_por_telefone(
            cliente_teste.telefone,
            usuario_teste.id
        )
        
        assert cliente is not None
        assert cliente.id == cliente_teste.id
    
    def test_atualizar_nps(self, db_session, cliente_teste, usuario_teste):
        """Testa atualização de NPS"""
        cliente = ClienteService.atualizar_nps(
            cliente_teste.id,
            nota=9,
            comentario='Excelente atendimento!',
            usuario_crm_id=usuario_teste.id
        )
        
        assert cliente.nps_nota == 9
        assert cliente.nps_comentario == 'Excelente atendimento!'
        assert cliente.nps_data is not None
        assert cliente.aguardando_nps is False
    
    def test_atualizar_nps_nota_invalida(self, cliente_teste, usuario_teste):
        """Testa NPS com nota inválida (> 10)"""
        with pytest.raises(ValidationError):
            ClienteService.atualizar_nps(
                cliente_teste.id,
                nota=11,  # Inválido
                usuario_crm_id=usuario_teste.id
            )


# ===== FIXTURES =====

@pytest.fixture
def usuario_teste(db_session):
    """Cria usuário para testes"""
    from models import UsuarioCRM
    
    usuario = UsuarioCRM(
        nome='Usuário Teste',
        email='teste@example.com',
        tipo_usuario='admin',
        ativo=True
    )
    usuario.set_password('senha123')
    
    db_session.add(usuario)
    db_session.commit()
    
    return usuario


@pytest.fixture
def cliente_teste(db_session, usuario_teste):
    """Cria cliente para testes"""
    from models import Cliente
    
    cliente = Cliente(
        usuario_crm_id=usuario_teste.id,
        nome='Cliente Teste',
        telefone='11987654321',
        email='cliente@example.com',
        tipo_pessoa='Física'
    )
    
    db_session.add(cliente)
    db_session.commit()
    
    return cliente

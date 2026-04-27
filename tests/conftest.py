"""
Configuração do Pytest
"""
import pytest
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope='session')
def app():
    """Cria aplicação Flask para testes"""
    from CRM import app as flask_app
    
    # Configurar para testes
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Banco em memória
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Desabilitar CSRF nos testes
    
    return flask_app


@pytest.fixture(scope='function')
def db_session(app):
    """Cria sessão de banco de dados para cada teste"""
    from database_rls import db
    
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de teste Flask"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner para testes"""
    return app.test_cli_runner()

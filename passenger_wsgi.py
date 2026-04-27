"""
Passenger WSGI para Locaweb
Este arquivo é o ponto de entrada da aplicação no servidor
"""
import sys
import os

# Caminho do interpretador Python do ambiente virtual
# AJUSTAR conforme informado pela Locaweb
INTERP = os.path.join(os.environ['HOME'], 'virtualenv', 'python3.10', 'bin', 'python3')

# Usar ambiente virtual
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Importar aplicação Flask
from CRM import app as application

# Para debug (comentar em produção)
# application.debug = False

if __name__ == '__main__':
    application.run()

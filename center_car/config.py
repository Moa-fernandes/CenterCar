# center_car/config.py

import os

# Host e porta padrão do servidor MCP
HOST = os.getenv('CENTERCAR_HOST', '127.0.0.1')
PORTA = int(os.getenv('CENTERCAR_PORTA', '5000'))

# Caminho do banco SQLite
RAIZ_PROJETO = os.path.abspath(os.path.dirname(__file__) + os.sep + '..')
CAMINHO_BD = os.getenv('CENTERCAR_BD', os.path.join(RAIZ_PROJETO, 'centercar.db'))

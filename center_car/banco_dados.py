# center_car/banco_dados.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# define o caminho do arquivo SQLite no diretório do projeto
CAMINHO_BD = os.path.join(os.path.dirname(__file__), '..', 'centercar.db')
URL_BD = f"sqlite:///{CAMINHO_BD}"

# cria o engine e a sessão
engine = create_engine(URL_BD, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def criar_banco():
    """
    Cria todas as tabelas no banco, de acordo com os modelos.
    """
    from center_car.modelo_veiculo import Base
    Base.metadata.create_all(bind=engine)

def obter_sessao():
    """
    Retorna uma nova sessão
    """
    return SessionLocal()

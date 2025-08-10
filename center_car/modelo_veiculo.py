# center_car/modelo_veiculo.py
"""
Modelo SQLAlchemy para veículos, com mixin de __repr__ e constantes de tamanho
para facilitar manutenção e evitar “números mágicos”.
"""

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Constantes de tamanho para evitar números mágicos
MAX_LEN_MARCA = 50
MAX_LEN_MODELO = 50
MAX_LEN_MOTORIZACAO = 50
MAX_LEN_TIPO_COMBUSTIVEL = 30
MAX_LEN_COR = 30
MAX_LEN_TRANSMISSAO = 30


class ReprMixin:
    """
    Mixin para gerar __repr__ baseado em campos declarados em _repr_fields.
    Cada classe filha deve definir _repr_fields como uma tupla de nomes de atributo.
    """
    _repr_fields: tuple[str, ...] = ()

    def __repr__(self) -> str:
        field_strings = (
            f"{name}={getattr(self, name)!r}"
            for name in self._repr_fields
        )
        return f"<{self.__class__.__name__}({', '.join(field_strings)})>"


class Veiculo(ReprMixin, Base):
    """
    Entidade Veículo, representa a tabela 'veiculos' no banco de dados.
    """
    __tablename__ = 'veiculos'

    # Colunas
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    marca: str = Column(String(MAX_LEN_MARCA), nullable=False)
    modelo: str = Column(String(MAX_LEN_MODELO), nullable=False)
    ano: int = Column(Integer, nullable=False)
    motorizacao: str = Column(String(MAX_LEN_MOTORIZACAO), nullable=False)
    tipo_combustivel: str = Column(String(MAX_LEN_TIPO_COMBUSTIVEL), nullable=False)
    cor: str = Column(String(MAX_LEN_COR), nullable=False)
    quilometragem: float = Column(Float, nullable=False)
    numero_portas: int = Column(Integer, nullable=False)
    transmissao: str = Column(String(MAX_LEN_TRANSMISSAO), nullable=False)
    preco: float = Column(Float, nullable=False)

    # Campos incluídos no __repr__
    _repr_fields = (
        'id',
        'marca',
        'modelo',
        'ano',
        'tipo_combustivel',
        'preco',
    )

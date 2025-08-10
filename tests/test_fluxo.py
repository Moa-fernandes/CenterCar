# tests/test_fluxo.py

import json
import socket

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from center_car.modelo_veiculo import Base, Veiculo
from cliente.cliente_mcp import envia_filtros
from servidor.servidor_mcp import aplicar_filtros

# --- Parte 1: testes de filtros com SQLAlchemy ---


@pytest.fixture(scope="function")
def sessao_em_memoria(tmp_path, monkeypatch):
    # cria banco SQLite em memória e popula
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    sess = Session()
    # dois veículos de teste
    sess.add_all(
        [
            Veiculo(
                marca="X",
                modelo="Alpha",
                ano=2020,
                motorizacao="1.0",
                tipo_combustivel="Gasolina",
                cor="Branco",
                quilometragem=1000,
                numero_portas=4,
                transmissao="Manual",
                preco=50000,
            ),
            Veiculo(
                marca="Y",
                modelo="Beta",
                ano=2018,
                motorizacao="2.0",
                tipo_combustivel="Diesel",
                cor="Preto",
                quilometragem=2000,
                numero_portas=2,
                transmissao="Automática",
                preco=70000,
            ),
        ]
    )
    sess.commit()
    yield sess
    sess.close()


def test_aplicar_filtro_marca(sessao_em_memoria):
    query = sessao_em_memoria.query(Veiculo)
    filtros = {"marca": "X"}
    resultados = aplicar_filtros(query, filtros).all()
    assert len(resultados) == 1
    assert resultados[0].modelo == "Alpha"


def test_aplicar_filtro_preco_max(sessao_em_memoria):
    query = sessao_em_memoria.query(Veiculo)
    filtros = {"preco_max": 60000}
    resultados = aplicar_filtros(query, filtros).all()
    assert len(resultados) == 1
    assert resultados[0].marca == "X"


# --- Parte 2: testes de cliente MCP simulando socket ---


class FakeSocket:
    """
    Simula um socket com respostas pré-carregadas.
    O primeiro recv(4) deve retornar o tamanho do payload,
    os próximos recvs devolvem pedaços do JSON.
    """

    def __init__(self, responses):
        self._resp = responses.copy()
        self.sent = b""

    def settimeout(self, _):  # tolera chamadas em código real
        pass

    def connect(self, addr):
        pass

    def sendall(self, data):
        self.sent += data

    def recv(self, bufsize):
        if not self._resp:
            return b""
        # retorna o próximo bloco pronto (já respeita o framing do teste)
        return self._resp.pop(0)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


@pytest.fixture(autouse=True)
def fake_socket(monkeypatch):
    """
    Monkeypatch em socket.socket para usar FakeSocket.
    Fornece lista vazia de respostas para cada teste, que
    você preenche dentro do próprio teste via fake_socket.respostas.
    """

    def _factory():
        # será substituído no teste quando necessário
        return FakeSocket([])

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: _factory())
    return _factory


def test_envia_filtros_retorna_lista(monkeypatch):
    # prepara a resposta JSON no fake (modo legado: lista direta)
    dados = json.dumps([{"id": 1, "marca": "X"}]).encode("utf-8")
    tamanho = len(dados).to_bytes(4, "big")
    fake = FakeSocket([tamanho, dados])
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    resultado = envia_filtros({"marca": "X"})
    assert resultado == [{"id": 1, "marca": "X"}]

    # checa que o cliente mandou um payload válido (aceita MCP OU legado)
    payload = fake.sent[4:]  # pula os 4 bytes de comprimento
    obj = json.loads(payload.decode("utf-8"))

    # MCP: envelope {"tool":"search_cars","args":{"marca":"X"}}  OU  Legado: {"marca":"X"}
    if isinstance(obj, dict) and "tool" in obj:
        assert obj["tool"] == "search_cars"
        assert obj["args"] == {"marca": "X"}
    else:
        assert obj == {"marca": "X"}


def test_envia_filtros_trata_excecao(monkeypatch):
    # Simula falha de conexão
    class BadSocket:
        def settimeout(self, _):
            pass

        def connect(self, addr):
            raise ConnectionRefusedError

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(socket, "socket", lambda *a, **k: BadSocket())

    resultado = envia_filtros({"marca": "X"})
    assert resultado == []

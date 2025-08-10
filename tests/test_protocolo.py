import json
import socket

import pytest

# Importa cliente e servidor considerando dois layouts possíveis do projeto
try:
    import servidor.servidor_mcp as srv
except ImportError:  # layout plano
    import servidor_mcp as srv

try:
    from cliente.cliente_mcp import envia_filtros as _envia
except ImportError:  # layout plano
    from cliente_mcp import envia_filtros as _envia


def _frame(obj) -> bytes:
    """Serializa obj em JSON UTF-8 com prefixo de 4 bytes (big-endian)."""
    data = json.dumps(obj).encode("utf-8")
    return len(data).to_bytes(4, "big") + data


class FakeConn:
    """
    Conexão fake para chamar srv.trata_cliente sem abrir socket real.
    Alimentamos com um único request (framed). Tudo que o servidor
    enviar via sendall() fica em .sent.
    """

    def __init__(self, framed_request: bytes):
        self._buf = memoryview(framed_request)
        self._pos = 0
        self.sent = b""
        self.timeout = None

    # API usada pelo servidor
    def settimeout(self, t: float) -> None:
        self.timeout = t

    def recv(self, n: int) -> bytes:
        if self._pos >= len(self._buf):
            return b""
        end = min(self._pos + n, len(self._buf))
        chunk = self._buf[self._pos : end].tobytes()
        self._pos = end
        return chunk

    def sendall(self, data: bytes) -> None:
        self.sent += data

    # contexto "with conn:"
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False  # não suprime exceções


class _V:
    """Objeto veículo mínimo para os testes (atributos usados pelo servidor)."""

    def __init__(self, **k):
        self.id = k.get("id", 1)
        self.marca = k.get("marca", "Jeep")
        self.modelo = k.get("modelo", "Alpha")
        self.ano = k.get("ano", 2021)
        self.tipo_combustivel = k.get("tipo_combustivel", "Etanol")
        self.cor = k.get("cor", "Azul")
        self.quilometragem = k.get("quilometragem", 12345.6)
        self.numero_portas = k.get("numero_portas", 4)
        self.transmissao = k.get("transmissao", "Automático")
        self.preco = k.get("preco", 98765.43)


class FakeQuery:
    def __init__(self, results):
        self._results = results

    # o servidor só chama .all() após aplicar filtros
    def all(self):
        return self._results


class FakeSession:
    def __init__(self, results):
        self._results = results

    def query(self, _model):
        return FakeQuery(self._results)

    def close(self):
        pass


def test_cliente_envia_envelope(monkeypatch):
    """
    Garante que o cliente envia o envelope MCP {"tool":"search_cars","args":{...}}.
    Obs.: este teste espera que você tenha atualizado o cliente para o novo contrato.
    """
    # prepara uma resposta OK vazia para o cliente conseguir completar o fluxo
    body = {"ok": True, "result": []}
    data = json.dumps(body).encode("utf-8")
    tamanho = len(data).to_bytes(4, "big")

    created = []

    class FakeSocket:
        def __init__(self):
            self.sent = b""
            self._resp = [tamanho, data]

        def settimeout(self, t):
            pass

        def connect(self, addr):
            pass

        def sendall(self, b):
            self.sent += b

        def recv(self, n):
            return self._resp.pop(0) if self._resp else b""

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

    def factory(*a, **k):
        s = FakeSocket()
        created.append(s)
        return s

    monkeypatch.setattr(socket, "socket", factory)

    _envia({"marca": "X"})

    # Bytes enviados pelo cliente (pulando o header)
    fake = created[-1]
    payload = fake.sent[4:]
    obj = json.loads(payload.decode("utf-8"))
    assert obj.get("tool") == "search_cars"
    assert obj.get("args") == {"marca": "X"}


def test_servidor_rejeita_tool_desconhecida():
    """Envelope com tool inválida deve retornar ok:false + error.code='UNKNOWN_TOOL'."""
    req = {"tool": "xpto", "args": {}}
    conn = FakeConn(_frame(req))
    srv.trata_cliente(conn, ("127.0.0.1", 12345))

    header, body = conn.sent[:4], conn.sent[4:]
    assert int.from_bytes(header, "big") == len(body)
    msg = json.loads(body.decode("utf-8"))
    assert msg["ok"] is False
    assert msg["error"]["code"] == "UNKNOWN_TOOL"


def test_servidor_rejeita_args_nao_objeto():
    """Envelope com args que não é objeto deve retornar INVALID_REQUEST."""
    req = {"tool": "search_cars", "args": "marca=Jeep"}
    conn = FakeConn(_frame(req))
    srv.trata_cliente(conn, ("127.0.0.1", 12345))

    msg = json.loads(conn.sent[4:].decode("utf-8"))
    assert msg["ok"] is False
    assert msg["error"]["code"] == "INVALID_REQUEST"


def test_servidor_ok_envelope_valido(monkeypatch):
    """
    Com envelope válido, o servidor deve responder ok:true e uma lista de veículos.
    Evitamos I/O real mockando a sessão do banco e a função aplicar_filtros.
    """
    results = [
        _V(id=1, marca="Jeep", modelo="Alpha", ano=2021),
        _V(id=2, marca="Ford", modelo="Beta", ano=2020),
    ]

    # Mocka a sessão e o pipeline de filtros para devolver nossos results
    monkeypatch.setattr(srv, "obter_sessao", lambda: FakeSession(results))
    monkeypatch.setattr(srv, "aplicar_filtros", lambda q, f: q)

    req = {"tool": "search_cars", "args": {"marca": "Jeep", "ano_min": 2020}}
    conn = FakeConn(_frame(req))
    srv.trata_cliente(conn, ("127.0.0.1", 12345))

    msg = json.loads(conn.sent[4:].decode("utf-8"))
    assert msg["ok"] is True
    assert isinstance(msg["result"], list)
    assert len(msg["result"]) == 2
    assert {"id", "marca", "modelo", "ano", "cor", "quilometragem", "preco"} <= set(msg["result"][0].keys())

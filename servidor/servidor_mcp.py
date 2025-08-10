import socket
import threading
import json
import logging
from typing import Dict, Any, List, Tuple

from center_car.config import HOST, PORTA
from center_car.banco_dados import obter_sessao
from center_car.modelo_veiculo import Veiculo

# Configuração
BUFFER_SIZE: int = 64 * 1024  # 64 KiB
EXPECTED_TOOL = "search_cars"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ------------------------ Filtros / Util ------------------------ #

def aplicar_filtros(query: Any, filtros: Dict[str, Any]) -> Any:
    """
    Recebe Query de SQLAlchemy e um dict de filtros,
    aplicam-se na consulta e retorna o query resultante.
    """
    if 'marca' in filtros:
        query = query.filter(Veiculo.marca == filtros['marca'])
    if 'modelo' in filtros:
        termo = f"%{filtros['modelo']}%"
        query = query.filter(Veiculo.modelo.ilike(termo))
    if 'ano_min' in filtros:
        query = query.filter(Veiculo.ano >= filtros['ano_min'])
    if 'ano_max' in filtros:
        query = query.filter(Veiculo.ano <= filtros['ano_max'])
    if 'tipo_combustivel' in filtros:
        query = query.filter(Veiculo.tipo_combustivel == filtros['tipo_combustivel'])
    if 'preco_max' in filtros:
        query = query.filter(Veiculo.preco <= filtros['preco_max'])
    return query


def _recv_all(conn: socket.socket, total_bytes: int) -> bytes:
    """Lê exatamente `total_bytes` bytes do socket (ou menos, se a conexão encerrar)."""
    chunks: List[bytes] = []
    bytes_lidos = 0
    while bytes_lidos < total_bytes:
        to_read = min(BUFFER_SIZE, total_bytes - bytes_lidos)
        parte = conn.recv(to_read)
        if not parte:
            break
        chunks.append(parte)
        bytes_lidos += len(parte)
    return b"".join(chunks)


def _ok(result: List[Dict[str, Any]]) -> bytes:
    body = {"ok": True, "result": result}
    data = json.dumps(body).encode("utf-8")
    return len(data).to_bytes(4, "big") + data


def _erro(code: str, message: str) -> bytes:
    body = {"ok": False, "error": {"code": code, "message": message}}
    data = json.dumps(body).encode("utf-8")
    return len(data).to_bytes(4, "big") + data


def _validar_args(f: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validação simples dos filtros recebidos (tipos/chaves conhecidas).
    Ignora o que não bater com o esperado.
    """
    out: Dict[str, Any] = {}
    if isinstance(f.get("marca"), str): out["marca"] = f["marca"]
    if isinstance(f.get("modelo"), str): out["modelo"] = f["modelo"]
    if isinstance(f.get("tipo_combustivel"), str): out["tipo_combustivel"] = f["tipo_combustivel"]
    if isinstance(f.get("ano_min"), int): out["ano_min"] = f["ano_min"]
    if isinstance(f.get("ano_max"), int): out["ano_max"] = f["ano_max"]
    if isinstance(f.get("preco_max"), (int, float)): out["preco_max"] = float(f["preco_max"])
    return out

# ------------------------ Handler da conexão ------------------------ #

def trata_cliente(conn: socket.socket, addr: Tuple[str, int]) -> None:
    """
    Fluxo:
      1) lê header (4 bytes) com o tamanho do payload
      2) lê e decodifica JSON
      3) aceita dois formatos:
         a) MCP (envelope): {"tool": "search_cars", "args": {...}}
         b) legado: {...filtros...}   -> mantém compatibilidade
      4) consulta banco, retorna:
         - MCP: {"ok": true, "result": [...]}  (ou {"ok": false, "error": {...}})
         - legado: lista simples (como antes)
    """
    with conn:
        conn.settimeout(5.0)

        tamanho_bytes = conn.recv(4)
        if len(tamanho_bytes) < 4:
            # header inválido: não dá pra responder num formato confiável
            return
        tamanho = int.from_bytes(tamanho_bytes, "big")

        payload = _recv_all(conn, tamanho)
        try:
            req = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            # JSON inválido -> se for MCP, devolvemos erro MCP; se não souber, devolve lista vazia (legado)
            conn.sendall(_erro("INVALID_JSON", "JSON malformado"))
            return

        # ---- Modo MCP (envelope) ----
        if isinstance(req, dict) and "tool" in req and "args" in req:
            if req["tool"] != EXPECTED_TOOL:
                conn.sendall(_erro("UNKNOWN_TOOL", f"Tool '{req['tool']}' não suportada"))
                return
            if not isinstance(req["args"], dict):
                conn.sendall(_erro("INVALID_REQUEST", "'args' deve ser um objeto"))
                return

            filtros = _validar_args(req["args"])
            logging.info("MCP %s filtros=%s", addr, filtros)

            sessao = obter_sessao()
            try:
                consulta = aplicar_filtros(sessao.query(Veiculo), filtros)
                resultados: List[Dict[str, Any]] = [
                    {
                        "id": v.id,
                        "marca": v.marca,
                        "modelo": v.modelo,
                        "ano": v.ano,
                        "tipo_combustivel": v.tipo_combustivel,
                        "cor": v.cor,
                        "quilometragem": v.quilometragem,
                        "numero_portas": v.numero_portas,
                        "transmissao": v.transmissao,
                        "preco": v.preco,
                    }
                    for v in consulta.all()
                ]
            except Exception as e:
                logging.exception("Erro processando requisição MCP")
                conn.sendall(_erro("SERVER_ERROR", str(e)))
                return
            finally:
                sessao.close()

            conn.sendall(_ok(resultados))
            return

        # ---- Modo legado (apenas filtros): mantém compatibilidade com cliente antigo ----
        filtros = _validar_args(req if isinstance(req, dict) else {})
        logging.info("LEGACY %s filtros=%s", addr, filtros)

        sessao = obter_sessao()
        try:
            consulta = aplicar_filtros(sessao.query(Veiculo), filtros)
            resultados: List[Dict[str, Any]] = [
                {
                    "id": v.id,
                    "marca": v.marca,
                    "modelo": v.modelo,
                    "ano": v.ano,
                    "tipo_combustivel": v.tipo_combustivel,
                    "cor": v.cor,
                    "quilometragem": v.quilometragem,
                    "numero_portas": v.numero_portas,
                    "transmissao": v.transmissao,
                    "preco": v.preco,
                }
                for v in consulta.all()
            ]
        finally:
            sessao.close()

        resposta = json.dumps(resultados).encode("utf-8")
        header = len(resposta).to_bytes(4, "big")
        conn.sendall(header + resposta)


# ------------------------ Bootstrap do servidor ------------------------ #

def iniciar_servidor() -> None:
    """Inicializa o socket servidor e aceita conexões em loop."""
    print(f"🚀 Servidor MCP iniciado em {HOST}:{PORTA}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PORTA))
        servidor.listen()
        while True:
            conn, addr = servidor.accept()
            thread = threading.Thread(
                target=trata_cliente,
                args=(conn, addr),
                daemon=True,
            )
            thread.start()


if __name__ == "__main__":
    iniciar_servidor()

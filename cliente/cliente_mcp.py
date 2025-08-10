import socket
import json
from typing import Any, Dict, List, Union

from center_car.config import HOST, PORTA

BUFFER_SIZE: int = 64 * 1024  # 64 KiB para recv
ENVELOPE_TOOL = "search_cars"


def envia_filtros(filtros: Dict[str, Any]) -> List[Any]:
    """
    Envia filtros ao servidor no envelope MCP:
        {"tool": "search_cars", "args": {...}}
    Espera resposta MCP:
        {"ok": true, "result": [...]}
    Fallback: se vier uma lista (modo legado), retorna a lista.
    Em qualquer erro, retorna [].
    """
    envelope = {"tool": ENVELOPE_TOOL, "args": filtros}
    payload = json.dumps(envelope).encode("utf-8")
    header = len(payload).to_bytes(4, "big")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # tolera FakeSocket do teste (que pode não ter settimeout)
            try:
                sock.settimeout(3.0)
            except Exception:
                pass

            try:
                sock.connect((HOST, PORTA))
            except ConnectionRefusedError:
                return []

            # envia header + payload
            sock.sendall(header + payload)

            # lê header da resposta
            tamanho_bytes = sock.recv(4)
            if len(tamanho_bytes) < 4:
                return []

            tamanho = int.from_bytes(tamanho_bytes, "big")
            if tamanho <= 0:
                return []

            # lê corpo completo
            recebido = _recv_all(sock, tamanho)

        data = _parse_json(recebido)

        # Contrato MCP
        if isinstance(data, dict):
            if data.get("ok") is True:
                result = data.get("result", [])
                return result if isinstance(result, list) else []
            # ok:false ou inesperado
            return []

        # Modo legado (lista direta)
        if isinstance(data, list):
            return data

        return []
    except Exception:
        return []


def _recv_all(sock: socket.socket, total_bytes: int) -> bytes:
    chunks: List[bytes] = []
    bytes_lidos = 0
    while bytes_lidos < total_bytes:
        to_read = min(BUFFER_SIZE, total_bytes - bytes_lidos)
        parte = sock.recv(to_read)
        if not parte:
            break
        chunks.append(parte)
        bytes_lidos += len(parte)
    return b"".join(chunks)


def _parse_json(data: bytes) -> Union[Dict[str, Any], List[Any], Any]:
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        return []

# tests/test_agente.py (apenas o helper atualizado)
import types
import importlib
import sys
import builtins
import pytest

def _load_agente_with_fake_client(monkeypatch, fake_envia=None):
   
    if fake_envia is None:
        def fake_envia(_):
            return []

    # cria submódulo fake cliente.cliente_mcp
    cliente_mcp = types.ModuleType("cliente.cliente_mcp")
    cliente_mcp.envia_filtros = fake_envia
    monkeypatch.setitem(sys.modules, "cliente.cliente_mcp", cliente_mcp)

    # garante reload do agente
    if "cliente.agente_terminal" in sys.modules:
        del sys.modules["cliente.agente_terminal"]

    agente = importlib.import_module("cliente.agente_terminal")
    return agente



def test_exibir_resultados_formato(monkeypatch, capsys):
    agente = _load_agente_with_fake_client(monkeypatch)

    veiculos = [{
        "id": 1,
        "marca": "Jeep",
        "modelo": "Alpha",
        "ano": 2021,
        "cor": "Azul",
        "quilometragem": 12345.6,
        "preco": 98765.43,
        "tipo_combustivel": "Etanol",
        "numero_portas": 4,
        "transmissao": "Automático",
    }]

    agente.exibir_resultados(veiculos)
    out = capsys.readouterr().out

    # Mensagem de cabeçalho
    assert "👍 Encontrei 1 veículo(s) compatível(eis):" in out
    # Linha do veículo (note o ponto "•" e o travessão "–")
    assert " • Jeep Alpha (2021) – Azul, 12345.6 km, R$ 98765.43" in out


def test_exibir_resultados_sem_itens(monkeypatch, capsys):
    agente = _load_agente_with_fake_client(monkeypatch)

    agente.exibir_resultados([])
    out = capsys.readouterr().out

    assert "Desculpe, não encontrei nenhum veículo" in out


def test_exibir_listagem_completa(monkeypatch, capsys):
    agente = _load_agente_with_fake_client(monkeypatch)

    veiculos = [{
        "id": 7,
        "marca": "Ford",
        "modelo": "Beta",
        "ano": 2018,
        "cor": "Preto",
        "quilometragem": 5000,
        "preco": 50000,
        "tipo_combustivel": "Gasolina",
        "numero_portas": 4,
        "transmissao": "Manual",
    }]

    agente.exibir_listagem_completa(veiculos)
    out = capsys.readouterr().out

    assert "Listagem completa: 1 veículo(s) no sistema:" in out
    assert "7: Ford Beta (2018) – Preto, 5000 km, R$ 50000" in out


def test_coletar_criterios_fluxo_basico(monkeypatch):
    # Mock do cliente (não será chamado nesse teste, mas precisa existir)
    agente = _load_agente_with_fake_client(monkeypatch)

    # Simula entradas do usuário na ordem:
    # marca, modelo, ano_min, ano_max, combustível, preço_max
    entradas = iter([
        "jeep",     # marca -> title()
        "alp",      # modelo -> title()
        "2020",     # ano_min -> int
        "",         # ano_max -> ignorado
        "etanol",   # tipo_combustivel -> title()
        "100000",   # preco_max -> float
    ])
    monkeypatch.setattr(builtins, "input", lambda *_args, **_kw: next(entradas))

    filtros = agente.coletar_criterios()

    assert filtros["marca"] == "Jeep"
    assert filtros["modelo"] == "Alp"
    assert filtros["ano_min"] == 2020
    assert "ano_max" not in filtros
    assert filtros["tipo_combustivel"] == "Etanol"
    assert filtros["preco_max"] == 100000.0


def test_pergunta_simples(monkeypatch):
    agente = _load_agente_with_fake_client(monkeypatch)

    # Responde "s" -> True
    monkeypatch.setattr(builtins, "input", lambda *_: "s")
    assert agente.pergunta_simples("confirma?") is True

    # Responde "n" -> False
    monkeypatch.setattr(builtins, "input", lambda *_: "n")
    assert agente.pergunta_simples("confirma?") is False

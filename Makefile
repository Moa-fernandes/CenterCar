.PHONY: setup db seed server agent test lint fmt

PY=python

setup:
	$(PY) -m venv .venv

db:
	$(PY) -c "from center_car.banco_dados import criar_banco; criar_banco()"

seed:
	$(PY) -m center_car.gerar_dados_ficticios

server:
	$(PY) -m servidor.servidor_mcp

agent:
	$(PY) -m cliente.agente_terminal

test:
	pytest -q

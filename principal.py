# principal.py

import argparse
import threading
import time
from servidor.servidor_mcp import iniciar_servidor
from cliente.agente_terminal import main as iniciar_agente

def main():
    parser = argparse.ArgumentParser(
        description='CenterCar: servidor e/ou agente de terminal MCP')
    parser.add_argument(
        '--servidor', action='store_true',
        help='Inicia apenas o servidor MCP')
    parser.add_argument(
        '--cliente', action='store_true',
        help='Inicia apenas o agente de terminal')
    parser.add_argument(
        '--tudo', action='store_true',
        help='Inicia servidor e agente juntos')

    args = parser.parse_args()

    if args.servidor:
        iniciar_servidor()

    elif args.cliente:
        iniciar_agente()

    elif args.tudo:
        # sobe servidor em thread
        t = threading.Thread(target=iniciar_servidor, daemon=True)
        t.start()
        # dá uma pausa rápida pra garantir que o servidor esteja aceitando conexões
        time.sleep(1)
        iniciar_agente()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

import sys
from typing import Any, Dict, List

from cliente.cliente_mcp import envia_filtros

# Mensagens e constantes
WELCOME_BANNER: str = "=== CenterCar ===\n"
INTRO_MESSAGE: str = (
    "Olá! Eu sou o CenterCar Bot e vou te ajudar a encontrar veículos.\n"
    "Pule qualquer pergunta apertando Enter, tá certo? Vamos lá?\n"
)
SEPARATOR: str = "-" * 40

PROMPT_BRAND: str = "Qual marca você procura no momento?"
PROMPT_MODEL: str = "E qual modelo (ou parte do nome) você tem em mente, pode nos contar?"
PROMPT_YEAR_MIN: str = "Ano mínimo que você desejaria? (ex: 2010)?"
PROMPT_YEAR_MAX: str = "Ano máximo que você desejaria? (ex: 2023)?"
PROMPT_FUEL: str = "Que tipo de combustível? " "(Gasolina, Etanol, Diesel, Elétrico, Híbrido?)"
PROMPT_PRICE_MAX: str = "Preço máximo que você deseja, digite somente os números, por favor. (somente números)?"

FINAL_PROMPT_LIST_ALL: str = (
    "Quer dar uma olhada em todos os nossos carros cadastrados? " "Olha que vale a pena hein!..."
)
FINAL_PROMPT_AGAIN: str = "Deseja fazer outra consulta com a gente? Vai ser rapidinho..."

NO_MATCH_MSG: str = "\n😞 Desculpe, não encontrei nenhum veículo com esses critérios, " "vamos procurar mais?\n"
FOUND_MSG_TEMPLATE: str = "\n👍 Encontrei {count} veículo(s) compatível(eis):\n"
EMPTY_LIST_MSG: str = "\nNenhum veículo cadastrado.\n"
FULL_LIST_MSG_TEMPLATE: str = "\nListagem completa: {count} veículo(s) no sistema:\n"

# Normalização “humanizada” de combustível (aceita variações do usuário)
FUEL_MAP = {
    "gasolina": "Gasolina",
    "etanol": "Etanol",
    "diesel": "Diesel",
    "elétrico": "Elétrico",
    "eletrico": "Elétrico",
    "hibrido": "Flex",  # muitos usuários escrevem “hibrido”, dataset usa “Flex”
    "híbrido": "Flex",
    "flex": "Flex",
}


def normaliza_combustivel(valor: str) -> str:
    """
    Normaliza a entrada do usuário para os valores usados no dataset.
    Se não reconhecer, retorna Title Case da entrada.
    """
    key = valor.strip().lower()
    return FUEL_MAP.get(key, valor.title())


def pergunta_livre(pergunta: str) -> str:
    """
    Faz uma pergunta livre e retorna a resposta (strip).
    """
    return input(pergunta + " ").strip()


def pergunta_simples(pergunta: str) -> bool:
    """
    Faz uma pergunta sim/não e retorna True se o usuário digitar 's' ou 'S'.
    """
    resp = input(f"{pergunta} (s/N) ").strip().lower()
    return resp == "s"


def coletar_criterios() -> Dict[str, Any]:
    """
    Interage com o usuário para coletar filtros de busca de veículos.
    Retorna um dict com possíveis chaves:
    'marca', 'modelo', 'ano_min', 'ano_max', 'tipo_combustivel', 'preco_max'
    """
    print(INTRO_MESSAGE)
    filtros: Dict[str, Any] = {}

    marca = pergunta_livre(PROMPT_BRAND)
    if marca:
        filtros["marca"] = marca.title()

    modelo = pergunta_livre(PROMPT_MODEL)
    if modelo:
        filtros["modelo"] = modelo.title()

    ano_min = pergunta_livre(PROMPT_YEAR_MIN)
    if ano_min.isdigit():
        filtros["ano_min"] = int(ano_min)

    ano_max = pergunta_livre(PROMPT_YEAR_MAX)
    if ano_max.isdigit():
        filtros["ano_max"] = int(ano_max)

    combustivel = pergunta_livre(PROMPT_FUEL)
    if combustivel:
        filtros["tipo_combustivel"] = normaliza_combustivel(combustivel)

    preco_max = pergunta_livre(PROMPT_PRICE_MAX)
    try:
        if preco_max:
            filtros["preco_max"] = float(preco_max)
    except ValueError:
        # ignora valor inválido
        pass

    return filtros


def exibir_resultados(veiculos: List[Dict[str, Any]]) -> None:
    """
    Exibe lista de veículos compatíveis com os critérios.
    """
    if not veiculos:
        print(NO_MATCH_MSG)
        return

    print(FOUND_MSG_TEMPLATE.format(count=len(veiculos)))
    for v in veiculos:
        print(
            f" • {v.get('marca')} {v.get('modelo')} ({v.get('ano')}) – "
            f"{v.get('cor')}, {v.get('quilometragem')} km, "
            f"R$ {v.get('preco')}"
        )
    print()


def exibir_listagem_completa(veiculos: List[Dict[str, Any]]) -> None:
    """
    Exibe todos os veículos cadastrados no sistema.
    """
    if not veiculos:
        print(EMPTY_LIST_MSG)
        return

    print(FULL_LIST_MSG_TEMPLATE.format(count=len(veiculos)))
    for v in veiculos:
        print(
            f"{v.get('id')}: {v.get('marca')} {v.get('modelo')} "
            f"({v.get('ano')}) – {v.get('cor')}, "
            f"{v.get('quilometragem')} km, R$ {v.get('preco')}"
        )
    print()


def main() -> None:
    """
    Loop principal do agente no terminal.
    """
    print(WELCOME_BANNER)
    while True:
        filtros = coletar_criterios()
        print("\nBuscando veículos...")
        veiculos = envia_filtros(filtros)
        exibir_resultados(veiculos)

        if pergunta_simples(FINAL_PROMPT_LIST_ALL):
            todos = envia_filtros({})
            exibir_listagem_completa(todos)

        if not pergunta_simples(FINAL_PROMPT_AGAIN):
            print("\nObrigado por usar o CenterCar. Até a próxima!")
            sys.exit(0)

        print("\n" + SEPARATOR + "\n")


if __name__ == "__main__":
    main()

import argparse
from random import choice, randint, uniform
from typing import Final

from faker import Faker
from faker.exceptions import UniquenessException

from center_car.banco_dados import engine, obter_sessao
from center_car.modelo_veiculo import Base, Veiculo

# Constantes de configuração
DEFAULT_QTD: Final[int] = 100
MARCAS: Final[list[str]] = ["Ford", "Chevrolet", "Toyota", "Honda", "Volkswagen", "BMW", "Jeep", "Jaguar"]
COMBUSTIVEIS: Final[list[str]] = ["Gasolina", "Etanol", "Diesel", "Flex", "Elétrico"]
TRANSMISSOES: Final[list[str]] = ["Manual", "Automática", "CVT"]
FLUSH_INTERVAL: Final[int] = 50


def create_tables() -> None:
    """
    Garante que todas as tabelas declaradas nos modelos existam no banco.
    """
    Base.metadata.create_all(bind=engine)


def popula_bd(qtd: int = DEFAULT_QTD) -> None:
    """
    Gera e insere `qtd` veículos fictícios no banco de dados.

    - Usa Faker em pt_BR para nomes e cores.
    - Garante unicidade de `modelo` até esgotar o pool e, então,
      volta a nomes repetidos.
    - Faz flush a cada `FLUSH_INTERVAL` objetos para controlar uso de memória.
    """
    faker = Faker("pt_BR")
    faker.unique.clear()

    # Context manager assegura commit/rollback e fechamento da sessão
    with obter_sessao() as session:
        for i in range(qtd):
            try:
                modelo = faker.unique.word().title()
            except UniquenessException:
                modelo = faker.word().title()

            veic = Veiculo(
                marca=choice(MARCAS),
                modelo=modelo,
                ano=randint(2000, 2025),
                motorizacao=f"{randint(1, 4)}.0",
                tipo_combustivel=choice(COMBUSTIVEIS),
                cor=faker.color_name(),
                quilometragem=round(uniform(0, 200_000), 2),
                numero_portas=choice([2, 4, 5]),
                transmissao=choice(TRANSMISSOES),
                preco=round(uniform(10_000, 300_000), 2),
            )
            session.add(veic)

            if (i + 1) % FLUSH_INTERVAL == 0:
                session.flush()

        # Commit ao final de todas as inserções
        session.commit()

    print(f"{qtd} veículos inseridos com sucesso!")


def parse_args() -> int:
    """
    Lê argumentos de linha de comando para definir a quantidade de veículos.
    """
    parser = argparse.ArgumentParser(description="Gera dados fictícios de veículos no banco de dados")
    parser.add_argument(
        "quantidade",
        nargs="?",
        type=int,
        default=DEFAULT_QTD,
        help=f"Número de veículos a inserir (padrão: {DEFAULT_QTD})",
    )
    args = parser.parse_args()
    return args.quantidade


def main() -> None:
    """
    Ponto de entrada:
    1. Cria as tabelas (se não existirem).
    2. Lê argumentos.
    3. Popula o banco.
    """
    create_tables()
    qtd = parse_args()
    popula_bd(qtd)


if __name__ == "__main__":
    main()

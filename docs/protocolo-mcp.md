# Protocolo MCP — CenterCar (contrato simplificado)

Este documento descreve **como o cliente conversa com o servidor** usando um envelope MCP minimalista.

## Camada de transporte
- **Socket TCP**.
- **Framing**: cada mensagem é `4 bytes (big-endian)` com o **tamanho do JSON** seguido do **JSON UTF-8**.
- Uma **requisição** gera **uma resposta**.

## Envelope de requisição
```json
{
  "tool": "search_cars",
  "args": {
    "marca": "Jeep",
    "modelo": "Ren",
    "ano_min": 2020,
    "ano_max": 2024,
    "tipo_combustivel": "Etanol",
    "preco_max": 120000
  }
}

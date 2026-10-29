"""Expresiones regulares asociadas con los tokens del lenguaje."""
from .lexer import TOKEN_SPECS


def listar_expresiones() -> list[dict[str, str]]:
    return [
        {
            "token": item["token"],
            "regex": item["regex"],
            "descripcion": item["descripcion"],
        }
        for item in TOKEN_SPECS
    ]

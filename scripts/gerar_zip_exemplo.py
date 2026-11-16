"""Gera exemplos/loja_virtual.zip a partir da pasta exemplos/loja_virtual.

Uso:
    python scripts/gerar_zip_exemplo.py
"""

from pathlib import Path
import zipfile

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "exemplos" / "loja_virtual"
DESTINO = RAIZ / "exemplos" / "loja_virtual.zip"


def gerar(origem: Path = ORIGEM, destino: Path = DESTINO) -> Path:
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in sorted(origem.rglob("*")):
            if arquivo.is_file() and "__pycache__" not in arquivo.parts:
                zf.write(arquivo, Path("loja_virtual") / arquivo.relative_to(origem))
    return destino


if __name__ == "__main__":
    print(f"Gerado: {gerar()}")

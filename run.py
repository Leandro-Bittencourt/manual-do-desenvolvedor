"""Ponto de entrada da aplicação Manual do Desenvolvedor.

Uso local:
    python run.py
Depois, abra http://127.0.0.1:5000 no navegador.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("MANUAL_HOST", "127.0.0.1")
    porta = int(os.environ.get("MANUAL_PORTA", "5000"))
    debug = os.environ.get("MANUAL_DEBUG", "0") == "1"
    app.run(host=host, port=porta, debug=debug)

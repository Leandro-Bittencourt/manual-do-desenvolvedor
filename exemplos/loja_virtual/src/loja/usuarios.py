import hashlib
import re


class CadastroUsuarios:
    """Mantém os usuários da loja."""

    def __init__(self):
        self.usuarios = {}

    # @traces RF-01
    def cadastrar(self, nome, email, senha):
        if not validar_email(email):
            raise ValueError("E-mail inválido")
        if email in self.usuarios:
            raise ValueError("E-mail já cadastrado")
        self.usuarios[email] = {"nome": nome, "senha_hash": gerar_hash_senha(senha)}
        return self.usuarios[email]

    def autenticar(self, email, senha):
        """Confere o e-mail e a senha informados na entrada do usuário."""
        usuario = self.usuarios.get(email)
        if usuario is None:
            return False
        return verificar_senha(senha, usuario["senha_hash"])


def validar_email(email):
    """Valida o formato do e-mail."""
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def gerar_hash_senha(senha):
    """Gera o hash da senha para que ela não seja armazenada em texto puro."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def verificar_senha(senha, senha_hash):
    return gerar_hash_senha(senha) == senha_hash

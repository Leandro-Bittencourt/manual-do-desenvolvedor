CUPONS = {"DESCONTO10": 0.10, "METADE": 0.50}


class Carrinho:
    def __init__(self):
        self.itens = {}

    def adicionar(self, produto, preco, quantidade=1):
        """Adiciona o produto ao carrinho com a quantidade informada."""
        if quantidade <= 0:
            raise ValueError("Quantidade inválida")
        atual = self.itens.get(produto, {"preco": preco, "quantidade": 0})
        atual["quantidade"] += quantidade
        self.itens[produto] = atual

    def remover(self, produto):
        """Remove o produto do carrinho."""
        self.itens.pop(produto, None)

    def calcular_total(self, cupom=None):
        """Implementa RF-04: soma os produtos e aplica o cupom."""
        subtotal = sum(item["preco"] * item["quantidade"] for item in self.itens.values())
        return aplicar_desconto(subtotal, cupom)


def aplicar_desconto(valor, cupom):
    if not cupom:
        return round(valor, 2)
    percentual = CUPONS[cupom]
    return round(valor * (1 - percentual), 2)

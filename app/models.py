"""Modelo de dados (SQLite), baseado no metamodelo da Figura 2 do TCC.

* ``Projeto`` e ``Versao``   -> modelo de contexto (cada envio de ZIP é uma versão);
* ``Elemento``               -> elemento rastreável (requisito, teste ou código);
* ``Vinculo``                -> vínculo de rastreabilidade;
* ``Evidencia``              -> regra de rastreabilidade que originou o vínculo;
* ``Decisao``                -> decisões do desenvolvedor, preservadas entre versões
                                (modelo de monitoramento: vínculos "a revisar").

Do código-fonte, apenas referências são guardadas (arquivo, linhas e hash).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)

    projetos = db.relationship("Projeto", back_populates="usuario", cascade="all, delete-orphan",
                               order_by="Projeto.criado_em.desc()")

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)


class Projeto(db.Model):
    __tablename__ = "projetos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    nome = db.Column(db.String(160), nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), default=_agora)

    usuario = db.relationship("Usuario", back_populates="projetos")
    versoes = db.relationship("Versao", back_populates="projeto", cascade="all, delete-orphan",
                              order_by="Versao.numero")
    decisoes = db.relationship("Decisao", back_populates="projeto", cascade="all, delete-orphan")

    @property
    def versao_atual(self) -> Versao | None:
        return self.versoes[-1] if self.versoes else None


class Versao(db.Model):
    __tablename__ = "versoes"

    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id"), nullable=False, index=True)
    numero = db.Column(db.Integer, nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    enviado_em = db.Column(db.DateTime(timezone=True), default=_agora)
    metricas_json = db.Column(db.Text, default="{}")
    avisos_json = db.Column(db.Text, default="[]")

    projeto = db.relationship("Projeto", back_populates="versoes")
    elementos = db.relationship("Elemento", back_populates="versao", cascade="all, delete-orphan")
    vinculos = db.relationship("Vinculo", back_populates="versao", cascade="all, delete-orphan")
    dependencias = db.relationship("Dependencia", back_populates="versao", cascade="all, delete-orphan")

    @property
    def metricas(self) -> dict:
        return json.loads(self.metricas_json or "{}")

    @property
    def avisos(self) -> list[str]:
        return json.loads(self.avisos_json or "[]")


class Elemento(db.Model):
    __tablename__ = "elementos"

    id = db.Column(db.Integer, primary_key=True)
    versao_id = db.Column(db.Integer, db.ForeignKey("versoes.id"), nullable=False, index=True)
    tipo = db.Column(db.String(20), nullable=False, index=True)  # requisito, teste, funcao, classe, metodo
    chave = db.Column(db.String(500), nullable=False)
    identificador = db.Column(db.String(300), nullable=False)
    nome = db.Column(db.String(300), nullable=False, default="")
    descricao = db.Column(db.Text, default="")  # apenas para requisitos
    arquivo = db.Column(db.String(500), default="")
    linha_inicio = db.Column(db.Integer)
    linha_fim = db.Column(db.Integer)
    hash = db.Column(db.String(64), default="")

    versao = db.relationship("Versao", back_populates="elementos")

    __table_args__ = (db.UniqueConstraint("versao_id", "chave", name="uq_elemento_versao_chave"),)

    @property
    def eh_requisito(self) -> bool:
        return self.tipo == "requisito"

    @property
    def eh_teste(self) -> bool:
        return self.tipo == "teste"

    @property
    def eh_codigo(self) -> bool:
        return self.tipo in {"funcao", "classe", "metodo", "interface"}

    @property
    def localizacao(self) -> str:
        if not self.arquivo:
            return ""
        if self.linha_inicio and self.linha_fim and self.linha_fim != self.linha_inicio:
            return f"{self.arquivo}, linhas {self.linha_inicio}–{self.linha_fim}"
        if self.linha_inicio:
            return f"{self.arquivo}, linha {self.linha_inicio}"
        return self.arquivo


class Dependencia(db.Model):
    """Aresta do grafo de chamadas entre elementos de produção."""

    __tablename__ = "dependencias"

    id = db.Column(db.Integer, primary_key=True)
    versao_id = db.Column(db.Integer, db.ForeignKey("versoes.id"), nullable=False, index=True)
    origem_id = db.Column(db.Integer, db.ForeignKey("elementos.id"), nullable=False)
    destino_id = db.Column(db.Integer, db.ForeignKey("elementos.id"), nullable=False)

    versao = db.relationship("Versao", back_populates="dependencias")
    origem = db.relationship("Elemento", foreign_keys=[origem_id])
    destino = db.relationship("Elemento", foreign_keys=[destino_id])


class Vinculo(db.Model):
    __tablename__ = "vinculos"

    STATUS = ("sugerido", "confirmado", "rejeitado", "a_revisar")

    id = db.Column(db.Integer, primary_key=True)
    versao_id = db.Column(db.Integer, db.ForeignKey("versoes.id"), nullable=False, index=True)
    origem_id = db.Column(db.Integer, db.ForeignKey("elementos.id"), nullable=False, index=True)
    destino_id = db.Column(db.Integer, db.ForeignKey("elementos.id"), nullable=False, index=True)
    confianca = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="sugerido", index=True)

    versao = db.relationship("Versao", back_populates="vinculos")
    origem = db.relationship("Elemento", foreign_keys=[origem_id])
    destino = db.relationship("Elemento", foreign_keys=[destino_id])
    evidencias = db.relationship("Evidencia", back_populates="vinculo", cascade="all, delete-orphan",
                                 order_by="Evidencia.estrategia")

    @property
    def ativo(self) -> bool:
        return self.status != "rejeitado"

    @property
    def estrategias(self) -> list[str]:
        return sorted({e.estrategia for e in self.evidencias})


class Evidencia(db.Model):
    __tablename__ = "evidencias"

    id = db.Column(db.Integer, primary_key=True)
    vinculo_id = db.Column(db.Integer, db.ForeignKey("vinculos.id"), nullable=False, index=True)
    estrategia = db.Column(db.String(10), nullable=False)  # E1, E2, E3, E4 ou REV
    pontuacao = db.Column(db.Float, nullable=False)
    detalhe = db.Column(db.Text, nullable=False)

    vinculo = db.relationship("Vinculo", back_populates="evidencias")


class Decisao(db.Model):
    """Confirmação ou rejeição feita pelo desenvolvedor (vale para versões futuras)."""

    __tablename__ = "decisoes"

    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id"), nullable=False, index=True)
    origem_chave = db.Column(db.String(500), nullable=False)
    destino_chave = db.Column(db.String(500), nullable=False)
    decisao = db.Column(db.String(20), nullable=False)  # confirmado ou rejeitado
    hash_origem = db.Column(db.String(64), default="")
    hash_destino = db.Column(db.String(64), default="")
    atualizado_em = db.Column(db.DateTime(timezone=True), default=_agora, onupdate=_agora)

    projeto = db.relationship("Projeto", back_populates="decisoes")

    __table_args__ = (
        db.UniqueConstraint("projeto_id", "origem_chave", "destino_chave", name="uq_decisao_par"),
    )

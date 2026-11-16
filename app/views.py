"""Telas da aplicação (Quadro 6 do TCC): painel, envio de projeto,
requisitos, código, testes, revisão de vínculos e localização de erros."""

from __future__ import annotations

from collections import OrderedDict

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    json,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from . import services
from .analysis.confianca import faixa as calcular_faixa
from .analysis.extrator import ErroExtracao
from .extensions import db
from .models import Elemento, Projeto, Vinculo

bp = Blueprint("main", __name__)


def _projeto_do_usuario(projeto_id: int) -> Projeto:
    projeto = Projeto.query.filter_by(id=projeto_id, usuario_id=current_user.id).first()
    if projeto is None:
        abort(404)
    return projeto


def _versao(projeto: Projeto):
    versao = projeto.versao_atual
    if versao is None:
        abort(404)
    return versao


def _arquivo_zip_enviado():
    arquivo = request.files.get("arquivo")
    if arquivo is None or not arquivo.filename:
        return None, "Selecione o arquivo .zip do projeto."
    if not arquivo.filename.lower().endswith(".zip"):
        return None, "O arquivo precisa estar no formato .zip."
    return arquivo, None


@bp.route("/")
def inicio():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))
    return redirect(url_for("auth.entrar"))


@bp.route("/painel")
@login_required
def painel():
    linhas = [{"projeto": p, "resumo": services.resumo(p.versao_atual)} for p in current_user.projetos]
    return render_template("painel.html", linhas=linhas)


@bp.route("/projetos/novo", methods=["GET", "POST"])
@login_required
def novo_projeto():
    erro = None
    nome = ""
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        arquivo, erro = _arquivo_zip_enviado()
        if not erro and not nome:
            nome = services.nome_seguro(arquivo.filename).rsplit(".", 1)[0]
        if not erro:
            try:
                resultado = services.analisar_arquivo_enviado(arquivo)
            except ErroExtracao as falha:
                erro = str(falha)
            else:
                projeto = services.criar_projeto(
                    current_user._get_current_object(), nome[:160], resultado, services.nome_seguro(arquivo.filename)
                )
                flash("Projeto analisado com sucesso.", "sucesso")
                return redirect(url_for("main.visao_geral", projeto_id=projeto.id))
    return render_template("projeto_novo.html", erro=erro, nome=nome)


@bp.route("/projetos/<int:projeto_id>")
@login_required
def visao_geral(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    return render_template(
        "projeto/visao_geral.html", projeto=projeto, versao=versao,
        resumo=services.resumo(versao), aba="visao",
    )


@bp.route("/projetos/<int:projeto_id>/versoes", methods=["POST"])
@login_required
def nova_versao(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    arquivo, erro = _arquivo_zip_enviado()
    if not erro:
        try:
            resultado = services.analisar_arquivo_enviado(arquivo)
        except ErroExtracao as falha:
            erro = str(falha)
        else:
            versao = services.salvar_versao(projeto, resultado, services.nome_seguro(arquivo.filename))
            db.session.commit()
            revisar = sum(1 for v in versao.vinculos if v.status == "a_revisar")
            mensagem = f"Versão {versao.numero} analisada."
            if revisar:
                mensagem += f" {revisar} vínculo(s) confirmado(s) antes precisam ser revisados, pois o código mudou."
            flash(mensagem, "sucesso")
    if erro:
        flash(erro, "erro")
    return redirect(url_for("main.visao_geral", projeto_id=projeto.id))


@bp.route("/projetos/<int:projeto_id>/excluir", methods=["POST"])
@login_required
def excluir_projeto(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    nome = projeto.nome
    db.session.delete(projeto)
    db.session.commit()
    flash(f"O projeto \"{nome}\" e todos os seus dados foram excluídos.", "sucesso")
    return redirect(url_for("main.painel"))


@bp.route("/projetos/<int:projeto_id>/requisitos")
@login_required
def requisitos(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    filtro = request.args.get("filtro", "todos")
    linhas = services.cobertura(versao)
    if filtro == "sem_codigo":
        linhas = [l for l in linhas if not l["codigo"]]
    elif filtro == "sem_teste":
        linhas = [l for l in linhas if not l["testes"]]
    return render_template("projeto/requisitos.html", projeto=projeto, versao=versao,
                           linhas=linhas, filtro=filtro, aba="requisitos")


@bp.route("/projetos/<int:projeto_id>/elementos/<int:elemento_id>")
@login_required
def elemento(projeto_id: int, elemento_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    item = Elemento.query.filter_by(id=elemento_id, versao_id=versao.id).first_or_404()
    vinculos = (
        Vinculo.query.filter(
            Vinculo.versao_id == versao.id,
            (Vinculo.origem_id == item.id) | (Vinculo.destino_id == item.id),
        )
        .order_by(Vinculo.confianca.desc())
        .all()
    )
    return render_template("projeto/elemento.html", projeto=projeto, versao=versao, item=item,
                           vinculos=vinculos, aba="requisitos" if item.eh_requisito else
                           ("testes" if item.eh_teste else "codigo"))


@bp.route("/projetos/<int:projeto_id>/codigo")
@login_required
def codigo(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    _, por_destino = services.mapa_de_vinculos(versao)
    arquivos: OrderedDict[str, list] = OrderedDict()
    for e in services.elementos_por_tipo(versao, "classe", "funcao", "metodo", "interface"):
        vinculos = por_destino.get(e.id, [])
        arquivos.setdefault(e.arquivo, []).append(
            {
                "elemento": e,
                "requisitos": [v for v in vinculos if v.origem.eh_requisito],
                "testes": [v for v in vinculos if v.origem.eh_teste],
            }
        )
    return render_template("projeto/codigo.html", projeto=projeto, versao=versao, arquivos=arquivos, aba="codigo")


@bp.route("/projetos/<int:projeto_id>/testes")
@login_required
def testes(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    por_origem, por_destino = services.mapa_de_vinculos(versao)
    linhas = [
        {
            "teste": t,
            "requisitos": [v for v in por_destino.get(t.id, []) if v.origem.eh_requisito],
            "codigo": [v for v in por_origem.get(t.id, []) if v.destino.eh_codigo],
        }
        for t in services.elementos_por_tipo(versao, "teste")
    ]
    return render_template("projeto/testes.html", projeto=projeto, versao=versao, linhas=linhas, aba="testes")


@bp.route("/projetos/<int:projeto_id>/revisao")
@login_required
def revisao(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    situacao = request.args.get("situacao", "pendentes")
    faixa_escolhida = request.args.get("faixa", "todas")

    consulta = Vinculo.query.filter(Vinculo.versao_id == versao.id)
    if situacao == "pendentes":
        consulta = consulta.filter(Vinculo.status.in_(["sugerido", "a_revisar"]))
    elif situacao in Vinculo.STATUS:
        consulta = consulta.filter(Vinculo.status == situacao)
    vinculos = consulta.all()

    if faixa_escolhida in {"alta", "media", "baixa"}:
        limites = current_app.config["ANALISE_FAIXAS"]
        vinculos = [v for v in vinculos if calcular_faixa(v.confianca, limites) == faixa_escolhida]
    vinculos.sort(key=lambda v: (v.status != "a_revisar", -v.confianca))
    return render_template("projeto/revisao.html", projeto=projeto, versao=versao, vinculos=vinculos,
                           situacao=situacao, faixa_escolhida=faixa_escolhida, aba="revisao")


@bp.route("/projetos/<int:projeto_id>/vinculos/<int:vinculo_id>/decisao", methods=["POST"])
@login_required
def decidir(projeto_id: int, vinculo_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    vinculo = Vinculo.query.filter_by(id=vinculo_id, versao_id=versao.id).first_or_404()
    acao = request.form.get("acao")
    decisao = {"confirmar": "confirmado", "rejeitar": "rejeitado"}.get(acao)
    if decisao is None:
        abort(400, description="Ação inválida.")
    services.registrar_decisao(vinculo, decisao)
    destino = request.form.get("voltar", "")
    if not destino.startswith("/") or destino.startswith("//"):
        destino = url_for("main.revisao", projeto_id=projeto.id)
    return redirect(destino)


@bp.route("/projetos/<int:projeto_id>/localizar", methods=["GET", "POST"])
@login_required
def localizar(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    texto = ""
    resultado = None
    if request.method == "POST":
        texto = request.form.get("erro", "")[:20000]
        if texto.strip():
            resultado = services.localizar_erro(versao, texto)
        else:
            flash("Cole a mensagem de erro, o traceback ou o nome do teste que falhou.", "aviso")
    return render_template("projeto/localizar.html", projeto=projeto, versao=versao, texto=texto,
                           resultado=resultado, aba="localizar")


@bp.route("/projetos/<int:projeto_id>/exportar.json")
@login_required
def exportar(projeto_id: int):
    projeto = _projeto_do_usuario(projeto_id)
    versao = _versao(projeto)
    conteudo = json.dumps(services.exportar(versao), ensure_ascii=False, indent=2)
    nome = f"rastreabilidade-projeto{projeto.id}-v{versao.numero}.json"
    return Response(conteudo, mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename={nome}"})

"""Dados para a capa da SEMA e para a lavratura dos autos (R4/E4).

Este sistema não gera a capa: organiza os dados, na ordem da capa, para copiar para o sistema da SEMA sem
redigitar. A regra de montagem (formato do texto, "Não informado", o que é opcional) fica aqui; a tela só renderiza.
"""
from app.domain.constantes import ASSUNTO_OUTRO, INTERESSADO_PADRAO
from app.domain.contato import formatar_telefone
from app.domain.coordenadas import formatar_par_gms
from app.domain.documento import formatar_cep, formatar_cpf_cnpj
from app.models import Inspecao
from app.services import empreendimento_service

NAO_INFORMADO = "Não informado"


def _limpo(valor) -> str | None:
    texto = (str(valor) if valor is not None else "").strip()
    return texto or None


def _campo(rotulo: str, valor, opcional: bool = False) -> dict:
    """`faltando` = vazio e obrigatório para a SEMA (destacado na tela); `opcional` vazio só aparece esmaecido."""
    v = _limpo(valor)
    return {
        "rotulo": rotulo,
        "valor": v or NAO_INFORMADO,
        "copiar": v or "",
        "ausente": v is None,
        "faltando": v is None and not opcional,
    }


def _bloco(chave: str, titulo: str, campos: list[dict], linhas: list[str]) -> dict:
    return {"chave": chave, "titulo": titulo, "campos": campos, "texto": "\n".join([f"{titulo}:", *linhas])}


def _municipio_uf(municipio, uf) -> str | None:
    m, u = _limpo(municipio), _limpo(uf)
    return f"{m}/{u}" if m and u else m or u


def _juntar(partes, separador: str = ", ") -> str | None:
    return separador.join(p for p in (_limpo(x) for x in partes) if p) or None


def _endereco_empreendimento(e: dict) -> str | None:
    return _juntar([e.get("logradouro"), _municipio_uf(e.get("municipio"), e.get("uf"))])


def _endereco_correspondencia(p: dict) -> str | None:
    endereco = _juntar([
        p.get("corr_logradouro"), p.get("corr_numero"), p.get("corr_complemento"), p.get("corr_bairro"),
        _municipio_uf(p.get("corr_municipio"), p.get("corr_uf")),
    ])
    cep = formatar_cep(_limpo(p.get("corr_cep")))
    return _juntar([endereco, f"CEP {cep}" if cep else None], " – ")


def _rotulo_documento(digitos: str | None) -> str:
    return "CPF" if digitos and len(digitos) == 11 else "CNPJ" if digitos and len(digitos) == 14 else "CPF/CNPJ"


def _ordinal(rotulo: str, i: int, total: int) -> str:
    return f"{rotulo} {i + 1}" if total > 1 else rotulo


def _interessado(i: Inspecao, protocolo: str | None) -> dict:
    orgao, unidade = _limpo(i.interessado_orgao), _limpo(i.interessado_unidade)
    comarca, requerente = _limpo(i.interessado_comarca), _limpo(i.interessado_requerente)
    linha_protocolo = f"Protocolo nº {protocolo}" if protocolo else f"Protocolo nº: {NAO_INFORMADO}"
    if not any((orgao, unidade, comarca, requerente)):  # demanda interna: nada a faltar
        campos = [_campo("Interessado", INTERESSADO_PADRAO), _campo("Protocolo nº", protocolo)]
        return _bloco("interessado", "1 – Interessado", campos, [INTERESSADO_PADRAO, linha_protocolo])
    campos = [
        _campo("Órgão / entidade", orgao), _campo("Unidade", unidade), _campo("Comarca", comarca, opcional=True),
        _campo("Protocolo nº", protocolo), _campo("Requerente", requerente),
    ]
    linhas = [_juntar([orgao, unidade], " - ") or NAO_INFORMADO]
    if comarca:
        linhas.append(comarca)
    linhas += [linha_protocolo, f"Requerente: {requerente or NAO_INFORMADO}"]
    return _bloco("interessado", "1 – Interessado", campos, linhas)


def _assunto(i: Inspecao) -> dict:
    tipo = _limpo(i.assunto_tipo)
    assunto = _limpo(i.assunto_outro) if tipo == ASSUNTO_OUTRO else tipo
    campos = [_campo("Assunto", assunto), _campo("Objetivo", i.objetivo)]
    linhas = [assunto or NAO_INFORMADO, f"Objetivo: {_limpo(i.objetivo) or NAO_INFORMADO}"]
    return _bloco("assunto", "2 – Assunto", campos, linhas)


def _caracterizacao(e: dict) -> dict:
    campos = [_campo("Nome fantasia / denominação", e.get("nome"))]
    linhas = [f"Nome fantasia: {_limpo(e.get('nome')) or NAO_INFORMADO}"]
    responsaveis = e.get("proprietarios") or []
    if not responsaveis:
        campos += [_campo("Responsável (nome / razão social)", None), _campo("CPF/CNPJ", None)]
        linhas += [f"Responsável: {NAO_INFORMADO}", f"CPF/CNPJ: {NAO_INFORMADO}"]
    for k, p in enumerate(responsaveis):
        doc = _limpo(p.get("cpf_cnpj"))
        campos += [
            _campo(_ordinal("Responsável", k, len(responsaveis)) + " – nome / razão social", p.get("nome")),
            _campo(_ordinal("Responsável", k, len(responsaveis)) + " – CPF/CNPJ", formatar_cpf_cnpj(doc)),
        ]
        linhas += [
            f"{_ordinal('Responsável', k, len(responsaveis))}: {_limpo(p.get('nome')) or NAO_INFORMADO}",
            f"{_rotulo_documento(doc)}: {formatar_cpf_cnpj(doc) or NAO_INFORMADO}",
        ]
    car = _limpo(e.get("numero_car"))
    coordenadas = formatar_par_gms(e["latitude"], e["longitude"]) if e.get("latitude") is not None else None
    endereco, cep = _endereco_empreendimento(e), formatar_cep(_limpo(e.get("cep")))
    campos += [
        _campo("CAR", car), _campo("Coordenadas", coordenadas), _campo("Endereço do empreendimento", endereco), _campo("CEP", cep),
    ]
    linhas += [
        f"CAR: {car or NAO_INFORMADO}", f"Coordenadas: {coordenadas or NAO_INFORMADO}",
        f"Endereço: {endereco or NAO_INFORMADO}", f"CEP: {cep or NAO_INFORMADO}",
    ]
    return _bloco("empreendimento", "3 – Caracterização do empreendimento", campos, linhas)


def _equipe(i: Inspecao) -> dict:
    if not i.equipe:
        return _bloco("equipe", "4 – Equipe técnica", [_campo("Equipe técnica", None)], [NAO_INFORMADO])
    campos, linhas = [], []
    for k, m in enumerate(i.equipe):
        linha = _juntar([m.nome, m.cargo, m.orgao], " – ")
        campos.append(_campo(f"Membro {k + 1}", linha))
        linhas.append(linha or NAO_INFORMADO)
    return _bloco("equipe", "4 – Equipe técnica", campos, linhas)


def _atos(i: Inspecao, e: dict, protocolo: str | None) -> dict:
    campos, linhas = [], []
    if not i.atos:
        linhas.append("Nenhum ato informado.")
    for k, a in enumerate(i.atos):
        numero = _limpo(a.numero)
        campos.append(_campo(f"Ato {k + 1}", f"{a.tipo} – {numero}" if numero else f"{a.tipo} – nº a definir"))
        linhas.append(f"Ato {k + 1}: {a.tipo} ({'nº ' + numero if numero else 'nº a definir'})")
    coordenadas = formatar_par_gms(e["latitude"], e["longitude"]) if e.get("latitude") is not None else None
    car = _limpo(e.get("numero_car"))
    campos += [
        _campo("Protocolo nº", protocolo), _campo("Empreendimento", e.get("nome")), _campo("Coordenadas", coordenadas), _campo("CAR", car),
    ]
    linhas += [
        f"Protocolo nº: {protocolo or NAO_INFORMADO}", f"Empreendimento: {_limpo(e.get('nome')) or NAO_INFORMADO}",
        f"Coordenadas: {coordenadas or NAO_INFORMADO}", f"CAR: {car or NAO_INFORMADO}",
    ]
    responsaveis = e.get("proprietarios") or []
    if not responsaveis:
        campos.append(_campo("Responsável (nome / razão social)", None))
        linhas.append(f"Responsável: {NAO_INFORMADO}")
    for k, p in enumerate(responsaveis):
        r = _ordinal("Responsável", k, len(responsaveis))
        doc = _limpo(p.get("cpf_cnpj"))
        telefone = formatar_telefone(_limpo(p.get("telefone")))  # o instantâneo guarda só os dígitos
        correspondencia = _endereco_correspondencia(p)
        campos += [
            _campo(f"{r} – nome / razão social", p.get("nome")), _campo(f"{r} – CPF/CNPJ", formatar_cpf_cnpj(doc)),
            _campo(f"{r} – telefone", telefone), _campo(f"{r} – endereço para correspondência", correspondencia),
        ]
        linhas += [
            f"{r}: {_limpo(p.get('nome')) or NAO_INFORMADO}",
            f"{_rotulo_documento(doc)}: {formatar_cpf_cnpj(doc) or NAO_INFORMADO}",
            f"Telefone: {telefone or NAO_INFORMADO}",
            f"Endereço para correspondência: {correspondencia or NAO_INFORMADO}",
        ]
    return _bloco("atos", "Atos a lavrar", campos, linhas)


def montar(inspecao: Inspecao) -> dict:
    """Blocos na ordem da capa (1 a 4) mais "Atos a lavrar", cada um com o texto pronto e o texto completo."""
    e = empreendimento_service.da_inspecao(inspecao)
    protocolo = _limpo(inspecao.numero_processo)
    blocos = [
        _interessado(inspecao, protocolo), _assunto(inspecao), _caracterizacao(e), _equipe(inspecao),
        _atos(inspecao, e, protocolo),
    ]
    return {
        "codigo": inspecao.codigo,
        "protocolo": protocolo,
        "blocos": blocos,
        "texto_completo": "\n\n".join(b["texto"] for b in blocos),
        "campos_faltando": sum(1 for b in blocos for c in b["campos"] if c["faltando"]),
    }

"""Dados fictícios de exemplo (seção 12 do handoff). Nenhum dado real."""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.domain.constantes import Origem, Situacao, Status
from app.domain.resultado import calcular_resultado
from app.models import Inspecao, ItemInspecao, Local, Proprietario
from app.seed.modelo import garantir_modelo
from app.services import empreendimento_service, numeracao_service

LOCAIS = [
    ("Fazenda Horizonte Azul", "Vila Nova do Cerrado", "Propriedade rural", -10.42318, -58.71264),
    ("Serraria Ipê Dourado", "Porto das Águas", "Indústria madeireira", -11.21456, -58.30977),
    ("Posto Rio Claro", "São Tomé do Norte", "Posto de combustíveis", -9.71234, -58.12845),
    ("Reserva Mata Ciliar Beta", "Campo Verde do Sul", "Área de preservação", -10.91507, -59.46288),
]

# Dados 100% fictícios (LGPD): CAR de mentira e proprietários inventados, telefones (65) 90000-000N.
CAR_EXEMPLO = ["MT-5107925-00000000000000000000000000000001", None, None, "MT-5107925-00000000000000000000000000000004"]
PROPRIETARIOS_EXEMPLO = [
    [("Proprietário Fictício Um", "65900000001"), ("Proprietária Fictícia Dois", "65900000002")],
    [("Madeireira Fictícia Ltda.", "65900000003")],
    [],
    [("Proprietário Fictício Quatro", None)],
]

OBS_VISTORIA = {
    1: "Propriedade em boas condições gerais. Documentação apresentada pelo responsável fictício no ato da vistoria. Sem pendências visíveis.",
    2: "Pátio com acúmulo moderado de serragem junto ao galpão. Placas de segurança parcialmente desgastadas. Registro de manejo com atualização atrasada.",
    3: "Odor de combustível na área de descarga. Caixa separadora de efluentes com sinais de transbordamento. Responsável ausente no horário da vistoria.",
    4: "Acesso pela estrada vicinal em bom estado. Nascente delimitada com cerca; vegetação ciliar preservada no trecho norte. Trecho sul ainda não percorrido.",
    5: None,
}

OBS_ITEM_NC = {
    (2, 4): "Placas de segurança com tinta desgastada na entrada do galpão.",
    (2, 5): "Último registro de manejo datado de meses antes da vistoria.",
    (3, 6): "Caixa separadora com sinais de transbordamento e resíduo oleoso no solo.",
}

CONFORME = Situacao.CONFORME
NC = Situacao.NAO_CONFORME

# (numero, indice do local, agendamento, realizacao, status, {ordem do item: situacao})
INSPECOES = [
    (1, 0, date(2026, 10, 5), date(2026, 10, 6), Status.FINALIZADA, {i: CONFORME for i in range(1, 7)}),
    (2, 1, date(2026, 10, 13), date(2026, 10, 13), Status.FINALIZADA,
     {1: CONFORME, 2: CONFORME, 3: CONFORME, 4: NC, 5: NC, 6: CONFORME}),
    (3, 2, date(2026, 10, 14), date(2026, 10, 15), Status.FINALIZADA,
     {1: CONFORME, 2: CONFORME, 3: CONFORME, 4: CONFORME, 5: CONFORME, 6: NC}),
    (4, 3, date(2026, 10, 20), date(2026, 10, 20), Status.EM_ANDAMENTO,
     {1: CONFORME, 2: CONFORME, 3: CONFORME}),
    (5, 0, date(2026, 10, 28), None, Status.ABERTA, {}),
]


def banco_povoado(db: Session) -> bool:
    # O modelo de checklist é configuração fixa (criada na inicialização) e não conta como dado.
    return any(db.query(m).first() is not None for m in (Local, Inspecao))


def carregar(db: Session) -> list[Inspecao]:
    """Insere locais, modelo e 5 inspeções, gravando o estado final de cada exemplo."""
    locais = [
        Local(
            nome=n, municipio=m, tipo=t, latitude=la, longitude=lo, ativo=True, numero_car=CAR_EXEMPLO[k],
            proprietarios=[
                Proprietario(nome=nome, telefone=tel, ordem=ordem)
                for ordem, (nome, tel) in enumerate(PROPRIETARIOS_EXEMPLO[k])
            ],
        )
        for k, (n, m, t, la, lo) in enumerate(LOCAIS)
    ]
    modelo = garantir_modelo(db)
    db.add_all(locais)
    db.flush()

    criadas = []
    for numero, idx_local, agend, real, status, situacoes in INSPECOES:
        criado = datetime.combine(agend, datetime.min.time()).replace(hour=8)
        insp = Inspecao(
            codigo=f"INS-{numero:03d}",
            numero_processo=f"SEMA-PRO-2026/{10000 + numero}",
            local_id=locais[idx_local].id,
            objetivo="Vistoria de rotina (exemplo fictício)",
            observacoes_vistoria=OBS_VISTORIA[numero],
            data_agendamento=agend,
            data_realizacao=real,
            status=status,
            criado_em=criado,
            atualizado_em=criado,
        )
        for m in modelo:
            insp.itens.append(
                ItemInspecao(
                    modelo_item_id=m.id, descricao=m.descricao, critico=m.critico, origem=Origem.MODELO,
                    ordem=m.ordem, situacao=situacoes.get(m.ordem, Situacao.NAO_RESPONDIDO),
                    observacao=OBS_ITEM_NC.get((numero, m.ordem)),
                )
            )
        if status == Status.FINALIZADA:
            insp.resultado = calcular_resultado(insp.itens)
            insp.fechado_em = datetime.combine(real, datetime.min.time()).replace(hour=17)
            insp.local = locais[idx_local]
            empreendimento_service.copiar_no_fechamento(insp)
            numeracao_service.atribuir_numero(db, insp, real.year)
        db.add(insp)
        criadas.append(insp)
    db.flush()
    return criadas

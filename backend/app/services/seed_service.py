from sqlalchemy.orm import Session

from app import clock
from app.domain import imagem
from app.errors import ErroNegocio
from app.models import FotoVistoria
from app.seed import dados_exemplo, fotos_exemplo
from app.storage.arquivos import ArmazenamentoArquivos


def carregar_exemplos(db: Session, storage: ArmazenamentoArquivos) -> dict:
    if dados_exemplo.banco_povoado(db):
        raise ErroNegocio("BANCO_JA_POVOADO", "O banco já contém dados; exemplos não foram carregados.", 409)
    gravados: list[str] = []
    try:
        inspecoes = {i.codigo: i for i in dados_exemplo.carregar(db)}
        contagem: dict[str, int] = {}
        for numero, ordem_item, anotacao in fotos_exemplo.FOTOS:
            insp = inspecoes[f"INS-{numero:03d}"]
            contagem[insp.codigo] = n = contagem.get(insp.codigo, 0) + 1
            p = imagem.processar(fotos_exemplo.gerar_imagem(numero, n))
            orig = storage.salvar(insp.id, "original", p.extensao, p.original)
            gravados.append(orig)
            mini = storage.salvar(insp.id, "miniatura", p.extensao, p.miniatura)
            gravados.append(mini)
            item = next((i for i in insp.itens if i.ordem == ordem_item), None) if ordem_item else None
            db.add(FotoVistoria(
                inspecao_id=insp.id, item_inspecao_id=item.id if item else None,
                nome_original=f"foto_ficticia_ins{numero:03d}_{n}.jpg", arquivo_path=orig, miniatura_path=mini,
                mime_type=p.mime_type, tamanho_bytes=len(p.original), largura=p.largura, altura=p.altura,
                hash_sha256=p.hash_sha256, legenda=None, anotacao=anotacao, ordem=n, criado_em=clock.agora(),
            ))
        db.commit()
    except Exception:
        db.rollback()
        for c in gravados:
            storage.remover(c)
        raise
    return {"locais": len(dados_exemplo.LOCAIS), "inspecoes": len(inspecoes), "fotos": len(fotos_exemplo.FOTOS)}

from sqlalchemy.orm import Session

from app.models import ModeloItem

MODELO = [
    ("Licença ambiental fictícia apresentada e dentro da validade", True),
    ("Área de preservação delimitada e sem supressão", True),
    ("Armazenamento de resíduos adequado", False),
    ("Sinalização de segurança visível", False),
    ("Registro de manejo/atividade atualizado", False),
    ("Destinação de efluentes regular", True),
]


def garantir_modelo(db: Session) -> list[ModeloItem]:
    """Modelo de checklist fixo (a tela de modelos está fora do escopo). Idempotente."""
    existentes = db.query(ModeloItem).order_by(ModeloItem.ordem).all()
    if existentes:
        return existentes
    itens = [ModeloItem(descricao=d, critico=c, ativo=True, ordem=i) for i, (d, c) in enumerate(MODELO, 1)]
    db.add_all(itens)
    db.commit()
    return itens

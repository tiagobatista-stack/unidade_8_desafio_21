import { useRef, useState, type FormEvent } from "react";
import { paraErro } from "../api/cliente";
import type { Local, NovoLocal } from "../api/tipos";
import { formatarTelefone, segueModeloSicar } from "../utils/formatar";
import { MensagemErro } from "./Basicos";

interface Props {
  /** Local existente (edição) ou nada (cadastro). */
  inicial?: Local;
  rotuloSalvar: string;
  salvar: (dados: NovoLocal) => Promise<Local>;
  onSalvo: (local: Local) => void | Promise<void>;
  onCancelar: () => void;
}

interface LinhaProprietario {
  chave: number;
  nome: string;
  telefone: string;
}

/** Aceita vírgula ou ponto como separador decimal; devolve NaN se não for número. */
const numero = (texto: string) => (texto.trim() === "" ? NaN : Number(texto.trim().replace(",", ".")));
const coordenada = (valor: number | undefined) => (valor === undefined ? "" : String(valor));

export function FormularioLocal({ inicial, rotuloSalvar, salvar, onSalvo, onCancelar }: Props) {
  const proximaChave = useRef(1);
  const novaLinha = (nome = "", telefone = ""): LinhaProprietario => ({ chave: proximaChave.current++, nome, telefone });
  const [campos, setCampos] = useState({
    nome: inicial?.nome ?? "",
    municipio: inicial?.municipio ?? "",
    tipo: inicial?.tipo ?? "",
    latitude: coordenada(inicial?.latitude),
    longitude: coordenada(inicial?.longitude),
    numero_car: inicial?.numero_car ?? "",
  });
  const [linhas, setLinhas] = useState<LinhaProprietario[]>(() =>
    (inicial?.proprietarios ?? []).map((p) => novaLinha(p.nome, p.telefone_formatado ?? p.telefone ?? "")),
  );
  const [tentou, setTentou] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<unknown>(null);

  const mudar = (campo: keyof typeof campos, valor: string) => setCampos((c) => ({ ...c, [campo]: valor }));
  const mudarLinha = (chave: number, parcial: Partial<LinhaProprietario>) =>
    setLinhas((l) => l.map((x) => (x.chave === chave ? { ...x, ...parcial } : x)));

  // Só presença e sintaxe numérica; faixa de MT, DDD e tamanho do telefone são validados pela API.
  const faltando = {
    nome: !campos.nome.trim(),
    municipio: !campos.municipio.trim(),
    tipo: !campos.tipo.trim(),
    latitude: !Number.isFinite(numero(campos.latitude)),
    longitude: !Number.isFinite(numero(campos.longitude)),
  };
  const linhaSemNome = (l: LinhaProprietario) => !l.nome.trim() && l.telefone.trim() !== "";
  const carForaDoModelo = campos.numero_car.trim() !== "" && !segueModeloSicar(campos.numero_car);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setTentou(true);
    setErro(null);
    if (Object.values(faltando).some(Boolean) || linhas.some(linhaSemNome)) return;
    setEnviando(true);
    try {
      const local = await salvar({
        nome: campos.nome,
        municipio: campos.municipio,
        tipo: campos.tipo,
        latitude: numero(campos.latitude),
        longitude: numero(campos.longitude),
        numero_car: campos.numero_car.trim() || null,
        proprietarios: linhas
          .filter((l) => l.nome.trim() || l.telefone.trim())
          .map((l) => ({ nome: l.nome, telefone: l.telefone.trim() || null })),
      });
      await onSalvo(local);
    } catch (e2) {
      setErro(paraErro(e2));
    } finally {
      setEnviando(false);
    }
  }

  const aviso = (campo: keyof typeof faltando, texto: string) =>
    tentou && faltando[campo] ? <span className="campo-erro">{texto}</span> : null;

  return (
    <form onSubmit={enviar} noValidate className="formulario">
      <label htmlFor="local-nome">
        Nome *
        <input id="local-nome" name="local-nome" aria-label="Nome do local" value={campos.nome} onChange={(e) => mudar("nome", e.target.value)} />
        {aviso("nome", "Informe o nome.")}
      </label>
      <label htmlFor="local-municipio">
        Município *
        <input id="local-municipio" name="local-municipio" aria-label="Município do local" value={campos.municipio} onChange={(e) => mudar("municipio", e.target.value)} />
        {aviso("municipio", "Informe o município.")}
      </label>
      <label htmlFor="local-tipo">
        Tipo *
        <input id="local-tipo" name="local-tipo" aria-label="Tipo do local" placeholder="Ex.: Propriedade rural" value={campos.tipo} onChange={(e) => mudar("tipo", e.target.value)} />
        {aviso("tipo", "Informe o tipo.")}
      </label>
      <div className="duas-colunas">
        <label htmlFor="local-latitude">
          Latitude *
          <input id="local-latitude" name="local-latitude" aria-label="Latitude do local" inputMode="decimal" placeholder="-10.42318" value={campos.latitude} onChange={(e) => mudar("latitude", e.target.value)} />
          {aviso("latitude", "Informe um número.")}
        </label>
        <label htmlFor="local-longitude">
          Longitude *
          <input id="local-longitude" name="local-longitude" aria-label="Longitude do local" inputMode="decimal" placeholder="-58.71264" value={campos.longitude} onChange={(e) => mudar("longitude", e.target.value)} />
          {aviso("longitude", "Informe um número.")}
        </label>
      </div>
      <p className="dica">Coordenadas devem estar dentro de Mato Grosso (latitude −18,05 a −7,35; longitude −61,65 a −50,20).</p>

      <label htmlFor="local-numero-car">
        Número do CAR (opcional)
        <input
          id="local-numero-car"
          name="local-numero-car"
          aria-label="Número do CAR"
          placeholder="MT-5107925-…"
          value={campos.numero_car}
          onChange={(e) => mudar("numero_car", e.target.value)}
        />
      </label>
      {carForaDoModelo && (
        <p className="dica" data-testid="aviso-car">
          Formato diferente do SICAR (UF-código IBGE-código). Será aceito mesmo assim.
        </p>
      )}

      <fieldset className="proprietarios">
        <legend>Proprietários</legend>
        {linhas.length === 0 && <p className="dica">Nenhum proprietário informado.</p>}
        {linhas.map((l, i) => (
          <div className="linha-proprietario" key={l.chave} data-testid="linha-proprietario">
            <label htmlFor={`local-prop-${l.chave}-nome`}>
              Nome *
              <input
                id={`local-prop-${l.chave}-nome`}
                name={`local-prop-${l.chave}-nome`}
                aria-label={`Nome do proprietário ${i + 1}`}
                value={l.nome}
                onChange={(e) => mudarLinha(l.chave, { nome: e.target.value })}
              />
              {tentou && linhaSemNome(l) && <span className="campo-erro">Informe o nome.</span>}
            </label>
            <label htmlFor={`local-prop-${l.chave}-telefone`}>
              Telefone
              <input
                id={`local-prop-${l.chave}-telefone`}
                name={`local-prop-${l.chave}-telefone`}
                aria-label={`Telefone do proprietário ${i + 1}`}
                inputMode="tel"
                placeholder="(65) 90000-0001"
                value={l.telefone}
                onChange={(e) => mudarLinha(l.chave, { telefone: e.target.value })}
                onBlur={() => mudarLinha(l.chave, { telefone: formatarTelefone(l.telefone) })}
              />
            </label>
            <button type="button" className="secundario" aria-label={`Remover proprietário ${i + 1}`} onClick={() => setLinhas((x) => x.filter((y) => y.chave !== l.chave))}>
              Remover
            </button>
          </div>
        ))}
        <button type="button" className="secundario" onClick={() => setLinhas((l) => [...l, novaLinha()])}>
          + Adicionar proprietário
        </button>
      </fieldset>

      <MensagemErro erro={erro} />
      <div className="acoes">
        <button type="submit" disabled={enviando}>{rotuloSalvar}</button>
        <button type="button" className="secundario" onClick={onCancelar}>Cancelar</button>
      </div>
    </form>
  );
}

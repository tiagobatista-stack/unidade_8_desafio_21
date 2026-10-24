import { useRef, useState, type FormEvent } from "react";
import { paraErro } from "../api/cliente";
import type { Local, NovoLocal, NovoProprietario, Proprietario } from "../api/tipos";
import { formatarTelefone, mascararCep, mascararCpfCnpj, mascararGms, segueModeloSicar } from "../utils/formatar";
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
  cpf_cnpj: string;
  mesmo_endereco: boolean;
  corr_logradouro: string;
  corr_numero: string;
  corr_complemento: string;
  corr_bairro: string;
  corr_municipio: string;
  corr_uf: string;
  corr_cep: string;
}

type ModoCoordenada = "decimal" | "gms";

/** Aceita vírgula ou ponto como separador decimal; devolve NaN se não for número. */
const numero = (texto: string) => (texto.trim() === "" ? NaN : Number(texto.trim().replace(",", ".")));
const coordenada = (valor: number | undefined) => (valor === undefined ? "" : String(valor));
const ou = (texto: string) => texto.trim() || undefined; // vazio não vai no corpo

/** Linha em branco ou a partir de um proprietário já cadastrado. */
function linhaDe(chave: number, p?: Proprietario, local?: Local): LinhaProprietario {
  const igualAoEmpreendimento =
    !!p && !!local?.logradouro && p.corr_logradouro === local.logradouro && p.corr_municipio === local.municipio &&
    p.corr_uf === local.uf && p.corr_cep === local.cep;
  return {
    chave,
    nome: p?.nome ?? "",
    telefone: p?.telefone_formatado ?? p?.telefone ?? "",
    cpf_cnpj: mascararCpfCnpj(p?.cpf_cnpj ?? ""),
    mesmo_endereco: igualAoEmpreendimento,
    corr_logradouro: p?.corr_logradouro ?? "",
    corr_numero: p?.corr_numero ?? "",
    corr_complemento: p?.corr_complemento ?? "",
    corr_bairro: p?.corr_bairro ?? "",
    corr_municipio: p?.corr_municipio ?? "",
    corr_uf: p?.corr_uf ?? "",
    corr_cep: mascararCep(p?.corr_cep ?? ""),
  };
}

export function FormularioLocal({ inicial, rotuloSalvar, salvar, onSalvo, onCancelar }: Props) {
  const proximaChave = useRef(1);
  const [campos, setCampos] = useState({
    nome: inicial?.nome ?? "",
    municipio: inicial?.municipio ?? "",
    tipo: inicial?.tipo ?? "",
    latitude: coordenada(inicial?.latitude),
    longitude: coordenada(inicial?.longitude),
    latitude_gms: inicial?.latitude_gms ?? "",
    longitude_gms: inicial?.longitude_gms ?? "",
    numero_car: inicial?.numero_car ?? "",
    logradouro: inicial?.logradouro ?? "",
    uf: inicial?.uf ?? "MT",
    cep: mascararCep(inicial?.cep ?? ""),
  });
  const [modo, setModo] = useState<ModoCoordenada>("decimal");
  const [linhas, setLinhas] = useState<LinhaProprietario[]>(() =>
    (inicial?.proprietarios ?? []).map((p) => linhaDe(proximaChave.current++, p, inicial)),
  );
  const [tentou, setTentou] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<unknown>(null);

  const mudar = (campo: keyof typeof campos, valor: string) => setCampos((c) => ({ ...c, [campo]: valor }));
  const mudarLinha = (chave: number, parcial: Partial<LinhaProprietario>) =>
    setLinhas((l) => l.map((x) => (x.chave === chave ? { ...x, ...parcial } : x)));

  // Só presença e sintaxe numérica; faixa de MT, minutos/segundos, DDD, CPF/CNPJ e CEP são validados pela API.
  const faltando = {
    nome: !campos.nome.trim(),
    municipio: !campos.municipio.trim(),
    tipo: !campos.tipo.trim(),
    latitude: modo === "decimal" ? !Number.isFinite(numero(campos.latitude)) : !campos.latitude_gms.trim(),
    longitude: modo === "decimal" ? !Number.isFinite(numero(campos.longitude)) : !campos.longitude_gms.trim(),
  };
  const linhaSemNome = (l: LinhaProprietario) =>
    !l.nome.trim() && [l.telefone, l.cpf_cnpj, l.corr_logradouro, l.corr_numero, l.corr_bairro, l.corr_cep].some((t) => t.trim() !== "");
  const carForaDoModelo = campos.numero_car.trim() !== "" && !segueModeloSicar(campos.numero_car);

  const proprietario = (l: LinhaProprietario): NovoProprietario => ({
    nome: l.nome,
    telefone: l.telefone.trim() || null,
    cpf_cnpj: ou(l.cpf_cnpj),
    corr_numero: ou(l.corr_numero),
    corr_complemento: ou(l.corr_complemento),
    corr_bairro: ou(l.corr_bairro),
    ...(l.mesmo_endereco
      ? { correspondencia_mesmo_endereco: true }
      : { corr_logradouro: ou(l.corr_logradouro), corr_municipio: ou(l.corr_municipio), corr_uf: ou(l.corr_uf), corr_cep: ou(l.corr_cep) }),
  });

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
        ...(modo === "decimal"
          ? { latitude: numero(campos.latitude), longitude: numero(campos.longitude) }
          : { latitude_gms: campos.latitude_gms.trim(), longitude_gms: campos.longitude_gms.trim() }),
        numero_car: campos.numero_car.trim() || null,
        logradouro: ou(campos.logradouro),
        uf: ou(campos.uf),
        cep: ou(campos.cep),
        proprietarios: linhas
          .filter((l) => l.nome.trim() || l.telefone.trim() || l.cpf_cnpj.trim())
          .map(proprietario),
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
        Nome fantasia / denominação *
        <input id="local-nome" name="local-nome" aria-label="Nome do local" value={campos.nome} onChange={(e) => mudar("nome", e.target.value)} />
        {aviso("nome", "Informe o nome.")}
      </label>
      <label htmlFor="local-tipo">
        Tipo *
        <input id="local-tipo" name="local-tipo" aria-label="Tipo do local" placeholder="Ex.: Propriedade rural" value={campos.tipo} onChange={(e) => mudar("tipo", e.target.value)} />
        {aviso("tipo", "Informe o tipo.")}
      </label>

      <fieldset className="proprietarios" aria-label="Endereço do empreendimento">
        <legend>Endereço do empreendimento</legend>
        <label htmlFor="local-logradouro">
          Logradouro / referência
          <input id="local-logradouro" name="local-logradouro" aria-label="Logradouro do empreendimento" placeholder="Ex.: Zona Rural, aos fundos da Fazenda…" value={campos.logradouro} onChange={(e) => mudar("logradouro", e.target.value)} />
        </label>
        <label htmlFor="local-municipio">
          Município *
          <input id="local-municipio" name="local-municipio" aria-label="Município do local" value={campos.municipio} onChange={(e) => mudar("municipio", e.target.value)} />
          {aviso("municipio", "Informe o município.")}
        </label>
        <div className="duas-colunas">
          <label htmlFor="local-uf">
            UF
            <input id="local-uf" name="local-uf" aria-label="UF do empreendimento" maxLength={2} value={campos.uf} onChange={(e) => mudar("uf", e.target.value.toUpperCase())} />
          </label>
          <label htmlFor="local-cep">
            CEP
            <input id="local-cep" name="local-cep" aria-label="CEP do empreendimento" inputMode="numeric" placeholder="00.000-000" value={campos.cep} onChange={(e) => mudar("cep", mascararCep(e.target.value))} />
          </label>
        </div>
      </fieldset>

      <fieldset className="proprietarios" aria-label="Coordenadas">
        <legend>Coordenadas</legend>
        <div role="radiogroup" aria-label="Formato das coordenadas" className="acoes">
          <label htmlFor="local-modo-decimal">
            <input type="radio" id="local-modo-decimal" name="local-modo-coordenada" checked={modo === "decimal"} onChange={() => setModo("decimal")} /> Decimal
          </label>
          <label htmlFor="local-modo-gms">
            <input type="radio" id="local-modo-gms" name="local-modo-coordenada" checked={modo === "gms"} onChange={() => setModo("gms")} /> Graus, minutos e segundos (GMS)
          </label>
        </div>
        {modo === "decimal" ? (
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
        ) : (
          <div className="duas-colunas">
            <label htmlFor="local-latitude-gms">
              Latitude (GMS) *
              <input id="local-latitude-gms" name="local-latitude-gms" aria-label="Latitude GMS do local" placeholder={`11° 46' 34" S`} value={campos.latitude_gms} onChange={(e) => mudar("latitude_gms", mascararGms(e.target.value, "latitude"))} />
              {aviso("latitude", "Informe a latitude em GMS.")}
            </label>
            <label htmlFor="local-longitude-gms">
              Longitude (GMS) *
              <input id="local-longitude-gms" name="local-longitude-gms" aria-label="Longitude GMS do local" placeholder={`59° 05' 12" W`} value={campos.longitude_gms} onChange={(e) => mudar("longitude_gms", mascararGms(e.target.value, "longitude"))} />
              {aviso("longitude", "Informe a longitude em GMS.")}
            </label>
          </div>
        )}
        <p className="dica">
          Digite só números e a letra do hemisfério (S e W em Mato Grosso); a máscara completa os símbolos. As coordenadas devem estar
          dentro de Mato Grosso (latitude −18,05 a −7,35; longitude −61,65 a −50,20) e são salvas em decimal.
        </p>
      </fieldset>

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
        <legend>Responsáveis (proprietários)</legend>
        {linhas.length === 0 && <p className="dica">Nenhum proprietário informado.</p>}
        {linhas.map((l, i) => {
          const p = `local-prop-${l.chave}`;
          return (
            <div className="linha-proprietario" key={l.chave} data-testid="linha-proprietario">
              <label htmlFor={`${p}-nome`}>
                Nome / Razão social *
                <input id={`${p}-nome`} name={`${p}-nome`} aria-label={`Nome do proprietário ${i + 1}`} value={l.nome} onChange={(e) => mudarLinha(l.chave, { nome: e.target.value })} />
                {tentou && linhaSemNome(l) && <span className="campo-erro">Informe o nome.</span>}
              </label>
              <label htmlFor={`${p}-cpf_cnpj`}>
                CPF/CNPJ
                <input id={`${p}-cpf_cnpj`} name={`${p}-cpf_cnpj`} aria-label={`CPF/CNPJ do proprietário ${i + 1}`} inputMode="numeric" placeholder="000.000.000-00" value={l.cpf_cnpj} onChange={(e) => mudarLinha(l.chave, { cpf_cnpj: mascararCpfCnpj(e.target.value) })} />
              </label>
              <label htmlFor={`${p}-telefone`}>
                Telefone
                <input
                  id={`${p}-telefone`}
                  name={`${p}-telefone`}
                  aria-label={`Telefone do proprietário ${i + 1}`}
                  inputMode="tel"
                  placeholder="(65) 90000-0001"
                  value={l.telefone}
                  onChange={(e) => mudarLinha(l.chave, { telefone: e.target.value })}
                  onBlur={() => mudarLinha(l.chave, { telefone: formatarTelefone(l.telefone) })}
                />
              </label>
              <fieldset className="proprietarios" aria-label={`Endereço para correspondência do proprietário ${i + 1}`}>
                <legend>Endereço para correspondência</legend>
                <label htmlFor={`${p}-mesmo`}>
                  <input type="checkbox" id={`${p}-mesmo`} name={`${p}-mesmo`} checked={l.mesmo_endereco} onChange={(e) => mudarLinha(l.chave, { mesmo_endereco: e.target.checked })} />{" "}
                  Mesmo endereço do empreendimento
                </label>
                {l.mesmo_endereco ? (
                  <p className="dica" data-testid={`mesmo-endereco-${i + 1}`}>
                    Logradouro, município, UF e CEP serão copiados do endereço do empreendimento ao salvar.
                  </p>
                ) : (
                  <>
                    <label htmlFor={`${p}-corr_logradouro`}>
                      Logradouro
                      <input id={`${p}-corr_logradouro`} name={`${p}-corr_logradouro`} aria-label={`Logradouro de correspondência do proprietário ${i + 1}`} value={l.corr_logradouro} onChange={(e) => mudarLinha(l.chave, { corr_logradouro: e.target.value })} />
                    </label>
                    <div className="duas-colunas">
                      <label htmlFor={`${p}-corr_municipio`}>
                        Município
                        <input id={`${p}-corr_municipio`} name={`${p}-corr_municipio`} aria-label={`Município de correspondência do proprietário ${i + 1}`} value={l.corr_municipio} onChange={(e) => mudarLinha(l.chave, { corr_municipio: e.target.value })} />
                      </label>
                      <label htmlFor={`${p}-corr_uf`}>
                        UF
                        <input id={`${p}-corr_uf`} name={`${p}-corr_uf`} aria-label={`UF de correspondência do proprietário ${i + 1}`} maxLength={2} value={l.corr_uf} onChange={(e) => mudarLinha(l.chave, { corr_uf: e.target.value.toUpperCase() })} />
                      </label>
                    </div>
                    <label htmlFor={`${p}-corr_cep`}>
                      CEP
                      <input id={`${p}-corr_cep`} name={`${p}-corr_cep`} aria-label={`CEP de correspondência do proprietário ${i + 1}`} inputMode="numeric" placeholder="00.000-000" value={l.corr_cep} onChange={(e) => mudarLinha(l.chave, { corr_cep: mascararCep(e.target.value) })} />
                    </label>
                  </>
                )}
                <div className="duas-colunas">
                  <label htmlFor={`${p}-corr_numero`}>
                    Número
                    <input id={`${p}-corr_numero`} name={`${p}-corr_numero`} aria-label={`Número de correspondência do proprietário ${i + 1}`} value={l.corr_numero} onChange={(e) => mudarLinha(l.chave, { corr_numero: e.target.value })} />
                  </label>
                  <label htmlFor={`${p}-corr_complemento`}>
                    Complemento
                    <input id={`${p}-corr_complemento`} name={`${p}-corr_complemento`} aria-label={`Complemento de correspondência do proprietário ${i + 1}`} value={l.corr_complemento} onChange={(e) => mudarLinha(l.chave, { corr_complemento: e.target.value })} />
                  </label>
                </div>
                <label htmlFor={`${p}-corr_bairro`}>
                  Bairro
                  <input id={`${p}-corr_bairro`} name={`${p}-corr_bairro`} aria-label={`Bairro de correspondência do proprietário ${i + 1}`} value={l.corr_bairro} onChange={(e) => mudarLinha(l.chave, { corr_bairro: e.target.value })} />
                </label>
              </fieldset>
              <button type="button" className="secundario" aria-label={`Remover proprietário ${i + 1}`} onClick={() => setLinhas((x) => x.filter((y) => y.chave !== l.chave))}>
                Remover
              </button>
            </div>
          );
        })}
        <button type="button" className="secundario" onClick={() => setLinhas((l) => [...l, linhaDe(proximaChave.current++)])}>
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

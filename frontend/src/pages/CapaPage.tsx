import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Carregando, MensagemErro } from "../components/Basicos";
import { useDadosCapa } from "../hooks/useDados";
import { copiarTexto } from "../utils/copiar";

/**
 * "Dados para a capa e lavratura": os dados da inspeção na ordem da capa da SEMA, prontos para copiar para o sistema da
 * SEMA. O texto de cada bloco e o "Copiar tudo" vêm prontos da API; a tela só mostra, destaca o que falta e copia.
 */
export default function CapaPage() {
  const id = Number(useParams().id);
  const { data, isLoading, error } = useDadosCapa(id);
  const [aviso, setAviso] = useState<string | null>(null);

  async function copiar(texto: string, o_que: string) {
    const ok = await copiarTexto(texto);
    setAviso(ok ? `Copiado: ${o_que}.` : `Não foi possível copiar ${o_que}. Selecione o texto e copie manualmente.`);
  }

  if (isLoading) return <Carregando />;
  if (error) return <MensagemErro erro={error} />;
  if (!data) return null;

  return (
    <section>
      <p><Link to={`/inspecoes/${id}`}>← {data.codigo}</Link></p>
      <h1>Dados para a capa e lavratura — {data.codigo}</h1>
      <p className="dica">
        Dados organizados na ordem da capa do sistema da SEMA. Este sistema não gera a capa: copie cada campo, cada bloco ou tudo
        de uma vez.
      </p>
      {data.campos_faltando > 0 ? (
        <div role="alert" className="alerta alerta-aviso" data-testid="resumo-faltando">
          {data.campos_faltando === 1 ? "1 campo não informado" : `${data.campos_faltando} campos não informados`} (destacados abaixo).
          Complete antes de ir para o sistema da SEMA: em <Link to={`/inspecoes/${id}/editar`}>Editar inspeção</Link> e, para
          empreendimento e responsáveis, em <Link to="/locais">Locais</Link>.
        </div>
      ) : (
        <div role="status" className="alerta alerta-ok" data-testid="resumo-faltando">Todos os campos estão preenchidos.</div>
      )}
      <div className="acoes">
        <button type="button" onClick={() => copiar(data.texto_completo, "todos os dados")}>Copiar tudo</button>
      </div>
      <div role="status" aria-live="polite" className="dica" data-testid="aviso-copia">{aviso}</div>

      {data.blocos.map((b) => (
        <section key={b.chave} className="cartao" aria-labelledby={`capa-${b.chave}`} data-testid={`bloco-${b.chave}`}>
          <div className="acoes">
            <h2 id={`capa-${b.chave}`}>{b.titulo}</h2>
            <button type="button" className="secundario" aria-label={`Copiar bloco ${b.titulo}`} onClick={() => copiar(b.texto, `bloco ${b.titulo}`)}>
              Copiar bloco
            </button>
          </div>
          <dl className="dados-capa">
            {b.campos.map((c, i) => (
              <div key={i} className={c.faltando ? "campo-faltando" : c.ausente ? "campo-ausente" : undefined} data-testid={c.faltando ? "campo-faltando" : undefined}>
                <dt>{c.rotulo}</dt>
                <dd>
                  <span>{c.valor}</span>
                  <button
                    type="button"
                    className="secundario"
                    aria-label={`Copiar ${c.rotulo}`}
                    disabled={c.ausente}
                    onClick={() => copiar(c.copiar, c.rotulo)}
                  >
                    Copiar
                  </button>
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </section>
  );
}

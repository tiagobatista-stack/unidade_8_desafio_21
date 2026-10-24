"""R4/E3: o Local aceita coordenadas em decimal ou em GMS e devolve as duas formas."""
import pytest

BASE = "/api/v1"


@pytest.fixture
def api(client, exemplos):
    return client


def corpo(**kw):
    base = dict(nome="Fazenda GMS Fictícia", municipio="Município Fictício", tipo="Propriedade rural")
    base.update(kw)
    return base


def test_cadastro_em_gms_converte_para_decimal_ao_salvar(api):
    r = api.post(f"{BASE}/locais", json=corpo(latitude_gms="11° 46' 34\" S", longitude_gms="59° 05' 12\" W"))
    assert r.status_code == 201, r.text
    d = r.json()
    assert (d["latitude"], d["longitude"]) == (-11.77611, -59.08667)
    assert (d["latitude_gms"], d["longitude_gms"]) == ("11° 46' 34\" S", "59° 05' 12\" W")
    assert d["coordenadas_gms"] == "LAT 11° 46' 34\" S | LONG 59° 05' 12\" W"


def test_cadastro_em_decimal_continua_valendo_e_devolve_o_gms(api):
    d = api.post(f"{BASE}/locais", json=corpo(latitude=-11.77611, longitude=-59.08667)).json()
    assert d["coordenadas_gms"] == "LAT 11° 46' 34\" S | LONG 59° 05' 12\" W"


def test_pode_misturar_um_eixo_em_cada_formato(api):
    d = api.post(f"{BASE}/locais", json=corpo(latitude_gms="11 46 34 S", longitude=-59.08667)).json()
    assert (d["latitude"], d["longitude"]) == (-11.77611, -59.08667)


def test_gms_com_minutos_60_e_rejeitado_apontando_o_campo(api):
    r = api.post(f"{BASE}/locais", json=corpo(latitude_gms="11° 60' 00\" S", longitude=-55.5))
    assert r.status_code == 422
    assert r.json()["erro"]["detalhes"] == [{"campo": "latitude_gms", "mensagem": "Minutos e segundos devem ser menores que 60."}]


def test_gms_fora_de_mato_grosso_mantem_a_validacao_dos_limites(api):
    r = api.post(f"{BASE}/locais", json=corpo(latitude_gms="25° 00' 00\" S", longitude_gms="59° 05' 12\" W"))
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "COORDENADA_FORA_DE_MT"
    assert r.json()["erro"]["detalhes"][0]["campo"] == "latitude"


def test_sem_coordenada_nenhuma_e_obrigatoria(api):
    r = api.post(f"{BASE}/locais", json=corpo(longitude=-55.5))
    assert r.status_code == 422
    assert r.json()["erro"]["detalhes"] == [{"campo": "latitude", "mensagem": "Campo obrigatório."}]


def test_editar_em_gms_atualiza_o_decimal(api):
    lid = api.post(f"{BASE}/locais", json=corpo(latitude=-12.5, longitude=-55.5)).json()["id"]
    r = api.put(f"{BASE}/locais/{lid}", json=corpo(latitude_gms="11° 46' 34\" S", longitude_gms="59° 05' 12\" W"))
    assert r.status_code == 200 and r.json()["latitude"] == -11.77611


def test_detalhe_da_inspecao_traz_gms_do_empreendimento(api):
    i = api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"][0]
    e = api.get(f"{BASE}/inspecoes/{i['id']}").json()["empreendimento"]
    assert e["coordenadas_gms"].startswith("LAT ") and " | LONG " in e["coordenadas_gms"]

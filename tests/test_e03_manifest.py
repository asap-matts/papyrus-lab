"""Il manifest di E03 deve fallire su ogni rapporto del socio alterato, incompleto o non numerico (revisione R3, secondo giro).

I rapporti reali si leggono dal branch `origin/e03-socio`; se il branch non è disponibile i test che ne dipendono
vengono saltati, non superati.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import e03_manifest as m  # noqa: E402

CURVE = ROOT / "docs" / "reports" / "e03-r01" / "metrics" / "curve.json"
DS = ROOT / "configs" / "e03" / "datasets.json"


def _git_show(path: str) -> str | None:
    r = subprocess.run(["git", "show", f"origin/e03-socio:{path}"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    return r.stdout if r.returncode == 0 else None


@pytest.fixture(scope="module")
def curve():
    return json.loads(CURVE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ds():
    return json.loads(DS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def s3():
    t = _git_show("docs/reports/2026-09-07-e03-socio-s3-ricalcolo.md")
    if t is None:
        pytest.skip("branch origin/e03-socio non disponibile")
    return t


@pytest.fixture(scope="module")
def s2():
    t = _git_show("docs/reports/2026-09-07-e03-socio-s2-pooling-46527.md")
    if t is None:
        pytest.skip("branch origin/e03-socio non disponibile")
    return t


def _auroc_rows(s3: str) -> list[str]:
    return [ln for ln in s3.split("## AUROC held-out\n\n", 1)[1].split("\n\n", 1)[0].splitlines()[2:]]


def test_s3_reale_passa(s3, curve):
    out = m.check_s3(s3, curve)
    assert out["auroc_cells_compared"] == 28 and out["auroc_table_max_abs_diff"] < 5e-6
    assert out["H1_violations_compared"] == 6


def test_s3_riga_zero_ripetuta_sette_volte_fallisce(s3, curve):
    rows = _auroc_rows(s3)
    zero = next(r for r in rows if r.startswith("| 0 "))
    bad = s3.replace("\n".join(rows), "\n".join([zero] * 7))
    with pytest.raises(ValueError, match="duplicato"):
        m.check_s3(bad, curve)


def test_s3_offset_mancante_fallisce(s3, curve):
    rows = _auroc_rows(s3)
    bad = s3.replace("\n".join(rows), "\n".join(r for r in rows if not r.startswith("| +5 ")))
    with pytest.raises(ValueError, match="diversi da"):
        m.check_s3(bad, curve)


@pytest.mark.parametrize("token", ["nan", "inf"])
def test_s3_valore_non_finito_fallisce(s3, curve, token):
    bad = s3.replace("0,813722", token, 1)
    with pytest.raises(ValueError, match="non finito"):
        m.check_s3(bad, curve)


def test_s3_auroc_alterata_fallisce(s3, curve):
    bad = s3.replace("0,813722", "0,813822", 1)
    with pytest.raises(ValueError, match="scarto AUROC"):
        m.check_s3(bad, curve)


def test_s3_colonne_permutate_falliscono(s3, curve):
    rows = _auroc_rows(s3)
    swapped = []
    for r in rows:
        c = [x.strip() for x in r.strip().strip("|").split("|")]
        swapped.append("| " + " | ".join([c[0], c[2], c[1], c[3], c[4]]) + " |")
    bad = s3.replace("\n".join(rows), "\n".join(swapped))
    with pytest.raises(ValueError, match="scarto AUROC"):
        m.check_s3(bad, curve)


def test_s3_h1_stesso_numero_ma_violazione_diversa_fallisce(s3, curve):
    # stesso conteggio (6), ma una combinazione sostituita da una che non viola
    bad = s3.replace("| w016/s43 | +2 | −0,026046 | 0,006046 |", "| 0814/s43 | +2 | +0,013821 | 0,000000 |")
    with pytest.raises(ValueError, match="violazioni H1 diverse"):
        m.check_s3(bad, curve)


def test_s3_h2_riga_duplicata_fallisce(s3, curve):
    bad = s3.replace("| 43 | + | −0,006112 | −0,011889 | −0,018510 | sì | sì | **sì** |",
                     "| 43 | − | −0,027476 | −0,051385 | −0,083349 | sì | sì | **sì** |")
    with pytest.raises(ValueError, match="H2"):
        m.check_s3(bad, curve)


def test_s3_tolleranza_duplicata_fallisce(s3, curve):
    bad = s3.replace("| 0814 | 43 | 5 slice |", "| 0814 | 42 | 5 slice |")
    with pytest.raises(ValueError, match="tolleranza"):
        m.check_s3(bad, curve)


def test_s3_controllo_fuori_sezione_non_conta(s3, curve):
    # il verdetto della media dei seed viene spostato fuori dalla sua sezione: due frasi ci sono ancora, ma non al posto giusto
    bad = s3.replace("**Verdetto complessivo: non aiuta.** La media supera seed 42", "La media supera seed 42", 1)
    bad = bad.replace("## Ambiguità e scelte conservative", "**Verdetto complessivo: non aiuta.**\n\n## Ambiguità e scelte conservative", 1)
    with pytest.raises(ValueError, match="verdetto del controllo"):
        m.check_s3(bad, curve)


def test_s3_anomalia_attivata_fallisce(s3, curve):
    bad = s3.replace("**Non attivata.**", "**Attivata.**", 1)
    with pytest.raises(ValueError, match="anomalia"):
        m.check_s3(bad, curve)


def test_s1_verdetto_vuoto_o_sconosciuto_fallisce():
    with pytest.raises(ValueError, match="verdetto S1"):
        m.check_s1({"verdict": "", "counts": {}}, "")
    with pytest.raises(ValueError, match="verdetto S1"):
        m.check_s1({"verdict": "tutto bene", "counts": {}}, "tutto bene")
    with pytest.raises(ValueError, match="assente dal rapporto"):
        m.check_s1({"verdict": "trovato lavoro parziale", "counts": {}}, "altro testo")


def test_s2_reale_passa_e_alterazioni_falliscono(s2, ds):
    script_sha = m.sha256_file(ROOT / "scripts" / "e03_pool_shifted.py")
    assert m.check_s2(s2, ds, script_sha)["identical_to_datasets_json"] is True
    with pytest.raises(ValueError, match="impronte S2"):
        m.check_s2(s2.replace("bc7423431221", "bc7423431222", 1), ds, script_sha)
    with pytest.raises(ValueError, match="impronta dello script"):
        m.check_s2(s2, ds, "0" * 64)
    # due token `True` presenti ma non nelle frasi di uguaglianza attese
    bad = s2.replace("del centrale — `True`.", "del centrale — controllato.").replace("## Ostacoli", "`True` `True`\n\n## Ostacoli")
    with pytest.raises(ValueError, match="uguaglianza slice"):
        m.check_s2(bad, ds, script_sha)
    with pytest.raises(ValueError, match="duplicato"):
        m.check_s2(s2.replace("| 25 | +3 |", "| 13 | +3 |", 1), ds, script_sha)


def test_curva_alterata_fallisce(curve):
    bad = json.loads(json.dumps(curve))
    bad["auroc_held"]["43"]["5"]["pherc0814-46527"] += 1e-4
    with pytest.raises(ValueError, match="non coincide"):
        m.recompute_curve(bad)


def test_sigillo_su_modo_fallisce():
    with pytest.raises(ValueError, match="sigillato"):
        m.sealed_scan({f"infer_{m.SEALED}_s42_z0": {}})

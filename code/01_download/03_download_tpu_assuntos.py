"""
Fetch the official CNJ/PJe Tabela Processual Unificada (TPU) record for every
electoral-lawsuit subject code that appears in our dataset, to give the subject
taxonomy auditable provenance (official name + glossary + parent hierarchy)
instead of hand labels.

Source API (public, no auth):
  https://gateway.cloud.pje.jus.br/tpu/  (Swagger: /tpu/swagger-ui.html)
  GET /api/v1/publico/consulta/detalhada/assuntos?codigo=<cod>
      -> [{cod_item, cod_item_pai, nome, descricao_glossario, ...}]

Universe of codes = every `main_subject_code` in subject_taxonomy_PROPOSED.csv
(the full set of subjects observed in the TSE processual data, with our volume).

For each code we record: official name, the legal glossary ("what it is"),
the immediate parent, and the full ancestor path up to the TPU root — so each
subject can be grouped by the official tree rather than by our own families.

Output:
  data/raw/tpu_assunto_reference.csv   (one row per subject code; committed snapshot)
  data/raw/tpu_eleitoral_tree.json     (raw subtree dump, for reference)

Run: python code/01_download/03_download_tpu_assuntos.py
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN = PROJECT_ROOT / "data" / "clean"
RAW = PROJECT_ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://gateway.cloud.pje.jus.br/tpu/api/v1/publico"
DETALHADA = BASE + "/consulta/detalhada/assuntos"
DOWNLOAD = BASE + "/download/assuntos"
ELECTORAL_ROOT = 11428  # "DIREITO ELEITORAL E PROCESSO ELEITORAL ..." branch

UA = {"User-Agent": "Mozilla/5.0 (research; taxonomy validation)"}


def _get(url: str, timeout: int = 20) -> object | None:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 — resilient bulk fetch
        print(f"   ! fetch failed: {url[:90]} ({e})")
        return None


def clean_glossary(text: str) -> str:
    """Collapse the legal-text glossary into a single trimmed line."""
    if not text:
        return ""
    t = re.sub(r"\s+", " ", str(text)).strip()
    return t


def main() -> None:
    tax = pd.read_csv(
        CLEAN / "subject_taxonomy_PROPOSED.csv",
        dtype={"main_subject_code": str},
        encoding="utf-8-sig",
        keep_default_na=False,
    )
    codes = [int(c) for c in tax["main_subject_code"]]
    vol = {int(r.main_subject_code): r.vol for r in tax.itertuples()}
    prev_disp = {int(r.main_subject_code): r.disposition for r in tax.itertuples()}
    prev_fam = {int(r.main_subject_code): r.family for r in tax.itertuples()}
    print(f"Subjects in our dataset: {len(codes)}")

    # node cache: cod_item -> {nome, pai, glossario}
    cache: dict[int, dict] = {}

    def ingest(records: object) -> None:
        if not isinstance(records, list):
            return
        for rec in records:
            if isinstance(rec, dict) and "cod_item" in rec:
                cache[int(rec["cod_item"])] = {
                    "nome": rec.get("nome", ""),
                    "pai": rec.get("cod_item_pai"),
                    "glossario": clean_glossary(rec.get("descricao_glossario", "")),
                }

    # 1. seed cache with the full electoral subtree (one bulk download)
    print(f"Downloading electoral subtree (root {ELECTORAL_ROOT}) ...")
    tree = _get(f"{DOWNLOAD}?codigo={ELECTORAL_ROOT}", timeout=90)
    if isinstance(tree, list):
        (RAW / "tpu_eleitoral_tree.json").write_text(
            json.dumps(tree, ensure_ascii=False), encoding="utf-8"
        )
        ingest(tree)
        print(f"   cached {len(cache)} electoral nodes")

    # 2. fetch any of our codes still missing, individually
    missing = [c for c in codes if c not in cache]
    print(f"Fetching {len(missing)} codes not in electoral subtree ...")
    for i, c in enumerate(missing, 1):
        ingest(_get(f"{DETALHADA}?codigo={c}"))
        if i % 25 == 0:
            print(f"   {i}/{len(missing)}")
        time.sleep(0.05)

    # 3. resolve parent names: close the ancestor set (fetch missing parents)
    for _ in range(15):  # depth cap
        need = {
            v["pai"]
            for v in cache.values()
            if v.get("pai") and int(v["pai"]) not in cache
        }
        if not need:
            break
        for p in need:
            ingest(_get(f"{DETALHADA}?codigo={int(p)}"))
            time.sleep(0.05)

    def name(c) -> str:
        return cache.get(int(c), {}).get("nome", "") if c is not None else ""

    def ancestor_path(c: int) -> str:
        chain, seen, cur = [], set(), c
        while cur is not None and int(cur) in cache and int(cur) not in seen:
            seen.add(int(cur))
            chain.append(name(cur))
            cur = cache[int(cur)].get("pai")
        return " > ".join(reversed(chain))

    # 4. assemble the reference table
    rows = []
    for c in codes:
        node = cache.get(c, {})
        rows.append(
            {
                "subject_code": c,
                "official_name": node.get("nome", ""),
                "what_it_is": node.get("glossario", ""),
                "parent_code": node.get("pai"),
                "parent_name": name(node.get("pai")),
                "ancestor_path": ancestor_path(c),
                "our_volume": vol.get(c, 0),
                "found_in_tpu": c in cache,
                "prev_disposition": prev_disp.get(c, ""),
                "prev_family": prev_fam.get(c, ""),
            }
        )
    ref = pd.DataFrame(rows).sort_values("our_volume", ascending=False)
    out = RAW / "tpu_assunto_reference.csv"
    ref.to_csv(out, index=False, encoding="utf-8-sig")

    n_found = int(ref["found_in_tpu"].sum())
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}  ({len(ref)} subjects)")
    print(f"Matched in TPU: {n_found}/{len(ref)}  | not found: {len(ref) - n_found}")
    print("\nTop-level electoral branches (by our volume):")
    ref["branch_l2"] = ref["ancestor_path"].str.split(" > ").str[:3].str.join(" > ")
    g = (
        ref[ref["found_in_tpu"]]
        .groupby("branch_l2")
        .agg(codes=("subject_code", "size"), vol=("our_volume", "sum"))
        .sort_values("vol", ascending=False)
        .head(20)
    )
    for b, r in g.iterrows():
        print(f"  {int(r['vol']):>9,}  {int(r['codes']):>3} codes  {b[:80]}")


if __name__ == "__main__":
    main()

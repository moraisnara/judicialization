"""
Fetch the official CNJ/PJe Tabela Processual Unificada (TPU) record for every
procedural CLASS code that appears in our electoral-lawsuit data, mirroring
03_download_tpu_assuntos.py (which does the same for subjects/assuntos).

The CLASS (classe processual) is the *kind of action* (AIJE, AIME, RCED,
Representação, Registro de Candidatura, ...) -- orthogonal to the subject. Some
classes are adversarial by nature (an AIJE is always an abuse-of-power
investigation regardless of its subject tag); others are mandatory filings
(Registro de Candidatura, Prestação de Contas). We need the official class tree
+ glossary so the keep/drop decision can use the class, not just the subject.

Source API (public, no auth):
  https://gateway.cloud.pje.jus.br/tpu/
  GET /api/v1/publico/consulta/detalhada/classes?codigo=<cod>
      -> [{cod_item, cod_item_pai, nome, descricao_glossario, ...}]
  GET /api/v1/publico/download/classes?codigo=<root>  -> full subtree

Universe of class codes = every distinct case_class_code in the zona panel.

Output:
  data/raw/tpu_classe_reference.csv   (one row per class code; committed snapshot)
  data/raw/tpu_classe_tree.json       (raw electoral-class subtree dump)

Run: python code/01_download/03b_download_tpu_classes.py
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://gateway.cloud.pje.jus.br/tpu/api/v1/publico"
DETALHADA = BASE + "/consulta/detalhada/classes"
DOWNLOAD = BASE + "/download/classes"
UA = {"User-Agent": "Mozilla/5.0 (research; taxonomy validation)"}

PANEL = CLEAN / "zona_lawsuit_panel.csv"


def _get(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"   ! fetch failed: {url[:90]} ({e})")
        return None


def clean_gloss(t: str) -> str:
    return re.sub(r"\s+", " ", str(t)).strip() if t else ""


def main() -> None:
    p = pd.read_csv(PANEL, dtype={"case_class_code": str}, low_memory=False,
                    usecols=["case_class_code", "case_class_name", "n_lawsuits"])
    vol = (p.groupby("case_class_code")["n_lawsuits"].sum().to_dict())
    names = dict(zip(p["case_class_code"], p["case_class_name"]))
    codes = sorted({int(c) for c in p["case_class_code"].dropna()
                    if str(c).strip().isdigit()})
    print(f"Distinct class codes in our data: {len(codes)}")

    cache: dict[int, dict] = {}

    def ingest(records) -> None:
        if not isinstance(records, list):
            return
        for rec in records:
            if isinstance(rec, dict) and "cod_item" in rec:
                cache[int(rec["cod_item"])] = {
                    "nome": rec.get("nome", ""),
                    "pai": rec.get("cod_item_pai"),
                    "glossario": clean_gloss(rec.get("descricao_glossario", "")),
                }

    # 1. fetch each observed class code individually (and discover its parents)
    print("Fetching observed class codes ...")
    for i, c in enumerate(codes, 1):
        ingest(_get(f"{DETALHADA}?codigo={c}"))
        if i % 20 == 0:
            print(f"   {i}/{len(codes)}")
        time.sleep(0.05)

    # 2. close the ancestor set so we can build the full path/root for each class
    for _ in range(20):
        need = {v["pai"] for v in cache.values()
                if v.get("pai") and int(v["pai"]) not in cache}
        if not need:
            break
        for q in need:
            ingest(_get(f"{DETALHADA}?codigo={int(q)}"))
            time.sleep(0.05)

    # 3. try to dump the electoral-class subtree from each discovered root
    roots = {int(v["pai"]) for v in cache.values()
             if v.get("pai") and int(v["pai"]) not in
             {vv["pai"] for vv in cache.values() if vv.get("pai")}}
    tree_dump = []
    for r in sorted(roots):
        t = _get(f"{DOWNLOAD}?codigo={r}", timeout=90)
        if isinstance(t, list):
            tree_dump.extend(t)
            ingest(t)
    if tree_dump:
        (RAW / "tpu_classe_tree.json").write_text(
            json.dumps(tree_dump, ensure_ascii=False), encoding="utf-8")

    def nm(c):
        return cache.get(int(c), {}).get("nome", "") if c is not None else ""

    def path(c):
        chain, seen, cur = [], set(), c
        while cur is not None and int(cur) in cache and int(cur) not in seen:
            seen.add(int(cur)); chain.append(nm(cur)); cur = cache[int(cur)].get("pai")
        return " > ".join(reversed(chain))

    rows = []
    for c in codes:
        node = cache.get(c, {})
        rows.append({
            "class_code": c,
            "official_name": node.get("nome", "") or names.get(str(c), ""),
            "what_it_is": node.get("glossario", ""),
            "parent_code": node.get("pai"),
            "parent_name": nm(node.get("pai")),
            "ancestor_path": path(c),
            "our_volume": int(vol.get(str(c), 0)),
            "found_in_tpu": c in cache,
            "our_name": names.get(str(c), ""),
        })
    ref = pd.DataFrame(rows).sort_values("our_volume", ascending=False)
    out = RAW / "tpu_classe_reference.csv"
    ref.to_csv(out, index=False, encoding="utf-8-sig")
    n_found = int(ref["found_in_tpu"].sum())
    print(f"\nSaved: {out.relative_to(ROOT)}  ({len(ref)} classes)")
    print(f"Matched in TPU: {n_found}/{len(ref)} | not found: {len(ref)-n_found}")
    print("\nTop classes by our volume (official name | glossary present?):")
    for r in ref.head(20).itertuples():
        gl = "gloss" if r.what_it_is else "  -  "
        print(f"  {r.our_volume:>10,}  [{gl}]  {r.class_code}  {r.official_name[:55]}")


if __name__ == "__main__":
    main()

r"""
19_candidate_experience.py  (exploratory)

Candidate-level electoral experience, pooled across offices. For every PREFEITO
and VEREADOR candidate we count prior runs (since 2012) for the SAME office, then
report:
  * share running for the first time vs. returning, by office and year;
  * for mayors, the full nth-observed-run distribution (1st / 2nd / 3rd / 4th+).

Caveats (intrinsic to the data):
  * Left-censored at 2012: "prior runs" = prior runs OBSERVED since 2012, so true
    career length is undercounted (max 3 priors by 2024). This makes "first-timer"
    an UPPER bound -- some apparent first-timers ran before 2012.
  * Council (vereador) has no term limit, so a high prior count is normal and the
    "career politician" cut is less meaningful there; first-vs-returning is the
    clean comparison across offices.

Reads:  data/raw/consulta_cand_{2012,2016,2020,2024}/...
Writes: output/tables/descriptives/candidate_experience_distribution.csv
        output/tables/descriptives/candidate_experience_firsttime.csv
"""
import unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "output" / "tables" / "descriptives"
OUT.mkdir(parents=True, exist_ok=True)
YEARS = [2012, 2016, 2020, 2024]
ELECTED = {"ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA"}
USECOLS = ["SG_UF", "SG_UE", "DS_CARGO", "CD_TIPO_ELEICAO", "NR_TURNO",
           "NR_TITULO_ELEITORAL_CANDIDATO", "NM_CANDIDATO", "DT_NASCIMENTO",
           "DS_SIT_TOT_TURNO"]


def norm(s):
    t = "" if pd.isna(s) else str(s).strip().upper()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return " ".join(t.split())


def office_of(cargo):
    c = str(cargo).upper()
    if "PREFEITO" in c:
        return "Prefeito"
    if "VEREADOR" in c:
        return "Vereador"
    return None


def load_year(year):
    folder = RAW / f"consulta_cand_{year}"
    files = sorted(folder.glob(f"consulta_cand_{year}_BRASIL.csv"))
    if not files:
        files = [f for f in folder.glob(f"consulta_cand_{year}_*.csv")
                 if "leiame" not in f.name.lower()]
    frames = [pd.read_csv(f, sep=";", encoding="latin-1",
                          usecols=lambda c: c in USECOLS, dtype=str, low_memory=False)
              for f in files]
    df = pd.concat(frames, ignore_index=True)
    df = df[df["CD_TIPO_ELEICAO"] == "2"]
    df = df[df["NR_TURNO"] == "1"]
    df["office"] = df["DS_CARGO"].map(office_of)
    df = df[df["office"].notna()].copy()
    df["election_year"] = year
    tk = df["NR_TITULO_ELEITORAL_CANDIDATO"].fillna("").str.strip().replace(
        {"#NULO#": "", "-4": "", "-1": ""})
    nm = df["NM_CANDIDATO"].map(norm)
    dt = pd.to_datetime(df.get("DT_NASCIMENTO", ""), format="%d/%m/%Y",
                        errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    df["person_key"] = tk.where(tk.str.len() > 3, nm + "|" + dt)
    df["is_elected"] = df["DS_SIT_TOT_TURNO"].map(norm).isin(ELECTED).astype(int)
    df = df.drop_duplicates(subset=["election_year", "office", "SG_UF", "SG_UE", "person_key"])
    return df[["election_year", "office", "SG_UF", "SG_UE", "person_key", "is_elected"]]


print("Loading 2012-2024 prefeito + vereador candidates ...")
allc = pd.concat([load_year(y) for y in YEARS], ignore_index=True)
print(f"  {len(allc):,} candidate-municipality rows")

# Prior runs are counted WITHIN office (running for mayor != running for council).
rows = []
for off in ["Prefeito", "Vereador"]:
    sub = allc[allc.office == off]
    for yr in YEARS:
        cur = sub[sub.election_year == yr].copy()
        prior = sub[sub.election_year < yr]
        pc = prior.groupby("person_key").agg(
            n_prior=("election_year", "count"),
            n_prior_wins=("is_elected", "sum")).reset_index()
        cur = cur.merge(pc, on="person_key", how="left")
        cur["n_prior"] = cur["n_prior"].fillna(0).astype(int)
        cur["n_prior_wins"] = cur["n_prior_wins"].fillna(0).astype(int)
        rows.append(cur)
hist = pd.concat(rows, ignore_index=True)
hist["nth_run"] = hist["n_prior"] + 1
hist["bucket"] = hist["nth_run"].clip(upper=4)
hist["is_first"] = (hist["n_prior"] == 0).astype(int)

# ----- first-time vs returning, by office x year -----
ft = (hist.groupby(["office", "election_year"])
      .agg(n=("person_key", "size"),
           share_first=("is_first", "mean"),
           mean_prior=("n_prior", "mean"),
           share_prior_winner=("n_prior_wins", lambda s: (s > 0).mean()))
      .reset_index())
ft.to_csv(OUT / "candidate_experience_firsttime.csv", index=False)

# ----- mayoral nth-run distribution -----
LABELS = {1: "1st (new)", 2: "2nd", 3: "3rd", 4: "4th+ (career)"}
g = hist.groupby(["office", "election_year", "bucket"]).size().rename("count").reset_index()
g["share"] = g["count"] / g.groupby(["office", "election_year"])["count"].transform("sum")
g["label"] = g["bucket"].map(LABELS)
g.to_csv(OUT / "candidate_experience_distribution.csv", index=False)

print("\nFirst-time share by office x year (UPPER bound; left-censored at 2012):")
fp = ft.pivot_table(index="election_year", columns="office", values="share_first")
print((fp * 100).round(1).to_string())

for off in ["Prefeito", "Vereador"]:
    print(f"\n[{off}] share by which (observed) run this is (%):")
    piv = (g[g.office == off].pivot_table(index="election_year", columns="label", values="share")
           .reindex(columns=["1st (new)", "2nd", "3rd", "4th+ (career)"]))
    print((piv * 100).round(1).to_string())

print("\nPer office x year summary:")
for r in ft.itertuples():
    print(f"  {r.office:8s} {r.election_year}: N={r.n:>7,}  first={100*r.share_first:5.1f}%  "
          f"mean prior={r.mean_prior:.2f}  won before={100*r.share_prior_winner:5.1f}%")
print("\nNote: 2012 is mechanically 100% 'first' (no prior window); read 2020/2024.")
print(f"\nWrote {OUT / 'candidate_experience_firsttime.csv'}")
print(f"Wrote {OUT / 'candidate_experience_distribution.csv'}")

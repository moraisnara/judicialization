"""Office-specific shift-share design build.

Lawsuits come from the SIG TSE microdata export, which resolves each case to its
municipality of origin directly. Only first-instance (Originario) cases filed
before first-round election day are kept. This replaces the old zona-eleitoral
panel and its zona->municipality many-to-many merge, which duplicated each
multi-municipality zona's caseload across its municipalities.

Core choices:
  - exposure unit: municipality, resolved directly by SIG (no zona expansion)
  - treatment universe: adversarial lawsuits only (administrative/procedural
    classes and subjects excluded via DROP_CLASSES and DROP_SUBJECTS)
  - outcome panels separated by office sought (executive = PREFEITO,
    legislative = VEREADOR)

Derived files:
  data/clean/office_candidate_outcomes_panel.csv,
  municipality_competition_subject_panel.csv, municipality_bartik_components.csv,
  executive_shift_share_design.csv, legislative_shift_share_design.csv

Notes:
  - new_candidate_* and incumbent_* are defined only relative to 2020 and are
    substantively meaningful for 2024 outcomes.
  - candidate-file-based concentration metrics (candidate_hhi_party,
    effective_party_count_candidates) are fragmentation proxies, not a full
    ideological polarization measure.
"""
from __future__ import annotations

from pathlib import Path
import difflib
import re
import unicodedata
import zipfile

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"
TABLES_DIR = PROJECT_ROOT / "output" / "tables" / "descriptives"

CROSSWALK_PATH = DERIVED_DIR / "shift_share_subject_crosswalk.csv"
OVERRIDES_PATH = DERIVED_DIR / "shift_share_subject_manual_assignments.csv"
LOOKUP_PATH = RAW_DIR / "lista-zonas-municipios-10-07-24.csv"

TARGET_YEARS = [2020, 2024]

# ── SIG municipality-level lawsuit source ──────────────────────────────────────
# The lawsuit panel is now built from the SIG TSE microdata export, which resolves
# each lawsuit to its MUNICIPALITY of origin (not just the electoral zona). This
# replaces the old zona-eleitoral panel + zona->municipality many-to-many merge,
# which duplicated each multi-municipality zona's caseload across its municipalities
# and inflated the first stage. SIG carries only TEXT labels (no CD_CLASSE /
# CD_ASSUNTO codes), so labels are bridged to the committed codes via the raw-TSE
# processo files; the adversarial DROP filter and subject->family crosswalk are then
# applied on codes exactly as before.
SIG_SOURCES = [
    ("processos_eleitorais.csv.zip", 2020),
    ("processos_eleitorais_2024.csv", 2024),  # despite the .csv name it is a zip
]
SIG_RAW_COLS = [
    "ano", "assunto", "classe", "data_dist", "muni", "tipo_origem", "uf", "zona",
    "qt_dec", "qt_proc", "tempo_med", "data_carga",
]
# First-round municipal election day per cycle (campaign-window cutoff), matching
# the committed ELECTION_CUTOFFS in the retired 01_lawsuit_panel.py.
SIG_ELECTION_DAY = {
    2020: pd.Timestamp("2020-11-15"),
    2024: pd.Timestamp("2024-10-06"),
}
MUNI_DIRECTORY_PATH = RAW_DIR / "bd_diretorio_municipio.csv"
# TSE spellings the fuzzy matcher cannot bridge -> id_municipio_tse (zero-padded).
MANUAL_MUNI_OVERRIDE = {"RN|ASSU": "16039"}  # Assu (TSE) == Acu (IBGE)

# ── Adversarial filter ─────────────────────────────────────────────────────────
# Classes to exclude: administrative and procedural/enforcement classes
DROP_CLASSES: set[str] = {
    # Administrative
    "11532", "12193", "12554", "11530", "12550", "12560", "1298",
    "12549", "12633", "12729", "386", "XXXJ", "12551", "11546",
    "1303", "1308", "12557", "12562",
    # Procedural / enforcement / generic
    "156", "241", "261", "258", "278", "157", "355", "1727", "12060",
    "12248", "12121", "1116", "193", "326", "83", "10980", "335",
    "221", "325", "228", "1463", "11793", "333",
}

# Subjects to exclude within adversarial-class cases
DROP_SUBJECTS: set[str] = {
    "12366",  # enforcement (cumprimento de sentença)
    "11778",  # generic requerimento
    "12362",  # administrative (autorização publicidade institucional)
    "11651",  # administrative (registro de pesquisa eleitoral)
    "12599",  # administrative (acesso sistema pesquisas)
    "12598",  # administrative (regularização inadimplência)
    "11753",  # administrative (convenção partidária)
    "11767",  # administrative (órgão de direção municipal)
    "11579",  # administrative (inscrição eleitoral)
    "11756",  # administrative (filiação - cancelamento)
    "11648",  # generic (pesquisa eleitoral)
    "11592",  # unknown (elegibilidade - quitação)
    "11589",  # unknown (elegibilidade - filiação)
    "11782",  # procedural (intimação)
    "11783",  # procedural (citação)
    "11428",  # generic (direito eleitoral)
    "-1",     # not identified
    # Cargo positional tags (all offices)
    "11628", "11629", "11630", "11631", "11632", "11633", "11634",
    "11637", "11638", "11640", "11641",
    # Generic candidato descriptors
    "11584", "12600", "12601",
}

STANDARD_TO_LEGACY = {
    "election_year": "ANO_ELEICAO",
    "state": "SG_UF",
    "electoral_zone": "zona_eleitoral",
    "municipality_id_tse": "SG_UE",
    "municipality_name": "NM_UE",
    "n_municipalities_in_zone": "n_municipios_zona",
    "case_class_code": "CD_CLASSE",
    "case_class_name": "DS_CLASSE",
    "main_subject_code": "CD_ASSUNTO_PRINCIPAL",
    "main_subject_name": "DS_ASSUNTO_PRINCIPAL",
}
LEGACY_TO_STANDARD = {value: key for key, value in STANDARD_TO_LEGACY.items()}
OFFICE_MAP = {
    "PREFEITO": "executive",
    "VEREADOR": "legislative",
}
ELECTED_STATUSES = {"ELEITO", "ELEITO POR QP", "ELEITO POR MÃ‰DIA", "ELEITO POR MÉDIA"}


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value).strip().upper()
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    return " ".join(text.split())


def load_crosswalk() -> pd.DataFrame:
    crosswalk = pd.read_csv(
        CROSSWALK_PATH,
        dtype={"CD_ASSUNTO_PRINCIPAL": str},
        keep_default_na=False,
    )
    if OVERRIDES_PATH.exists():
        overrides = pd.read_csv(
            OVERRIDES_PATH,
            dtype={"CD_ASSUNTO_PRINCIPAL": str},
            keep_default_na=False,
        )
        crosswalk = crosswalk.merge(
            overrides,
            on="CD_ASSUNTO_PRINCIPAL",
            how="left",
            validate="one_to_one",
            suffixes=("", "_override"),
        )
        crosswalk["manual_family"] = crosswalk["manual_family_override"].where(
            crosswalk["manual_family_override"].str.strip().ne(""),
            crosswalk["manual_family"],
        )
        crosswalk["notes"] = crosswalk["notes_override"].where(
            crosswalk["notes_override"].str.strip().ne(""),
            crosswalk["notes"],
        )
    crosswalk["topic_family"] = crosswalk["manual_family"].where(
        crosswalk["manual_family"].str.strip().ne(""),
        crosswalk["suggested_family"],
    )
    return crosswalk[["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"]]


def load_zone_lookup() -> pd.DataFrame:
    lookup = pd.read_csv(LOOKUP_PATH, sep=";", encoding="utf-8-sig", dtype=str)
    lookup.columns = lookup.columns.str.strip()
    lookup = lookup.rename(
        columns={
            "UF": "SG_UF",
            "ZONA": "zona_eleitoral",
            "COD_LOCALIDADE": "COD_MUN",
            "NOM_LOCALIDADE": "NM_UE",
        }
    )
    lookup = lookup[lookup["SG_UF"] != "ZZ"].copy()
    lookup["zona_eleitoral"] = pd.to_numeric(lookup["zona_eleitoral"], errors="coerce")
    lookup = lookup.dropna(subset=["zona_eleitoral"])
    lookup["zona_eleitoral"] = lookup["zona_eleitoral"].astype(int)
    lookup["SG_UE"] = lookup["COD_MUN"].str.strip().str.zfill(5)
    lookup = lookup[["SG_UF", "zona_eleitoral", "SG_UE", "NM_UE"]].drop_duplicates()
    return lookup


def norm_label(value: object) -> str:
    """Normalize a text label for code bridging: deaccent, drop punctuation,
    collapse whitespace, uppercase. Used to match SIG class/subject/municipality
    names to the canonical TSE codes (validated at 100% of lawsuit volume)."""
    text = "" if pd.isna(value) else str(value).strip()
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    text = re.sub(r"[^A-Za-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).upper().strip()


LABEL_BRIDGE_CACHE = DERIVED_DIR / "label_code_bridge.csv"


def _load_label_bridge_cache() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Reload the three label<->code dicts from the cached crosswalk (long form:
    columns map/key/value). Used when the raw processo dockets are off disk."""
    cache = pd.read_csv(LABEL_BRIDGE_CACHE, dtype=str, keep_default_na=False)
    def as_dict(name: str) -> dict[str, str]:
        sub = cache[cache["map"] == name]
        return dict(zip(sub["key"], sub["value"]))
    return as_dict("class"), as_dict("subject"), as_dict("code_to_ds")


def build_label_code_bridges() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Build normalized-label -> code dictionaries from the raw-TSE processo files,
    which carry both CD_CLASSE/DS_CLASSE and CD_ASSUNTO_PRINCIPAL/DS_ASSUNTO_PRINCIPAL.
    Returns (class_label->code, subject_label->code, subject_code->canonical_DS).

    The processo dockets are large and transient (not committed; they get swept off
    disk). The bridge itself is a tiny STATIC crosswalk, so we cache it to
    data/clean/label_code_bridge.csv on the first successful build and fall back to
    that cache whenever the raw dockets are absent -- a clean rebuild then needs no
    71 MB re-download. Delete the cache (or re-run 01_lawsuits.py) to refresh it."""
    cols = ["CD_CLASSE", "DS_CLASSE", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL"]
    frames: list[pd.DataFrame] = []
    for year in TARGET_YEARS:
        path = RAW_DIR / f"processo_eleitoral_{year}" / f"processo_eleitoral_{year}.csv"
        if not path.exists():
            continue
        frames.append(pd.read_csv(
            path, sep=";", encoding="latin-1", usecols=cols, dtype=str, low_memory=False,
        ))
    if not frames:
        if LABEL_BRIDGE_CACHE.exists():
            print(f"  [label bridge] raw processo dockets absent -> using cache "
                  f"{LABEL_BRIDGE_CACHE.name}", flush=True)
            return _load_label_bridge_cache()
        raise FileNotFoundError(
            f"No processo_eleitoral_* dockets in {RAW_DIR} and no cache at "
            f"{LABEL_BRIDGE_CACHE}. Run code/01_download/01_lawsuits.py to fetch them."
        )
    tse = pd.concat(frames, ignore_index=True)

    class_map: dict[str, str] = {}
    for _, row in tse[["CD_CLASSE", "DS_CLASSE"]].drop_duplicates().iterrows():
        class_map.setdefault(norm_label(row["DS_CLASSE"]), row["CD_CLASSE"])

    subject_map: dict[str, str] = {}
    code_to_ds: dict[str, str] = {}
    for _, row in tse[["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL"]].drop_duplicates().iterrows():
        subject_map.setdefault(norm_label(row["DS_ASSUNTO_PRINCIPAL"]), row["CD_ASSUNTO_PRINCIPAL"])
        code_to_ds.setdefault(row["CD_ASSUNTO_PRINCIPAL"], row["DS_ASSUNTO_PRINCIPAL"])

    # Persist the static crosswalk so future rebuilds survive docket sweeps.
    rows = ([("class", k, v) for k, v in class_map.items()]
            + [("subject", k, v) for k, v in subject_map.items()]
            + [("code_to_ds", k, v) for k, v in code_to_ds.items()])
    LABEL_BRIDGE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["map", "key", "value"]).to_csv(LABEL_BRIDGE_CACHE, index=False)
    return class_map, subject_map, code_to_ds


def build_muni_name_to_tse() -> dict[str, str]:
    """Build (UF|normalized municipality name) -> id_municipio_tse (zero-padded
    5-char) from the basedosdados municipality directory. Reused from the SIG
    builder; resolves each SIG municipality to its TSE code with no many-to-many."""
    directory = pd.read_csv(MUNI_DIRECTORY_PATH, dtype=str, encoding="utf-8")
    directory = directory.dropna(subset=["id_municipio_tse"]).copy()
    directory["key"] = directory["sigla_uf"].str.upper() + "|" + directory["nome"].map(norm_label)
    directory = directory.drop_duplicates("key")
    name_to_tse = {
        row["key"]: str(row["id_municipio_tse"]).strip().zfill(5)
        for _, row in directory.iterrows()
    }
    for key, tse in MANUAL_MUNI_OVERRIDE.items():
        name_to_tse[key] = str(tse).strip().zfill(5)
    return name_to_tse


def load_sig_lawsuits() -> pd.DataFrame:
    """Load the SIG TSE lawsuit microdata (2020 + 2024), municipality-resolved."""
    frames: list[pd.DataFrame] = []
    for filename, year in SIG_SOURCES:
        with zipfile.ZipFile(RAW_DIR / filename) as archive:
            df = pd.read_csv(
                archive.open(archive.namelist()[0]),
                sep=";", encoding="latin-1", dtype=str, low_memory=False,
            )
        df.columns = SIG_RAW_COLS
        df["election_year"] = year
        df["qt_proc"] = pd.to_numeric(df["qt_proc"], errors="coerce").fillna(0.0)
        df["dt_dist"] = pd.to_datetime(df["data_dist"], errors="coerce")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def build_sig_municipal_panel(
    crosswalk: pd.DataFrame,
    nm_ue_by_code: dict[str, str],
) -> pd.DataFrame:
    """Municipality-level lawsuit panel from SIG, matching the schema the bartik
    builder expects. Each lawsuit is already resolved to one municipality, so the
    panel is built WITHOUT the zona->municipality many-to-many expansion. Filters
    (first-instance Originário + filed before first-round election day) and the
    adversarial DROP sets + subject->family crosswalk mirror the committed design."""
    sig = load_sig_lawsuits()

    # Same restrictions as the retired raw-TSE panel: first-instance only
    # (Originário ≈ NR_INSTANCIA == 1) and filed before first-round election day.
    is_originario = sig["tipo_origem"].str.startswith("Origin", na=False)
    election_day = sig["election_year"].map(SIG_ELECTION_DAY)
    pre_election = sig["dt_dist"] < election_day
    sig = sig[is_originario & pre_election].copy()

    # Bridge SIG text labels -> committed TSE codes.
    class_map, subject_map, code_to_ds = build_label_code_bridges()
    sig["CD_CLASSE"] = sig["classe"].map(norm_label).map(class_map)
    sig["CD_ASSUNTO_PRINCIPAL"] = sig["assunto"].map(norm_label).map(subject_map)
    n_unbridged = int(sig["CD_ASSUNTO_PRINCIPAL"].isna().sum())
    if n_unbridged:
        print(f"    SIG subjects without a code bridge: {n_unbridged:,} rows "
              f"({100 * n_unbridged / max(len(sig), 1):.3f}%) — dropped")
    sig = sig[sig["CD_CLASSE"].notna() & sig["CD_ASSUNTO_PRINCIPAL"].notna()].copy()

    # NOTE: the adversarial filter is NO LONGER applied here. Both adversarial and
    # non-adversarial (mandatory/administrative) filings are carried through the
    # panel and tagged with `competition_case` below. Selecting competition_case==True
    # reproduces the old adversarial set byte-for-byte; the excluded filings feed the
    # non-adversarial intensity control and the placebo shift-share (BHJ generic-shares
    # diagnostic). The DROP sets now define the tag, not a row filter.

    # Resolve municipality of origin -> TSE code (no many-to-many; one muni per case).
    name_to_tse = build_muni_name_to_tse()
    sig["muni_key"] = sig["uf"].str.upper() + "|" + sig["muni"].map(norm_label)
    sig["SG_UE"] = sig["muni_key"].map(name_to_tse)
    unmatched_muni = sig["SG_UE"].isna()
    if unmatched_muni.any():
        pct = 100 * sig.loc[unmatched_muni, "qt_proc"].sum() / max(sig["qt_proc"].sum(), 1)
        print(f"    SIG municipalities unmatched to TSE code: "
              f"{int(unmatched_muni.sum()):,} rows ({pct:.3f}% of volume) — dropped")
    sig = sig[sig["SG_UE"].notna()].copy()

    sig = sig.rename(columns={"election_year": "ANO_ELEICAO", "uf": "SG_UF"})
    sig["SG_UF"] = sig["SG_UF"].str.upper()
    sig["zona_eleitoral"] = pd.to_numeric(sig["zona"], errors="coerce").astype("Int64")
    # Canonical DS label from the TSE dictionary, so the crosswalk keys align.
    sig["DS_ASSUNTO_PRINCIPAL"] = sig["CD_ASSUNTO_PRINCIPAL"].map(code_to_ds)
    # NM_UE comes from the same TSE source the universe uses, so design merges on
    # (SG_UF, SG_UE, NM_UE) stay consistent. Fall back to the SIG name (then the
    # code) for the rare municipality absent from the zona lookup, so no row is
    # dropped by the downstream groupby on a missing name.
    sig["NM_UE"] = sig["SG_UE"].map(nm_ue_by_code)
    sig["NM_UE"] = sig["NM_UE"].fillna(sig["muni"].map(norm_label)).fillna(sig["SG_UE"])

    panel = (
        sig.groupby(
            [
                "ANO_ELEICAO",
                "SG_UF",
                "zona_eleitoral",
                "SG_UE",
                "NM_UE",
                "CD_CLASSE",
                "CD_ASSUNTO_PRINCIPAL",
                "DS_ASSUNTO_PRINCIPAL",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(n_lawsuits=("qt_proc", "sum"))
    )
    panel = panel.merge(
        crosswalk,
        on=["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL"],
        how="left",
        validate="many_to_one",
    )
    panel["topic_family"] = panel["topic_family"].fillna("unmapped")
    # Adversarial (=competition) iff NOT in either DROP set. This tag reproduces the
    # old hard filter exactly: competition_case==True selects the identical rows that
    # the removed `~isin(DROP_*)` filter kept.
    panel["competition_case"] = ~(
        panel["CD_CLASSE"].isin(DROP_CLASSES)
        | panel["CD_ASSUNTO_PRINCIPAL"].isin(DROP_SUBJECTS)
    )
    return panel


def build_municipality_bartik_components(
    municipal_panel: pd.DataFrame,
    case_flag: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # case_flag=True -> adversarial (committed) instrument; case_flag=False -> placebo
    # shift-share over the EXCLUDED mandatory/administrative filings. National/leave-out
    # totals are computed from the selected subset only, so the two are fully separate.
    competition = municipal_panel[municipal_panel["competition_case"] == case_flag].copy()

    municipality_subject = (
        competition.groupby(
            [
                "ANO_ELEICAO",
                "SG_UF",
                "SG_UE",
                "NM_UE",
                "CD_ASSUNTO_PRINCIPAL",
                "DS_ASSUNTO_PRINCIPAL",
                "topic_family",
            ],
            as_index=False,
        )
        .agg(n_lawsuits=("n_lawsuits", "sum"))
    )

    baseline = municipality_subject[municipality_subject["ANO_ELEICAO"] == 2020].copy()
    base_totals = baseline.groupby(["SG_UF", "SG_UE"])["n_lawsuits"].transform("sum")
    baseline["baseline_share_2020"] = baseline["n_lawsuits"] / base_totals

    zone_subject = (
        competition.groupby(
            [
                "ANO_ELEICAO",
                "SG_UF",
                "zona_eleitoral",
                "CD_ASSUNTO_PRINCIPAL",
                "DS_ASSUNTO_PRINCIPAL",
                "topic_family",
            ],
            as_index=False,
        )
        .agg(n_lawsuits=("n_lawsuits", "sum"))
    )
    by_uf = (
        zone_subject.groupby(
            ["ANO_ELEICAO", "SG_UF", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
            as_index=False,
        )
        .agg(uf_lawsuits=("n_lawsuits", "sum"))
    )

    # Shift formula: log-change of the leave-state-out aggregate across other states.
    # This is a caseload-weighted adaptation of AMV (2025, JPE): each other state's
    # contribution is weighted by its case count rather than equally, which is necessary
    # because Brazilian lawsuit topics are sparse (many states have 0 cases per topic).
    # The unweighted AMV average collapses to near-zero for sparse topics and kills
    # the first stage (F < 1); the aggregate log-change preserves the strong first stage.
    national = (
        zone_subject.groupby(
            ["ANO_ELEICAO", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
            as_index=False,
        )
        .agg(national_lawsuits=("n_lawsuits", "sum"))
    )
    # Build the leave-state-out shock on the COMPLETE (UF x subject x year) grid. The
    # leave-out aggregate must NEVER be filled with 0 for absent cells: a (UF, subject,
    # year) cell absent from `by_uf` means the UF had zero OWN cases that year, so its
    # true leave-out is the FULL national total (national - 0), not 0. We therefore pivot
    # the OWN-UF count and the NATIONAL total separately -- each with a genuine 0 fill --
    # and subtract at the wide stage, so leave_out = national - own holds in every cell.
    national_wide = (
        national.pivot_table(
            index=["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
            columns="ANO_ELEICAO",
            values="national_lawsuits",
            fill_value=0,  # a subject absent nationally in a year genuinely has 0 filings
        )
        .rename(columns={2020: "national_2020", 2024: "national_2024"})
        .reset_index()
    )
    uf_wide = (
        by_uf.pivot_table(
            index=["SG_UF", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
            columns="ANO_ELEICAO",
            values="uf_lawsuits",
            fill_value=0,  # a UF with no cases of a subject in a year has 0 OWN cases
        )
        .rename(columns={2020: "uf_2020", 2024: "uf_2024"})
        .reset_index()
    )
    for frame, cols in ((national_wide, ["national_2020", "national_2024"]),
                        (uf_wide, ["uf_2020", "uf_2024"])):
        for column in cols:
            if column not in frame.columns:
                frame[column] = 0

    shifters = uf_wide.merge(
        national_wide,
        on=["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
        how="left",
        validate="many_to_one",
    )
    shifters["leave_uf_out_2020"] = shifters["national_2020"] - shifters["uf_2020"]
    shifters["leave_uf_out_2024"] = shifters["national_2024"] - shifters["uf_2024"]
    shifters["shock_log_growth_2020_2024"] = (
        np.log1p(shifters["leave_uf_out_2024"]) - np.log1p(shifters["leave_uf_out_2020"])
    )

    components = baseline.merge(
        shifters,
        on=["SG_UF", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
        how="left",
        validate="many_to_one",
    )
    components["shock_log_growth_2020_2024"] = components["shock_log_growth_2020_2024"].fillna(0.0)
    components["bartik_component"] = (
        components["baseline_share_2020"] * components["shock_log_growth_2020_2024"]
    )

    bartik = (
        components.groupby(["SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            bartik_iv_2020_2024=("bartik_component", "sum"),
            baseline_competition_lawsuits_2020=("n_lawsuits", "sum"),
            baseline_subjects_2020=("CD_ASSUNTO_PRINCIPAL", "nunique"),
        )
    )
    return municipality_subject, components, bartik


def build_municipality_judicialization_totals(
    municipal_panel: pd.DataFrame,
    case_flag: bool = True,
    prefix: str = "competition",
) -> pd.DataFrame:
    # case_flag=True/prefix="competition" -> adversarial caseload volume (the endogenous
    # treatment); case_flag=False/prefix="nonadversarial" -> excluded mandatory/admin
    # filing volume (the BHJ generic-shares intensity control).
    competition = municipal_panel[municipal_panel["competition_case"] == case_flag].copy()
    totals = (
        competition.groupby(["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            **{
                f"{prefix}_lawsuits": ("n_lawsuits", "sum"),
                f"{prefix}_subjects": ("CD_ASSUNTO_PRINCIPAL", "nunique"),
                f"{prefix}_families": ("topic_family", "nunique"),
            }
        )
    )
    wide = (
        totals.pivot_table(
            index=["SG_UF", "SG_UE", "NM_UE"],
            columns="ANO_ELEICAO",
            values=[f"{prefix}_lawsuits", f"{prefix}_subjects", f"{prefix}_families"],
            fill_value=0,
        )
    )
    wide.columns = [f"{name}_{year}" for name, year in wide.columns]
    wide = wide.reset_index()
    for year in TARGET_YEARS:
        wide[f"log1p_{prefix}_lawsuits_{year}"] = np.log1p(
            wide.get(f"{prefix}_lawsuits_{year}", 0)
        )
    wide[f"delta_log1p_{prefix}_lawsuits_2024_2020"] = (
        wide[f"log1p_{prefix}_lawsuits_2024"] - wide[f"log1p_{prefix}_lawsuits_2020"]
    )
    return wide


def load_candidates() -> pd.DataFrame:
    usecols = [
        "ANO_ELEICAO",
        "DT_ELEICAO",
        "NR_TURNO",
        "TP_ABRANGENCIA",
        "CD_TIPO_ELEICAO",
        "SG_UF",
        "SG_UE",
        "NM_UE",
        "DS_CARGO",
        "SQ_CANDIDATO",
        "NM_CANDIDATO",
        "NR_TITULO_ELEITORAL_CANDIDATO",
        "NR_PARTIDO",
        "NM_COLIGACAO",
        "DS_GENERO",
        "DS_GRAU_INSTRUCAO",
        "DS_ESTADO_CIVIL",
        "DS_COR_RACA",
        "DT_NASCIMENTO",
        "DS_SIT_TOT_TURNO",
    ]
    frames: list[pd.DataFrame] = []
    for year in TARGET_YEARS:
        path = RAW_DIR / f"consulta_cand_{year}" / f"consulta_cand_{year}_BRASIL.csv"
        if not path.exists():
            continue
        df = pd.read_csv(
            path,
            sep=";",
            encoding="latin-1",
            usecols=usecols,
            dtype=str,
            low_memory=False,
        )
        frames.append(df)
    if not frames:
        return pd.DataFrame()

    candidates = pd.concat(frames, ignore_index=True)
    candidates = candidates.loc[
        (candidates["TP_ABRANGENCIA"] == "MUNICIPAL")
        & (candidates["CD_TIPO_ELEICAO"] == "2")
        & (candidates["DS_CARGO"].isin(OFFICE_MAP))
    ].copy()
    candidates["ANO_ELEICAO"] = pd.to_numeric(candidates["ANO_ELEICAO"], errors="coerce")
    candidates["office_group"] = candidates["DS_CARGO"].map(OFFICE_MAP)
    candidates["DT_ELEICAO"] = pd.to_datetime(
        candidates["DT_ELEICAO"], format="%d/%m/%Y", errors="coerce"
    )
    candidates["NR_TURNO"] = pd.to_numeric(candidates["NR_TURNO"], errors="coerce")
    candidates["DT_NASCIMENTO"] = pd.to_datetime(
        candidates["DT_NASCIMENTO"], format="%d/%m/%Y", errors="coerce"
    )
    candidates["candidate_age"] = (
        (candidates["DT_ELEICAO"] - candidates["DT_NASCIMENTO"]).dt.days / 365.25
    )
    candidates["is_female"] = (candidates["DS_GENERO"] == "FEMININO").astype(int)
    # Accent-fold before matching: TSE files are latin-1 and the raw value is "INDIGENA"
    # with an accent (U+00CD); matching the literal accented/mojibake spelling silently
    # dropped every indigenous candidate (~2.2-2.6k/cycle) into the white bucket.
    candidates["is_nonwhite"] = candidates["DS_COR_RACA"].map(normalize_text).isin(
        ["PRETA", "PARDA", "AMARELA", "INDIGENA"]
    ).astype(int)
    candidates["is_higher_education"] = candidates["DS_GRAU_INSTRUCAO"].fillna("").str.contains(
        "SUPERIOR", regex=False
    ).astype(int)
    candidates["is_married"] = (candidates["DS_ESTADO_CIVIL"] == "CASADO(A)").astype(int)
    candidates["is_elected"] = candidates["DS_SIT_TOT_TURNO"].isin(ELECTED_STATUSES).astype(int)
    candidates["title_key"] = (
        candidates["NR_TITULO_ELEITORAL_CANDIDATO"].fillna("").str.strip()
    )
    candidates["title_key"] = candidates["title_key"].replace({"-4": "", "#NULO#": ""})
    candidates["person_key"] = (
        candidates["NM_CANDIDATO"].map(normalize_text)
        + "|"
        + candidates["DT_NASCIMENTO"].dt.strftime("%Y-%m-%d").fillna("")
    )
    candidates["person_key"] = candidates["title_key"].where(
        candidates["title_key"].ne(""),
        candidates["person_key"],
    )
    # Keep one row per candidate within year and municipality, preferring the later
    # turn when second-round rows duplicate first-round records.
    candidates = candidates.sort_values(
        ["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO", "NR_TURNO"]
    )
    candidates = candidates.drop_duplicates(
        subset=["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO"],
        keep="last",
    )
    return candidates


def add_candidate_history_flags(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    candidates = candidates.copy()
    baseline = candidates[candidates["ANO_ELEICAO"] == 2020].copy()
    baseline_keys = (
        baseline.loc[baseline["person_key"].ne(""), ["SG_UF", "SG_UE", "office_group", "person_key"]]
        .drop_duplicates()
        .assign(ran_in_2020=1)
    )
    elected_keys = (
        baseline.loc[
            (baseline["person_key"].ne("")) & (baseline["is_elected"] == 1),
            ["SG_UF", "SG_UE", "office_group", "person_key"],
        ]
        .drop_duplicates()
        .assign(elected_in_2020=1)
    )

    candidates = candidates.merge(
        baseline_keys,
        on=["SG_UF", "SG_UE", "office_group", "person_key"],
        how="left",
    )
    candidates = candidates.merge(
        elected_keys,
        on=["SG_UF", "SG_UE", "office_group", "person_key"],
        how="left",
    )
    candidates["ran_in_2020"] = candidates["ran_in_2020"].fillna(0).astype(int)
    candidates["elected_in_2020"] = candidates["elected_in_2020"].fillna(0).astype(int)
    candidates["is_new_candidate_vs_2020"] = (
        (candidates["ANO_ELEICAO"] == 2024)
        & candidates["person_key"].ne("")
        & (candidates["ran_in_2020"] == 0)
    ).astype(int)
    candidates["is_incumbent_from_2020"] = (
        (candidates["ANO_ELEICAO"] == 2024)
        & candidates["person_key"].ne("")
        & (candidates["elected_in_2020"] == 1)
    ).astype(int)
    candidates["is_reelected_incumbent_2024"] = (
        (candidates["is_incumbent_from_2020"] == 1) & (candidates["is_elected"] == 1)
    ).astype(int)
    return candidates


def safe_mean(series: pd.Series) -> float:
    valid = series.dropna()
    if valid.empty:
        return float("nan")
    return float(valid.mean())


def safe_sum(series: pd.Series) -> int:
    return int(series.fillna(0).sum())


def summarize_office_outcomes(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()

    outcomes = (
        candidates.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            total_candidates=("SQ_CANDIDATO", "nunique"),
            elected_candidates=("is_elected", "sum"),
            party_count=("NR_PARTIDO", lambda s: s.fillna("").replace("", pd.NA).dropna().nunique()),
            coalition_count=("NM_COLIGACAO", lambda s: s.fillna("").replace("", pd.NA).dropna().nunique()),
            female_share=("is_female", "mean"),
            nonwhite_share=("is_nonwhite", "mean"),
            higher_education_share=("is_higher_education", "mean"),
            married_share=("is_married", "mean"),
            mean_age=("candidate_age", "mean"),
            sd_age=("candidate_age", "std"),
            elected_female_share=("is_female", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            elected_nonwhite_share=("is_nonwhite", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            elected_higher_education_share=("is_higher_education", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            elected_mean_age=("candidate_age", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            new_candidate_count=("is_new_candidate_vs_2020", safe_sum),
            incumbent_candidate_count=("is_incumbent_from_2020", safe_sum),
            incumbent_reelected_count=("is_reelected_incumbent_2024", safe_sum),
        )
    )

    denominator = outcomes["total_candidates"].replace(0, np.nan)
    elected_denominator = outcomes["elected_candidates"].replace(0, np.nan)
    outcomes["new_candidate_share"] = outcomes["new_candidate_count"] / denominator
    outcomes["incumbent_candidate_share"] = outcomes["incumbent_candidate_count"] / denominator
    outcomes["incumbent_reelected_share"] = (
        outcomes["incumbent_reelected_count"] / elected_denominator
    )
    outcomes["candidate_hhi_party"] = np.nan
    outcomes["effective_party_count_candidates"] = np.nan

    party_counts = (
        candidates.groupby(
            ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NR_PARTIDO"],
            as_index=False,
        )
        .agg(n_candidates=("SQ_CANDIDATO", "nunique"))
    )
    party_totals = party_counts.groupby(
        ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        as_index=False,
    )["n_candidates"].sum().rename(columns={"n_candidates": "total_candidates_tmp"})
    party_counts = party_counts.merge(
        party_totals,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left",
        validate="many_to_one",
    )
    party_counts["party_share"] = party_counts["n_candidates"] / party_counts["total_candidates_tmp"]
    concentration = (
        party_counts.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"], as_index=False)
        .agg(
            candidate_hhi_party=("party_share", lambda s: float((s**2).sum())),
            effective_party_count_candidates=("party_share", lambda s: float(1 / (s**2).sum()) if (s**2).sum() > 0 else np.nan),
        )
    )
    outcomes = outcomes.merge(
        concentration,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_calc"),
    )
    outcomes["candidate_hhi_party"] = outcomes["candidate_hhi_party_calc"]
    outcomes["effective_party_count_candidates"] = outcomes["effective_party_count_candidates_calc"]
    outcomes = outcomes.drop(
        columns=["candidate_hhi_party_calc", "effective_party_count_candidates_calc"]
    )
    return outcomes


def build_design_for_office(
    office_group: str,
    municipality_universe: pd.DataFrame,
    judicialization_totals: pd.DataFrame,
    bartik: pd.DataFrame,
    office_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    office_panel = office_outcomes[office_outcomes["office_group"] == office_group].copy()
    bartik_cols = [
        "SG_UF", "SG_UE", "NM_UE",
        "bartik_iv_2020_2024", "baseline_competition_lawsuits_2020", "baseline_subjects_2020",
    ]
    # Carry the placebo shift-share + its baseline counts when present (added in main()).
    for column in [
        "placebo_bartik_iv_2020_2024",
        "baseline_nonadversarial_lawsuits_2020",
        "baseline_nonadversarial_subjects_2020",
    ]:
        if column in bartik.columns:
            bartik_cols.append(column)
    design = municipality_universe.merge(
        bartik[bartik_cols]
        .drop_duplicates()
        .merge(judicialization_totals, on=["SG_UF", "SG_UE", "NM_UE"], how="outer"),
        on=["SG_UF", "SG_UE", "NM_UE"],
        how="left",
    )

    fill_zero_cols = [
        "bartik_iv_2020_2024",
        "baseline_competition_lawsuits_2020",
        "baseline_subjects_2020",
        "competition_families_2020",
        "competition_families_2024",
        "competition_lawsuits_2020",
        "competition_lawsuits_2024",
        "competition_subjects_2020",
        "competition_subjects_2024",
        "log1p_competition_lawsuits_2020",
        "log1p_competition_lawsuits_2024",
        "delta_log1p_competition_lawsuits_2024_2020",
        # Placebo / non-adversarial intensity (zero where a muni has no excluded filings).
        "placebo_bartik_iv_2020_2024",
        "baseline_nonadversarial_lawsuits_2020",
        "baseline_nonadversarial_subjects_2020",
        "nonadversarial_families_2020",
        "nonadversarial_families_2024",
        "nonadversarial_lawsuits_2020",
        "nonadversarial_lawsuits_2024",
        "nonadversarial_subjects_2020",
        "nonadversarial_subjects_2024",
        "log1p_nonadversarial_lawsuits_2020",
        "log1p_nonadversarial_lawsuits_2024",
        "delta_log1p_nonadversarial_lawsuits_2024_2020",
    ]
    for column in fill_zero_cols:
        if column in design.columns:
            design[column] = design[column].fillna(0)

    if not office_panel.empty:
        value_cols = [
            col for col in office_panel.columns
            if col not in {"office_group", "SG_UF", "SG_UE", "NM_UE", "ANO_ELEICAO"}
        ]
        # Pivot with NaN for missing muni x office x year cells. A blanket
        # fill_value=0 would turn a missing year into fake zeros for continuous
        # levels (mean_age, sd_age, elected_mean_age) and shares, corrupting the
        # delta outcomes. Zero-fill ONLY genuine counts below.
        office_wide = office_panel.pivot_table(
            index=["SG_UF", "SG_UE"],
            columns="ANO_ELEICAO",
            values=value_cols,
        )
        office_count_cols = {
            "total_candidates", "elected_candidates", "party_count",
            "coalition_count", "new_candidate_count", "incumbent_candidate_count",
            "incumbent_reelected_count",
        }
        for name, year in office_wide.columns:
            if name in office_count_cols:
                office_wide[(name, year)] = office_wide[(name, year)].fillna(0)
        office_wide.columns = [f"{name}_{year}" for name, year in office_wide.columns]
        office_wide = office_wide.reset_index()
        design = design.merge(office_wide, on=["SG_UF", "SG_UE"], how="left")

    rename_map = {
        "total_candidates_2020": "total_candidates_2020",
        "total_candidates_2024": "total_candidates_2024",
    }
    design = design.rename(columns=rename_map)

    if "total_candidates_2020" in design.columns and "total_candidates_2024" in design.columns:
        design["delta_total_candidates_2024_2020"] = (
            design["total_candidates_2024"] - design["total_candidates_2020"]
        )
    if "female_share_2020" in design.columns and "female_share_2024" in design.columns:
        design["delta_female_share_2024_2020"] = (
            design["female_share_2024"] - design["female_share_2020"]
        )
    if "candidate_hhi_party_2020" in design.columns and "candidate_hhi_party_2024" in design.columns:
        design["delta_candidate_hhi_party_2024_2020"] = (
            design["candidate_hhi_party_2024"] - design["candidate_hhi_party_2020"]
        )
    if (
        "effective_party_count_candidates_2020" in design.columns
        and "effective_party_count_candidates_2024" in design.columns
    ):
        design["delta_effective_party_count_candidates_2024_2020"] = (
            design["effective_party_count_candidates_2024"]
            - design["effective_party_count_candidates_2020"]
        )
    return design


def build_municipality_universe(
    zone_lookup: pd.DataFrame,
    office_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    universe = (
        zone_lookup.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg(NM_UE=("NM_UE", "first"))
    )
    if not office_outcomes.empty:
        outcome_universe = (
            office_outcomes.groupby(["SG_UF", "SG_UE"], as_index=False)
            .agg(NM_UE=("NM_UE", "first"))
        )
        universe = (
            pd.concat([universe, outcome_universe], ignore_index=True)
            .groupby(["SG_UF", "SG_UE"], as_index=False)
            .agg(NM_UE=("NM_UE", "first"))
        )
    return universe


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    crosswalk = load_crosswalk()
    zone_lookup = load_zone_lookup()
    # zone_lookup is now used only as the municipality-name / universe source —
    # lawsuits are resolved to municipality directly by SIG, with no zona merge.
    nm_ue_by_code = (
        zone_lookup.drop_duplicates("SG_UE").set_index("SG_UE")["NM_UE"].to_dict()
    )
    municipal_panel = build_sig_municipal_panel(crosswalk, nm_ue_by_code)
    municipality_subject, bartik_components, bartik = build_municipality_bartik_components(
        municipal_panel
    )
    judicialization_totals = build_municipality_judicialization_totals(municipal_panel)

    # Non-adversarial (excluded mandatory/administrative filings): placebo shift-share
    # + intensity volume for the BHJ generic-shares diagnostic. Same construction as the
    # adversarial instrument, over the complementary subset; merged onto the design so the
    # estimation can (a) add log non-adversarial volume as a control and (b) run the
    # placebo IV and condition the main result on it.
    _, _, placebo_bartik = build_municipality_bartik_components(
        municipal_panel, case_flag=False
    )
    placebo_bartik = placebo_bartik.rename(
        columns={
            "bartik_iv_2020_2024": "placebo_bartik_iv_2020_2024",
            "baseline_competition_lawsuits_2020": "baseline_nonadversarial_lawsuits_2020",
            "baseline_subjects_2020": "baseline_nonadversarial_subjects_2020",
        }
    )
    nonadversarial_totals = build_municipality_judicialization_totals(
        municipal_panel, case_flag=False, prefix="nonadversarial"
    )
    bartik = bartik.merge(placebo_bartik, on=["SG_UF", "SG_UE", "NM_UE"], how="outer")
    judicialization_totals = judicialization_totals.merge(
        nonadversarial_totals, on=["SG_UF", "SG_UE", "NM_UE"], how="outer"
    )

    candidates = load_candidates()
    candidates = add_candidate_history_flags(candidates)
    office_outcomes = summarize_office_outcomes(candidates)
    municipality_universe = build_municipality_universe(zone_lookup, office_outcomes)

    executive_design = build_design_for_office(
        "executive",
        municipality_universe,
        judicialization_totals,
        bartik,
        office_outcomes,
    )
    legislative_design = build_design_for_office(
        "legislative",
        municipality_universe,
        judicialization_totals,
        bartik,
        office_outcomes,
    )

    municipality_subject.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "municipality_competition_subject_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    bartik_components.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "municipality_bartik_components.csv",
        index=False,
        encoding="utf-8-sig",
    )
    office_outcomes.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "office_candidate_outcomes_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    executive_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "executive_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )
    legislative_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "legislative_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("Wrote office-specific shift-share inputs.")


if __name__ == "__main__":
    main()

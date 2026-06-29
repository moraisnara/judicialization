# Office-Specific Shift-Share Setup

Lawsuits come from the SIG TSE microdata export, which resolves each case to
its **municipality of origin** directly. Only first-instance (`Originário`)
cases filed before first-round election day are kept. This replaces the old
zona-eleitoral panel and its zona->municipality many-to-many merge, which
duplicated each multi-municipality zona's caseload across its municipalities.

## Core Choices

- exposure unit: municipality, resolved directly by SIG (no zona expansion)
- treatment universe: adversarial lawsuits only (administrative and procedural
  classes/subjects excluded via DROP_CLASSES and DROP_SUBJECTS in 02_bartik_inputs.py)
- outcome panels are separated by office sought
- executive office: `PREFEITO`
- legislative office: `VEREADOR`

## Derived Files

- `data/clean/office_candidate_outcomes_panel.csv`
- `data/clean/municipality_competition_subject_panel.csv`
- `data/clean/municipality_bartik_components.csv`
- `data/clean/executive_shift_share_design.csv`
- `data/clean/legislative_shift_share_design.csv`

## Coverage

- office outcome rows: 22,274
- executive design municipalities: 5,571
- legislative design municipalities: 5,571

## Notes

- `new_candidate_*` and `incumbent_*` variables are defined only relative to 2020 and
  therefore are substantively meaningful for 2024 outcomes.
- candidate-file-based concentration metrics (`candidate_hhi_party`,
  `effective_party_count_candidates`) are useful fragmentation proxies, but not a full
  ideological polarization measure.
# Office-Specific Shift-Share Setup

This setup uses only first-instance (`NR_INSTANCIA == 1`) electoral lawsuits,
which correspond to local `zonas eleitorais`, and maps them to municipalities.

## Core Choices

- exposure unit: municipality, aggregated from first-instance zona-eleitoral outputs
- main treatment universe: competition-relevant subject codes only
- primary robustness specification: exclude `11618 = RRC - Candidato`
- outcome panels are separated by office sought
- executive office: `PREFEITO`
- legislative office: `VEREADOR`

## Derived Files

- `data/derived/office_candidate_outcomes_panel.csv`
- `data/derived/municipality_competition_subject_panel.csv`
- `data/derived/municipality_bartik_components.csv`
- `data/derived/executive_shift_share_design.csv`
- `data/derived/legislative_shift_share_design.csv`

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
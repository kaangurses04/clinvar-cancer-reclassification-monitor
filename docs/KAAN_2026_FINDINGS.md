# My 2026 ClinVar Classification–Evidence Study

## Research question

For six hereditary-cancer genes—`ATM`, `BRCA1`, `BRCA2`, `CHEK2`, `PALB2`, and
`TP53`—which aggregate germline classification changes between the January 4 and
September 28, 2026 ClinVar GRCh38 releases occurred alongside stronger, weaker, or
unchanged review-star levels?

My focus is on the relationship between classification changes and review-star changes
across these two releases.

## Validated result

The workflow compared 66,526 selected records in the earlier release with 69,423 in the
later release. It found 1,018 grouped classification changes.

| Review-evidence direction during a classification change | Variants | Share of classification changes |
|---|---:|---:|
| Strengthened | 327 | 32.1% |
| Same star level | 401 | 39.4% |
| Weakened | 290 | 28.5% |
| **Total** | **1,018** | **100.0%** |

The workflow separately found 1,314 records whose grouped classification remained
stable while the review-status text changed: 1,310 strengthened in star level and four
weakened.

## Gene-level classification changes

| Gene | Strengthened | Same star level | Weakened | Total |
|---|---:|---:|---:|---:|
| ATM | 96 | 139 | 119 | 354 |
| BRCA1 | 53 | 44 | 35 | 132 |
| BRCA2 | 69 | 95 | 70 | 234 |
| CHEK2 | 21 | 13 | 18 | 52 |
| PALB2 | 29 | 59 | 30 | 118 |
| TP53 | 59 | 51 | 18 | 128 |
| **Total** | **327** | **401** | **290** | **1,018** |

## Interpretation and limitations

The main finding is not that a classification change became more or less correct. Review
stars summarize ClinVar's review status; they are not probabilities of correctness. The
two-axis result instead shows that classification movement and review-evidence movement
are related but distinct events.

The most frequent grouped transition was `Uncertain significance → Conflicting` (395
records). That should not be described as a pathogenic or benign reclassification. It
usually signals that the aggregate database label now represents disagreement among
submissions. Several other common transitions, such as `Pathogenic → Pathogenic / likely
pathogenic`, may reflect aggregation terminology rather than a movement across a clinical
decision boundary.

Therefore, the matrix is best used as an audit and review-navigation tool. Any individual
record still requires inspection of its current ClinVar page, contributing submissions,
conditions, dates, and primary evidence by qualified professionals.

## How this fits into my project

My analysis focuses on six genes and two dated releases. The code generates the
classification–evidence matrix from the comparison outputs, and the dashboard
presents the same categories through a filter and chart.

My next steps are to validate the workflow personally, document what I learn, and
maintain future improvements through this repository.

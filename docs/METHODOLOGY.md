# Methodology

## Objective

Detect changes in ClinVar aggregate germline classifications and their supporting review
status across two dated GRCh38 VCF releases for a focused hereditary-cancer gene panel.

## Inputs

The workflow accepts local VCF 4.1 files, either plain text or gzip compressed. Official
ClinVar GRCh38 VCF releases can be downloaded through the command-line interface from the
NCBI archive.

## Record selection

1. Parse the `GENEINFO` INFO tag as `symbol:GeneID` pairs separated by `|`.
2. Match target symbols exactly after converting the configured symbols to uppercase.
3. Retain variants that intersect the target panel and have a direct `CLNSIG` value.
4. Exclude included-only variants without a direct aggregate germline classification.

## Stable identifier

The VCF `ID` column is the ClinVar Variation ID. It is used as the cross-release key.
Position, reference, and alternate alleles are retained for inspection but are not used
as the primary key because genomic representations may evolve.

## Classification grouping

Raw `CLNSIG` values are retained. A second field groups values for summary charts:

- Pathogenic
- Pathogenic / likely pathogenic
- Likely pathogenic
- Uncertain significance
- Conflicting
- Likely benign
- Benign / likely benign
- Benign
- Risk factor
- Drug response
- Protective
- Other

Grouping is intentionally rule-based and transparent. It is not a clinical assertion.

## Review status

Raw `CLNREVSTAT` is retained and mapped to the public 0–4 star representation described
by ClinVar. Review status is analyzed independently of classification.

## Comparison logic

An outer join by Variation ID assigns exactly one comparison outcome:

1. Removed from later release
2. Added in later release
3. Classification changed
4. Review status changed
5. Unchanged

If both classification and review status changed, the record is counted as
`Classification changed`; both before/after review values remain in the output.

## Classification–evidence context

My analysis keeps two dimensions separate:

1. **What changed?** Classification, review status only, record presence, or nothing.
2. **How did the review-star level move?** Strengthened, weakened, unchanged, or not
   comparable for an added/removed record.

Every record receives a transparent `review_evidence_direction` and
`evidence_context`. The generated `change_evidence_matrix.csv` cross-tabulates these
dimensions, and the dashboard allows the user to filter them. This is deliberately not
a risk score, clinical priority, or claim that more stars make a classification true.

## Quality controls

- malformed rows with fewer than eight VCF fields raise an error;
- at least one gene must be configured;
- output identifier fields remain strings;
- numeric position and star fields receive explicit types;
- duplicate Variation IDs are deterministically reduced after sorting;
- unit tests cover parsing, star mapping, grouping, every comparison outcome, and output
  generation;
- the demo is synthetic and visibly labeled.

## Reproducibility

The exact release labels, source files, gene list, code version, and generated outputs
should be retained together. Raw official VCFs are not committed because of their size,
but dated releases are retrievable from the NCBI archive.

## Interpretation boundary

This workflow detects database changes; it does not adjudicate them. A scientifically
responsible follow-up would inspect the current VCV record, contributing SCVs, assertion
criteria, literature, and expert-panel guidance.


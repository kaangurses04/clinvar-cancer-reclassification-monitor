# ClinVar Hereditary-Cancer Reclassification Report

## Comparison

- Earlier release: **2026-01-04** (66,526 selected variants)
- Later release: **2026-09-28** (69,423 selected variants)
- Genes: **ATM, BRCA1, BRCA2, CHEK2, PALB2, TP53**
- Classification changes: **1,018**
- Review-status-only changes: **1,314**
- Added in the later release: **2,937**
- Removed from the later release: **40**

## Interpretation

This report detects record-level changes between two public ClinVar VCF releases using
the stable ClinVar Variation ID. A detected change means that the aggregate value in
ClinVar differs between releases. It does **not** establish why a submitter changed an
interpretation, nor does it independently validate a classification.

## Evidence quality

ClinVar review stars describe the review status supporting an aggregate classification.
They are not a numerical probability that a classification is correct. This workflow
reports review-status changes separately from classification changes.

## Classification–evidence context

The project adds a two-axis audit that asks whether a classification change occurred
while the ClinVar review-star level strengthened, weakened, or stayed the same. This
context prevents a classification change and an evidence-review change from being
collapsed into one misleading score. It is descriptive and is not a clinical ranking.

## Files

- `notable_changes.csv`: records added, removed, or changed
- `variant_comparison.csv`: complete outer-join comparison
- `classification_counts.csv`: classification counts by gene and release
- `gene_change_summary.csv`: comparison outcomes by gene
- `change_evidence_matrix.csv`: change type cross-tabulated by review-evidence direction
- `quality_summary.json`: machine-readable run summary
- `figures/`: generated visualizations

## Important limitation

This software is an educational research portfolio project. It must not be used for
patient care, diagnosis, treatment, genetic counseling, or clinical variant interpretation.
Always inspect the current ClinVar record and primary evidence with qualified professionals.

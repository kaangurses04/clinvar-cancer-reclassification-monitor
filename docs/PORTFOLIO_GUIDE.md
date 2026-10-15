# Portfolio and Interview Guide

## My project description

This is my personal bioinformatics portfolio project. I am using it to develop my
understanding of genomic data, Python workflows, reproducibility, and testing.

**ClinVar Hereditary-Cancer Reclassification Monitor — Python, pandas, Streamlit, Git**

My project compares official ClinVar releases for six hereditary-cancer genes. The
workflow streams VCF files, matches records by Variation ID, separates classification
changes from review-status changes, and presents tables, figures, and a dashboard.

I describe it as an educational database-monitoring project. It does not diagnose
disease or predict pathogenicity.

## Thirty-second explanation

“ClinVar changes as laboratories and expert panels submit new evidence. My project uses a Python
workflow that compares two dated ClinVar releases for six hereditary-cancer genes. It
streams the large VCF files, matches records by stable Variation ID, detects classification
and review-status changes, and generates reproducible tables, figures, and a dashboard. It
is an educational database-monitoring tool, not a clinical decision system.”

## Questions I am learning to explain

### Why use Variation ID instead of chromosome and position?

The ClinVar VCF defines its `ID` column as the ClinVar Variation ID. It is a database-level
identifier intended to represent the variant record, while coordinates and representations
can evolve across genome mappings and release processing.

### Why stream the VCF?

Official compressed releases are commonly hundreds of megabytes. Streaming allows the
workflow to retain only the selected genes rather than loading the entire file into memory.

### What is the difference between `CLNSIG` and `CLNREVSTAT`?

`CLNSIG` is ClinVar's aggregate germline classification. `CLNREVSTAT` describes the level
of review, transparency, and consensus supporting that aggregate classification.

### Do more review stars mean the variant is more pathogenic?

No. Stars describe review status, not the direction or probability of pathogenicity. A
benign classification can have strong review status, and a pathogenic classification can
have limited review status.

### Why not train a machine-learning pathogenicity model?

The objective is traceable database monitoring. A predictive model would require careful
feature design, independent validation, leakage controls, and a clinically defensible use
case. Adding machine learning without those elements would make the project less reliable.

### What would you improve next?

Possible extensions include parsing the comprehensive VCV XML, analyzing individual SCV
submissions, preserving release hashes in a run manifest, and adding automated scheduled
comparisons. Any extension should preserve the nonclinical scope.

## My next steps

1. Run the workflow and tests myself.
2. Read the parser and comparison functions until I can explain them.
3. Explore the packaged official-release results alongside the synthetic demo.
4. Review selected records against their current ClinVar pages.
5. Write down what I learned and changed.
6. Commit a meaningful improvement.
7. Record a future improvement as a GitHub issue.
8. Keep person-level genetic data out of this repository.

See [`PROJECT_OWNERSHIP.md`](PROJECT_OWNERSHIP.md) for my learning and maintenance checklist.

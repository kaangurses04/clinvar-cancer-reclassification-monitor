# Data directory

## `demo/`

Contains a deliberately small, synthetic VCF pair used by the unit tests and dashboard
demonstration. All records have `DEMO` identifiers and must not be interpreted as real
clinical variants.

## `raw/`

Destination for official ClinVar `.vcf.gz` releases. These files are large and are
excluded from Git by `.gitignore`. Download them reproducibly with the project CLI.

Do not commit patient data, protected health information, direct-to-consumer genetic
files, or any other person-level genomic data to this repository.


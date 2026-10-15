"""Streaming utilities for ClinVar VCF 4.1 files.

The parser intentionally uses only the Python standard library plus pandas.
Official ClinVar releases can exceed 150 MB compressed, so records are read
one line at a time and only selected genes are retained in memory.
"""

from __future__ import annotations

from contextlib import contextmanager
import gzip
from pathlib import Path
from typing import Iterable, Iterator, TextIO
from urllib.parse import unquote

import pandas as pd


OUTPUT_COLUMNS = [
    "variation_id",
    "chromosome",
    "position",
    "reference",
    "alternate",
    "selected_genes",
    "all_genes",
    "clinical_significance",
    "classification_group",
    "review_status",
    "review_stars",
    "conditions",
    "variant_type",
    "molecular_consequence",
    "hgvs",
    "rsid",
    "allele_id",
]


def decode_vcf_text(value: str | None) -> str:
    """Convert common ClinVar VCF text encoding into readable text."""
    if not value or value == ".":
        return ""
    return unquote(value).replace("_", " ")


def parse_info(info_text: str) -> dict[str, str]:
    """Parse the semicolon-delimited VCF INFO field."""
    parsed: dict[str, str] = {}
    for item in info_text.strip().split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            parsed[key] = value
        else:
            parsed[item] = "true"
    return parsed


def parse_gene_symbols(gene_info: str | None) -> list[str]:
    """Extract gene symbols from GENEINFO values such as BRCA1:672|NBR2:10230."""
    if not gene_info or gene_info == ".":
        return []
    symbols: list[str] = []
    for pair in gene_info.split("|"):
        symbol = pair.rsplit(":", 1)[0].strip()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols


def review_stars(review_status: str | None) -> int:
    """Map ClinVar aggregate germline review text to its displayed star count."""
    status = decode_vcf_text(review_status).lower()
    if (
        not status
        or "no assertion criteria" in status
        or "no classification" in status
        or "not classified" in status
    ):
        return 0
    if "practice guideline" in status:
        return 4
    if "reviewed by expert panel" in status:
        return 3
    if "multiple submitters" in status and "no conflicts" in status:
        return 2
    if "criteria provided" in status:
        return 1
    return 0


def classification_group(classification: str | None) -> str:
    """Collapse ClinVar germline classifications into readable analysis groups."""
    value = decode_vcf_text(classification).strip()
    lower = value.lower()
    if not value:
        return "No direct classification"
    if "conflicting" in lower:
        return "Conflicting"
    if "uncertain significance" in lower:
        return "Uncertain significance"
    if "pathogenic" in lower:
        if "/" in lower and "likely pathogenic" in lower:
            return "Pathogenic / likely pathogenic"
        if "likely pathogenic" in lower:
            return "Likely pathogenic"
        return "Pathogenic"
    if "benign" in lower:
        if "/" in lower and "likely benign" in lower:
            return "Benign / likely benign"
        if "likely benign" in lower:
            return "Likely benign"
        return "Benign"
    if "risk factor" in lower:
        return "Risk factor"
    if "drug response" in lower:
        return "Drug response"
    if "protective" in lower:
        return "Protective"
    return "Other"


@contextmanager
def open_vcf_text(path: str | Path) -> Iterator[TextIO]:
    """Open a plain-text or gzip-compressed local VCF file."""
    source = Path(path)
    if source.suffix == ".gz":
        with gzip.open(source, "rt", encoding="utf-8", errors="replace") as handle:
            yield handle
    else:
        with source.open("rt", encoding="utf-8", errors="replace") as handle:
            yield handle


def iter_selected_records(
    vcf_path: str | Path,
    genes: Iterable[str],
) -> Iterator[dict[str, object]]:
    """Yield directly classified records associated with one or more target genes."""
    target_genes = {gene.strip().upper() for gene in genes if gene.strip()}
    if not target_genes:
        raise ValueError("At least one target gene is required.")

    with open_vcf_text(vcf_path) as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 8:
                raise ValueError(f"Malformed VCF row at line {line_number}: expected 8 fields")

            chrom, pos, variation_id, ref, alt, _qual, _filter, info_text = fields[:8]
            info = parse_info(info_text)
            all_genes = parse_gene_symbols(info.get("GENEINFO"))
            selected = sorted({symbol.upper() for symbol in all_genes}.intersection(target_genes))
            if not selected or not info.get("CLNSIG"):
                continue

            clinical_significance = decode_vcf_text(info.get("CLNSIG")).replace("|", " | ")
            review_status = decode_vcf_text(info.get("CLNREVSTAT")).replace(",", ", ")

            yield {
                "variation_id": str(variation_id),
                "chromosome": str(chrom),
                "position": int(pos),
                "reference": ref,
                "alternate": alt,
                "selected_genes": "|".join(selected),
                "all_genes": "|".join(all_genes),
                "clinical_significance": clinical_significance,
                "classification_group": classification_group(info.get("CLNSIG")),
                "review_status": review_status,
                "review_stars": review_stars(info.get("CLNREVSTAT")),
                "conditions": decode_vcf_text(info.get("CLNDN")).replace("|", " | "),
                "variant_type": decode_vcf_text(info.get("CLNVC")),
                "molecular_consequence": decode_vcf_text(info.get("MC")).replace("|", ": "),
                "hgvs": decode_vcf_text(info.get("CLNHGVS")),
                "rsid": info.get("RS", ""),
                "allele_id": info.get("ALLELEID", ""),
            }


def extract_variants(vcf_path: str | Path, genes: Iterable[str]) -> pd.DataFrame:
    """Return selected ClinVar records as a consistently typed DataFrame."""
    records = list(iter_selected_records(vcf_path, genes))
    frame = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    if frame.empty:
        return frame

    frame["variation_id"] = frame["variation_id"].astype("string")
    frame["position"] = pd.to_numeric(frame["position"], errors="coerce").astype("Int64")
    frame["review_stars"] = pd.to_numeric(frame["review_stars"], errors="coerce").fillna(0).astype(int)

    # ClinVar Variation ID is the stable comparison key. Duplicate rows are
    # unexpected in the standard VCF but are resolved deterministically.
    frame = (
        frame.sort_values(["variation_id", "chromosome", "position"])
        .drop_duplicates(subset=["variation_id"], keep="first")
        .reset_index(drop=True)
    )
    return frame


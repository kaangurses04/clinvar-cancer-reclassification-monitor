"""Comparison, summaries, visualizations, and report generation."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def compare_releases(earlier: pd.DataFrame, later: pd.DataFrame) -> pd.DataFrame:
    """Compare two extracted ClinVar releases by stable Variation ID."""
    required = {"variation_id", "classification_group", "review_status", "review_stars", "selected_genes"}
    for label, frame in (("earlier", earlier), ("later", later)):
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{label} release is missing columns: {sorted(missing)}")

    merged = earlier.merge(
        later,
        on="variation_id",
        how="outer",
        suffixes=("_earlier", "_later"),
        indicator=True,
    )

    def choose_change(row: pd.Series) -> str:
        if row["_merge"] == "left_only":
            return "Removed from later release"
        if row["_merge"] == "right_only":
            return "Added in later release"
        if row["classification_group_earlier"] != row["classification_group_later"]:
            return "Classification changed"
        if row["review_status_earlier"] != row["review_status_later"]:
            return "Review status changed"
        return "Unchanged"

    merged["change_type"] = merged.apply(choose_change, axis=1)
    merged["selected_genes"] = merged["selected_genes_later"].fillna(merged["selected_genes_earlier"])
    merged["classification_transition"] = (
        merged["classification_group_earlier"].fillna("Not present")
        + " → "
        + merged["classification_group_later"].fillna("Not present")
    )
    merged["review_transition"] = (
        merged["review_status_earlier"].fillna("Not present")
        + " → "
        + merged["review_status_later"].fillna("Not present")
    )
    earlier_stars = pd.to_numeric(merged["review_stars_earlier"], errors="coerce")
    later_stars = pd.to_numeric(merged["review_stars_later"], errors="coerce")
    merged["star_delta"] = later_stars - earlier_stars
    merged["review_evidence_direction"] = merged["star_delta"].map(
        lambda delta: (
            "Not comparable"
            if pd.isna(delta)
            else "Strengthened"
            if delta > 0
            else "Weakened"
            if delta < 0
            else "Same star level"
        )
    )

    def evidence_context(row: pd.Series) -> str:
        """Combine what changed with the direction of review-evidence movement."""
        change = row["change_type"]
        direction = row["review_evidence_direction"]
        if change == "Classification changed":
            return f"Classification changed; review {direction.lower()}"
        if change == "Review status changed":
            return f"Classification stable; review {direction.lower()}"
        if change == "Added in later release":
            return "New record; evidence not comparable"
        if change == "Removed from later release":
            return "Not in later release; evidence not comparable"
        return "No detected change"

    merged["evidence_context"] = merged.apply(evidence_context, axis=1)
    merged["clinvar_url"] = "https://www.ncbi.nlm.nih.gov/clinvar/variation/" + merged["variation_id"].astype(str) + "/"

    priority = {
        "Classification changed": 0,
        "Review status changed": 1,
        "Added in later release": 2,
        "Removed from later release": 3,
        "Unchanged": 4,
    }
    merged["_priority"] = merged["change_type"].map(priority)
    merged = merged.sort_values(["_priority", "selected_genes", "variation_id"]).drop(columns=["_priority", "_merge"])
    return merged.reset_index(drop=True)


def _explode_genes(frame: pd.DataFrame, column: str = "selected_genes") -> pd.DataFrame:
    exploded = frame.copy()
    exploded[column] = exploded[column].fillna("").str.split("|")
    exploded = exploded.explode(column)
    return exploded[exploded[column].ne("")]


def classification_counts(
    earlier: pd.DataFrame,
    later: pd.DataFrame,
    earlier_label: str,
    later_label: str,
) -> pd.DataFrame:
    """Count classifications by selected gene and release."""
    frames: list[pd.DataFrame] = []
    for release, label in ((earlier, earlier_label), (later, later_label)):
        exploded = _explode_genes(release)
        counts = (
            exploded.groupby(["selected_genes", "classification_group"], dropna=False)
            .size()
            .rename("variant_count")
            .reset_index()
        )
        counts["release"] = label
        frames.append(counts)
    return pd.concat(frames, ignore_index=True)[
        ["release", "selected_genes", "classification_group", "variant_count"]
    ]


def gene_change_summary(comparison: pd.DataFrame) -> pd.DataFrame:
    """Count release-comparison outcomes by gene."""
    exploded = _explode_genes(comparison)
    summary = (
        exploded.groupby(["selected_genes", "change_type"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"selected_genes": "gene"})
    )
    summary.columns.name = None
    return summary


def change_evidence_matrix(comparison: pd.DataFrame) -> pd.DataFrame:
    """Count comparison outcomes against review-evidence direction.

    This two-axis audit keeps classification movement separate from changes in the
    ClinVar review-star level. It is descriptive and is not a clinical priority score.
    """
    matrix = (
        comparison.groupby(["change_type", "review_evidence_direction"], dropna=False)
        .size()
        .rename("variant_count")
        .reset_index()
    )
    return matrix.sort_values(
        ["change_type", "review_evidence_direction"], ignore_index=True
    )


def _save_classification_plot(counts: pd.DataFrame, later_label: str, output: Path) -> None:
    later = counts[counts["release"] == later_label]
    pivot = later.pivot_table(
        index="selected_genes",
        columns="classification_group",
        values="variant_count",
        aggfunc="sum",
        fill_value=0,
    )
    preferred = [
        "Pathogenic",
        "Pathogenic / likely pathogenic",
        "Likely pathogenic",
        "Uncertain significance",
        "Conflicting",
        "Likely benign",
        "Benign / likely benign",
        "Benign",
        "Other",
    ]
    ordered = [col for col in preferred if col in pivot.columns] + [col for col in pivot.columns if col not in preferred]
    pivot = pivot[ordered]
    ax = pivot.plot(kind="bar", stacked=True, figsize=(11, 6), colormap="tab20c")
    ax.set_title(f"Germline classifications by gene — {later_label}")
    ax.set_xlabel("Gene")
    ax.set_ylabel("ClinVar variants")
    ax.legend(title="Classification", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(output, dpi=180, bbox_inches="tight")
    plt.close()


def _save_change_plot(comparison: pd.DataFrame, output: Path) -> None:
    counts = comparison["change_type"].value_counts().sort_values()
    colors = ["#8795a1" if label == "Unchanged" else "#1f77b4" for label in counts.index]
    ax = counts.plot(kind="barh", figsize=(9, 4.8), color=colors)
    ax.set_title("Variant comparison outcomes")
    ax.set_xlabel("Number of variants")
    ax.set_ylabel("")
    for container in ax.containers:
        ax.bar_label(container, padding=3, fontsize=9)
    plt.tight_layout()
    plt.savefig(output, dpi=180, bbox_inches="tight")
    plt.close()


def _save_review_plot(later: pd.DataFrame, later_label: str, output: Path) -> None:
    exploded = _explode_genes(later)
    pivot = exploded.pivot_table(
        index="selected_genes",
        columns="review_stars",
        values="variation_id",
        aggfunc="count",
        fill_value=0,
    )
    pivot = pivot.reindex(columns=[0, 1, 2, 3, 4], fill_value=0)
    ax = pivot.plot(kind="bar", stacked=True, figsize=(10, 5.5), colormap="viridis")
    ax.set_title(f"Review-status evidence levels — {later_label}")
    ax.set_xlabel("Gene")
    ax.set_ylabel("ClinVar variants")
    ax.legend(title="Review stars")
    plt.tight_layout()
    plt.savefig(output, dpi=180, bbox_inches="tight")
    plt.close()


def _save_evidence_context_plot(comparison: pd.DataFrame, output: Path) -> None:
    changed = comparison[comparison["change_type"] == "Classification changed"]
    order = ["Strengthened", "Same star level", "Weakened"]
    counts = changed["review_evidence_direction"].value_counts().reindex(order, fill_value=0)
    colors = ["#2b8a3e", "#6c757d", "#c92a2a"]
    ax = counts.plot(kind="bar", figsize=(8.5, 4.8), color=colors)
    ax.set_title("Classification changes by review-evidence direction")
    ax.set_xlabel("Review-star movement")
    ax.set_ylabel("Number of variants")
    ax.tick_params(axis="x", rotation=0)
    for container in ax.containers:
        ax.bar_label(container, padding=3, fontsize=9)
    plt.tight_layout()
    plt.savefig(output, dpi=180, bbox_inches="tight")
    plt.close()


def write_markdown_report(
    earlier: pd.DataFrame,
    later: pd.DataFrame,
    comparison: pd.DataFrame,
    earlier_label: str,
    later_label: str,
    output: Path,
) -> None:
    change_counts = comparison["change_type"].value_counts()
    class_changes = int(change_counts.get("Classification changed", 0))
    review_changes = int(change_counts.get("Review status changed", 0))
    added = int(change_counts.get("Added in later release", 0))
    removed = int(change_counts.get("Removed from later release", 0))
    genes = sorted({g for value in later["selected_genes"].dropna() for g in value.split("|")})

    text = f"""# ClinVar Hereditary-Cancer Reclassification Report

## Comparison

- Earlier release: **{earlier_label}** ({len(earlier):,} selected variants)
- Later release: **{later_label}** ({len(later):,} selected variants)
- Genes: **{', '.join(genes)}**
- Classification changes: **{class_changes:,}**
- Review-status-only changes: **{review_changes:,}**
- Added in the later release: **{added:,}**
- Removed from the later release: **{removed:,}**

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
"""
    output.write_text(text, encoding="utf-8")


def generate_outputs(
    earlier: pd.DataFrame,
    later: pd.DataFrame,
    earlier_label: str,
    later_label: str,
    output_dir: str | Path,
) -> dict[str, int]:
    """Write all tabular, visual, and narrative outputs for a comparison."""
    destination = Path(output_dir)
    figures = destination / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    comparison = compare_releases(earlier, later)
    notable = comparison[comparison["change_type"] != "Unchanged"].copy()
    counts = classification_counts(earlier, later, earlier_label, later_label)
    gene_summary = gene_change_summary(comparison)
    evidence_matrix = change_evidence_matrix(comparison)

    earlier.to_csv(destination / "variants_earlier.csv", index=False)
    later.to_csv(destination / "variants_later.csv", index=False)
    comparison.to_csv(destination / "variant_comparison.csv", index=False)
    notable.to_csv(destination / "notable_changes.csv", index=False)
    counts.to_csv(destination / "classification_counts.csv", index=False)
    gene_summary.to_csv(destination / "gene_change_summary.csv", index=False)
    evidence_matrix.to_csv(destination / "change_evidence_matrix.csv", index=False)

    summary = {
        "earlier_label": earlier_label,
        "later_label": later_label,
        "earlier_selected_variants": int(len(earlier)),
        "later_selected_variants": int(len(later)),
        "classification_changes": int((comparison["change_type"] == "Classification changed").sum()),
        "review_status_changes": int((comparison["change_type"] == "Review status changed").sum()),
        "added_variants": int((comparison["change_type"] == "Added in later release").sum()),
        "removed_variants": int((comparison["change_type"] == "Removed from later release").sum()),
        "unchanged_variants": int((comparison["change_type"] == "Unchanged").sum()),
    }
    (destination / "quality_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    _save_classification_plot(counts, later_label, figures / "classification_by_gene.png")
    _save_change_plot(comparison, figures / "comparison_outcomes.png")
    _save_review_plot(later, later_label, figures / "review_stars_by_gene.png")
    _save_evidence_context_plot(
        comparison, figures / "classification_changes_by_evidence_direction.png"
    )
    write_markdown_report(
        earlier,
        later,
        comparison,
        earlier_label,
        later_label,
        destination / "REPORT.md",
    )
    return summary


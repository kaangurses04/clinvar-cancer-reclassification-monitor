"""Interactive Streamlit dashboard for generated ClinVar monitor outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="ClinVar Reclassification Monitor",
    page_icon="🧬",
    layout="wide",
)

st.title("ClinVar Hereditary-Cancer Reclassification Monitor")
st.caption(
    "Educational portfolio project comparing aggregate germline classifications across public ClinVar releases."
)
st.warning(
    "Not for diagnosis, treatment, genetic counseling, patient-specific interpretation, or other clinical use."
)

default_output = Path(__file__).resolve().parent / "reports" / "demo"
output_text = st.sidebar.text_input("Results directory", str(default_output))
output_dir = Path(output_text)


@st.cache_data
def load_results(
    directory: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int | str], bool]:
    root = Path(directory)
    counts = pd.read_csv(root / "classification_counts.csv")
    with (root / "quality_summary.json").open(encoding="utf-8") as handle:
        summary = json.load(handle)

    complete_comparison = root / "variant_comparison.csv"
    compact_mode = not complete_comparison.exists()
    comparison_path = root / "notable_changes.csv" if compact_mode else complete_comparison
    comparison = pd.read_csv(comparison_path, dtype={"variation_id": "string"})
    return comparison, counts, summary, compact_mode


try:
    comparison, classification_table, summary, compact_mode = load_results(str(output_dir))
except (FileNotFoundError, json.JSONDecodeError, pd.errors.EmptyDataError, KeyError) as error:
    st.error(
        "Results could not be loaded. Choose `reports/demo`, `reports/real_2026`, "
        "or a directory created by `clinvar-monitor analyze`. "
        f"Details: {error}"
    )
    st.stop()

if compact_mode:
    st.info(
        "Compact portfolio view: metrics and charts summarize the complete comparison, "
        "while the table contains changed, added, and removed records only."
    )

genes = sorted(classification_table["selected_genes"].dropna().astype(str).unique())
change_types = sorted(comparison["change_type"].dropna().unique())
evidence_contexts = sorted(comparison["evidence_context"].dropna().unique())

selected_genes = st.sidebar.multiselect("Genes", genes, default=genes)
selected_changes = st.sidebar.multiselect("Comparison outcomes", change_types, default=change_types)
selected_contexts = st.sidebar.multiselect(
    "Classification–evidence context", evidence_contexts, default=evidence_contexts
)
minimum_stars = st.sidebar.slider("Minimum later-release review stars", 0, 4, 0)

filtered = comparison[
    comparison["selected_genes"].fillna("").apply(
        lambda value: any(gene in str(value).split("|") for gene in selected_genes)
    )
    & comparison["change_type"].isin(selected_changes)
    & comparison["evidence_context"].isin(selected_contexts)
]
if "review_stars_later" in filtered.columns:
    filtered = filtered[
        filtered["review_stars_later"].fillna(0).astype(float) >= minimum_stars
    ]

metric_columns = st.columns(4)
metric_columns[0].metric("Later-release variants", f"{summary['later_selected_variants']:,}")
metric_columns[1].metric("Classification changes", f"{summary['classification_changes']:,}")
metric_columns[2].metric("Review-status changes", f"{summary['review_status_changes']:,}")
metric_columns[3].metric("Added records", f"{summary['added_variants']:,}")

st.subheader("Comparison outcomes")
outcome_counts = pd.Series(
    {
        "Classification changed": summary["classification_changes"],
        "Review status changed": summary["review_status_changes"],
        "Added in later release": summary["added_variants"],
        "Removed from later release": summary["removed_variants"],
        "Unchanged": summary["unchanged_variants"],
    },
    name="variant_count",
)
st.bar_chart(outcome_counts)

st.subheader("Classification–evidence audit")
st.caption(
    "This original project layer keeps classification movement separate from the "
    "direction of ClinVar review-star movement; it is not a clinical priority score."
)
context_chart = (
    comparison[comparison["change_type"] == "Classification changed"]
    ["review_evidence_direction"]
    .value_counts()
    .reindex(["Strengthened", "Same star level", "Weakened"], fill_value=0)
)
st.bar_chart(context_chart)

st.subheader("Later-release classifications")
later_label = classification_table["release"].dropna().astype(str).iloc[-1]
chart_data = classification_table[classification_table["release"].astype(str) == later_label]
chart_data = chart_data[chart_data["selected_genes"].isin(selected_genes)]
chart_pivot = chart_data.pivot_table(
    index="selected_genes",
    columns="classification_group",
    values="variant_count",
    aggfunc="sum",
    fill_value=0,
)
st.bar_chart(chart_pivot)

st.subheader("Variant-level results")
display_columns = [
    "variation_id",
    "selected_genes",
    "change_type",
    "classification_transition",
    "review_transition",
    "star_delta",
    "review_evidence_direction",
    "evidence_context",
    "clinvar_url",
]
st.dataframe(filtered[display_columns], width="stretch", hide_index=True)
st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="clinvar_filtered_results.csv",
    mime="text/csv",
)

with st.expander("How to interpret this dashboard"):
    st.markdown(
        """
        - A **classification change** means the aggregate `CLNSIG` category differs between releases.
        - A **review-status change** means the evidence-review label differs while the grouped classification is stable.
        - Stars summarize ClinVar review status; they are not probabilities of correctness.
        - The classification–evidence audit is a descriptive two-axis lens, not a clinical score.
        - Open the linked current ClinVar record before drawing any scientific conclusion.
        """
    )


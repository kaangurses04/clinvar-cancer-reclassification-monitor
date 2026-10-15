"""Command-line interface for the ClinVar monitor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import generate_outputs
from .download import download_release
from .vcf import extract_variants


DEFAULT_GENES = ["ATM", "BRCA1", "BRCA2", "CHEK2", "PALB2", "TP53"]


def _parse_genes(value: str) -> list[str]:
    genes = [gene.strip().upper() for gene in value.split(",") if gene.strip()]
    if not genes:
        raise argparse.ArgumentTypeError("Provide at least one comma-separated gene symbol.")
    return genes


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_analysis(args: argparse.Namespace) -> dict[str, int]:
    earlier = extract_variants(args.earlier, args.genes)
    later = extract_variants(args.later, args.genes)
    if earlier.empty or later.empty:
        raise SystemExit("No selected directly classified variants were found in one or both files.")
    return generate_outputs(
        earlier,
        later,
        args.earlier_label,
        args.later_label,
        args.output,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clinvar-monitor",
        description="Compare hereditary-cancer variant classifications across ClinVar releases.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Compare two local ClinVar VCF files.")
    analyze.add_argument("--earlier", required=True, type=Path, help="Earlier .vcf or .vcf.gz file")
    analyze.add_argument("--later", required=True, type=Path, help="Later .vcf or .vcf.gz file")
    analyze.add_argument("--earlier-label", required=True, help="Human-readable earlier release label")
    analyze.add_argument("--later-label", required=True, help="Human-readable later release label")
    analyze.add_argument("--genes", type=_parse_genes, default=DEFAULT_GENES, help="Comma-separated gene symbols")
    analyze.add_argument("--output", type=Path, default=Path("reports/local"), help="Output directory")
    analyze.set_defaults(handler="analyze")

    download = subparsers.add_parser("download", help="Download a known official GRCh38 release.")
    download.add_argument("--date", required=True, help="Release date in YYYY-MM-DD format")
    download.add_argument("--output", required=True, type=Path, help="Destination .vcf.gz path")
    download.set_defaults(handler="download")

    demo = subparsers.add_parser("demo", help="Run the included synthetic demonstration.")
    demo.add_argument("--output", type=Path, default=None, help="Optional output directory")
    demo.set_defaults(handler="demo")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.handler == "download":
        path = download_release(args.date, args.output)
        print(f"Downloaded {args.date} to {path}")
        return

    if args.handler == "demo":
        root = project_root()
        args.earlier = root / "data" / "demo" / "clinvar_demo_earlier.vcf"
        args.later = root / "data" / "demo" / "clinvar_demo_later.vcf"
        args.earlier_label = "Demo release A"
        args.later_label = "Demo release B"
        args.genes = DEFAULT_GENES
        args.output = args.output or (root / "reports" / "demo")

    summary = run_analysis(args)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()


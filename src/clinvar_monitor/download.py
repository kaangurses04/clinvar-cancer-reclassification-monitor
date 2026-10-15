"""Download official dated ClinVar GRCh38 VCF releases."""

from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import shutil
from urllib.request import Request, urlopen


ARCHIVE_TEMPLATE = (
    "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/"
    "archive_2.0/{year}/clinvar_{stamp}.vcf.gz"
)


def release_url(date_text: str) -> str:
    """Build the official archive URL for a known ClinVar release date."""
    date = datetime.strptime(date_text, "%Y-%m-%d")
    return ARCHIVE_TEMPLATE.format(year=date.year, stamp=date.strftime("%Y%m%d"))


def download_release(date_text: str, output: str | Path) -> Path:
    """Download a dated release and verify it against NCBI's MD5 sidecar."""
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    url = release_url(date_text)
    headers = {"User-Agent": "clinvar-monitor/1.0 educational-project"}
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=120) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target, length=1024 * 1024)
        checksum_request = Request(url + ".md5", headers=headers)
        with urlopen(checksum_request, timeout=30) as response:
            expected_md5 = response.read().decode("utf-8").strip().split()[0].lower()
        digest = hashlib.md5()
        with partial.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest().lower() != expected_md5:
            raise ValueError("Downloaded ClinVar release failed MD5 verification.")
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return destination


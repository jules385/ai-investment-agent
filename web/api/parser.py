from pathlib import Path


def parse_single_report(report_path: str | Path) -> dict:
    path = Path(report_path)
    return {
        "path": str(path),
        "stock": path.stem,
        "industries": {},
        "theses": {},
        "tracking": {},
    }


def parse_all_reports(reports_dir: str | Path | None = None) -> dict:
    return {
        "stocks_parsed": 0,
        "industries": {},
        "theses": {},
        "tracking": {},
    }

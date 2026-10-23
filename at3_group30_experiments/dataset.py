"""Create the validated daily cryptocurrency dataset used by Group 30."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError
import typer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "coinmarketcap"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "cryptocurrency_daily.csv"
DEFAULT_AUDIT_PATH = PROJECT_ROOT / "reports" / "data_quality.json"

TOKEN_BY_FOLDER = {
    "Bitcoin (BTC)": "BTC", "Ethereum (ETH)": "ETH", "Ripple (XRP)": "XRP",
    "Solana (SOL)": "SOL", "Dogecoin (DOGE)": "DOGE", "Monero (XMR)": "XMR",
    "Stellar (XLM)": "XLM", "Tron (TRX)": "TRX",
}
NUMERIC_COLUMNS = ["open", "high", "low", "close", "volume", "marketCap"]
REQUIRED_COLUMNS = {"timeOpen", *NUMERIC_COLUMNS}
OUTPUT_COLUMNS = ["token", "date", *NUMERIC_COLUMNS]


class DatasetValidationError(ValueError):
    """Raised when source data would make the canonical dataset unreliable."""


def _read_source_file(path: Path, token: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    except EmptyDataError:
        return None
    if frame.empty:
        return None

    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise DatasetValidationError(f"{path.name}: missing columns: {', '.join(sorted(missing))}")

    result = frame.loc[:, ["timeOpen", *NUMERIC_COLUMNS]].copy()
    result["date"] = pd.to_datetime(result.pop("timeOpen"), utc=True, errors="coerce").dt.normalize()
    for column in NUMERIC_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result.insert(0, "token", token)

    invalid = result[["date", *NUMERIC_COLUMNS]].isna().any(axis=1)
    if invalid.any():
        raise DatasetValidationError(f"{path.name}: {int(invalid.sum())} invalid rows")
    if (result[["open", "high", "low", "close"]] <= 0).any(axis=1).any():
        raise DatasetValidationError(f"{path.name}: prices must be positive")
    if (result[["volume", "marketCap"]] < 0).any(axis=1).any():
        raise DatasetValidationError(f"{path.name}: volume and market cap cannot be negative")

    bad_high = result["high"] < result[["open", "close", "low"]].max(axis=1)
    bad_low = result["low"] > result[["open", "close", "high"]].min(axis=1)
    if (bad_high | bad_low).any():
        raise DatasetValidationError(f"{path.name}: rows violate OHLC bounds")
    return result.loc[:, OUTPUT_COLUMNS]


def _validate_duplicate_consistency(frame: pd.DataFrame) -> None:
    duplicates = frame[frame.duplicated(["token", "date"], keep=False)]
    if duplicates.empty:
        return
    conflicts = duplicates.groupby(["token", "date"])[NUMERIC_COLUMNS].nunique(dropna=False)
    keys = conflicts.index[(conflicts > 1).any(axis=1)]
    if len(keys):
        examples = ", ".join(f"{token}/{date.date()}" for token, date in keys[:5])
        raise DatasetValidationError(f"Conflicting duplicate observations found: {examples}")


def _gap_ranges(dates: pd.Series) -> list[dict[str, Any]]:
    observed = pd.DatetimeIndex(dates.sort_values().unique())
    missing = pd.date_range(observed.min(), observed.max(), freq="D", tz="UTC").difference(observed)
    if missing.empty:
        return []
    ranges: list[dict[str, Any]] = []
    start = previous = missing[0]
    for current in missing[1:]:
        if (current.date() - previous.date()).days > 1:
            ranges.append({"start": str(start.date()), "end": str(previous.date()),
                           "days": int((previous - start).days + 1)})
            start = current
        previous = current
    ranges.append({"start": str(start.date()), "end": str(previous.date()),
                   "days": int((previous - start).days + 1)})
    return ranges


def clean_historical_data(input_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate, combine, and deduplicate all supported token exports."""
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Raw data directory does not exist: {input_dir}")
    unknown = sorted(p.name for p in input_dir.iterdir() if p.is_dir() and p.name not in TOKEN_BY_FOLDER)
    if unknown:
        raise DatasetValidationError(f"Unsupported token folders: {', '.join(unknown)}")

    files = sorted(input_dir.glob("*/*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found under: {input_dir}")
    frames: list[pd.DataFrame] = []
    empty_files: list[str] = []
    for path in files:
        frame = _read_source_file(path, TOKEN_BY_FOLDER[path.parent.name])
        if frame is None:
            empty_files.append(str(path.relative_to(input_dir)))
        else:
            frames.append(frame)
    if not frames:
        raise DatasetValidationError("All source files were empty")

    combined = pd.concat(frames, ignore_index=True)
    _validate_duplicate_consistency(combined)
    before = combined.groupby("token").size()
    cleaned = (combined.drop_duplicates(["token", "date"])
               .sort_values(["token", "date"], kind="stable").reset_index(drop=True))
    after = cleaned.groupby("token").size()
    missing_tokens = sorted(set(TOKEN_BY_FOLDER.values()) - set(cleaned["token"].unique()))
    if missing_tokens:
        raise DatasetValidationError(f"No usable data for tokens: {', '.join(missing_tokens)}")

    token_audit: dict[str, Any] = {}
    for token, token_frame in cleaned.groupby("token", sort=True):
        gaps = _gap_ranges(token_frame["date"])
        token_audit[token] = {
            "rows": int(len(token_frame)),
            "start_date": str(token_frame["date"].min().date()),
            "end_date": str(token_frame["date"].max().date()),
            "duplicate_rows_removed": int(before[token] - after[token]),
            "missing_calendar_days": int(sum(gap["days"] for gap in gaps)),
            "missing_date_ranges": gaps,
        }
    audit = {
        "source": "CoinMarketCap historical CSV exports supplied for AT3 experimentation",
        "source_files_found": len(files),
        "usable_source_files": len(files) - len(empty_files),
        "empty_files_skipped": empty_files,
        "rows_before_deduplication": int(len(combined)),
        "rows_after_deduplication": int(len(cleaned)),
        "duplicate_rows_removed": int(len(combined) - len(cleaned)),
        "missing_value_count": int(cleaned.isna().sum().sum()),
        "calendar_dates_filled": False,
        "tokens": token_audit,
    }
    return cleaned, audit


def write_clean_outputs(cleaned: pd.DataFrame, audit: dict[str, Any],
                        output_path: Path, audit_path: Path) -> None:
    output_path, audit_path = Path(output_path), Path(audit_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    export = cleaned.copy()
    export["date"] = export["date"].dt.strftime("%Y-%m-%d")
    export.to_csv(output_path, index=False)
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")


def main(input_dir: Path = DEFAULT_INPUT_DIR, output_path: Path = DEFAULT_OUTPUT_PATH,
         audit_path: Path = DEFAULT_AUDIT_PATH) -> None:
    cleaned, audit = clean_historical_data(input_dir)
    write_clean_outputs(cleaned, audit, output_path, audit_path)
    typer.echo(f"Wrote {len(cleaned):,} rows to {output_path}")
    typer.echo(f"Wrote data-quality evidence to {audit_path}")


if __name__ == "__main__":
    typer.run(main)

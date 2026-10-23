from pathlib import Path

import pandas as pd
import pytest

from at3_group30_experiments.dataset import DatasetValidationError, clean_historical_data

HEADER = "timeOpen;open;high;low;close;volume;marketCap\n"
FOLDERS = {
    "Bitcoin (BTC)": "2015-01-01", "Ethereum (ETH)": "2015-08-08",
    "Ripple (XRP)": "2015-01-01", "Solana (SOL)": "2020-04-11",
    "Dogecoin (DOGE)": "2014-11-27", "Monero (XMR)": "2014-11-27",
    "Stellar (XLM)": "2014-11-27", "Tron (TRX)": "2017-09-14",
}


def _write(root: Path, folder: str, filename: str, rows: list[str]) -> None:
    directory = root / folder
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(HEADER + "\n".join(rows) + "\n", encoding="utf-8")


def _base(root: Path) -> None:
    for folder, date in FOLDERS.items():
        _write(root, folder, "base.csv", [f"{date}T00:00:00Z;10;12;9;11;100;1000"])


def test_sorts_and_removes_identical_overlap(tmp_path: Path) -> None:
    _base(tmp_path)
    _write(tmp_path, "Bitcoin (BTC)", "overlap.csv", [
        "2015-01-03T00:00:00Z;12;14;11;13;120;1200",
        "2015-01-02T00:00:00Z;11;13;10;12;110;1100",
        "2015-01-01T00:00:00Z;10;12;9;11;100;1000",
    ])
    cleaned, audit = clean_historical_data(tmp_path)
    btc = cleaned[cleaned["token"] == "BTC"]
    assert btc["date"].is_monotonic_increasing
    assert len(btc) == 3
    assert audit["tokens"]["BTC"]["duplicate_rows_removed"] == 1


def test_skips_bom_only_file_and_accepts_optional_column(tmp_path: Path) -> None:
    _base(tmp_path)
    (tmp_path / "Solana (SOL)" / "prelaunch.csv").write_bytes(b"\xef\xbb\xbf")
    optional = tmp_path / "Bitcoin (BTC)" / "optional.csv"
    optional.write_text("timeOpen;open;high;low;close;volume;marketCap;circulatingSupply\n"
                        "2015-01-02T00:00:00Z;11;13;10;12;110;1100;100\n", encoding="utf-8")
    cleaned, audit = clean_historical_data(tmp_path)
    assert len(cleaned[cleaned["token"] == "BTC"]) == 2
    assert audit["empty_files_skipped"] == ["Solana (SOL)/prelaunch.csv"]


def test_rejects_conflicting_duplicate(tmp_path: Path) -> None:
    _base(tmp_path)
    _write(tmp_path, "Bitcoin (BTC)", "conflict.csv",
           ["2015-01-01T00:00:00Z;10;100;9;99;100;1000"])
    with pytest.raises(DatasetValidationError, match="Conflicting duplicate"):
        clean_historical_data(tmp_path)


def test_reports_gap_without_filling(tmp_path: Path) -> None:
    _base(tmp_path)
    _write(tmp_path, "Bitcoin (BTC)", "gap.csv",
           ["2015-01-03T00:00:00Z;12;14;11;13;120;1200"])
    cleaned, audit = clean_historical_data(tmp_path)
    dates = cleaned.loc[cleaned["token"] == "BTC", "date"].tolist()
    assert pd.Timestamp("2015-01-02", tz="UTC") not in dates
    assert audit["tokens"]["BTC"]["missing_calendar_days"] == 1
    assert audit["calendar_dates_filled"] is False


def test_rejects_invalid_ohlc(tmp_path: Path) -> None:
    _base(tmp_path)
    (tmp_path / "Bitcoin (BTC)" / "base.csv").write_text(
        HEADER + "2015-01-01T00:00:00Z;10;10;9;11;100;1000\n", encoding="utf-8")
    with pytest.raises(DatasetValidationError, match="OHLC bounds"):
        clean_historical_data(tmp_path)

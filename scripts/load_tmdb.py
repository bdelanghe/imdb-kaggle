#!/usr/bin/env python3
"""Helper for loading the TMDb dataset via kagglehub."""

from __future__ import annotations

import argparse
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from dotenv import load_dotenv

import kagglehub

load_dotenv()

DEFAULT_DATASET = "asaniczka/tmdb-movies-dataset-2023-930k-movies"
DEFAULT_NROWS = 5


def parse_pandas_kwargs(raw: str | None) -> Dict[str, Any]:
    """Decode a JSON object of kwargs for pandas.read_*."""
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--pandas-kwargs is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise SystemExit("--pandas-kwargs must decode to a JSON object/dict")

    return parsed


def has_kaggle_credentials() -> bool:
    """Make sure the Kaggle API token or config file is on the machine."""
    env = os.environ
    if env.get("KAGGLE_API_TOKEN"):
        return True

    if env.get("KAGGLE_USERNAME") and env.get("KAGGLE_KEY"):
        return True

    kaggle_dir = Path.home() / ".kaggle"
    return any((kaggle_dir / name).exists() for name in ("access_token", "access_token.txt", "kaggle.json"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the TMDb movie dataset from Kaggle and preview it with pandas."
    )
    parser.add_argument(
        "--dataset",
        "-d",
        default=DEFAULT_DATASET,
        help="Kaggle dataset slug (e.g. asaniczka/full-tmdb-movies)",
    )
    parser.add_argument(
        "--nrows",
        "-n",
        type=int,
        default=DEFAULT_NROWS,
        help="Pass through pandas' `nrows` so we preview only the first few rows.",
    )
    parser.add_argument(
        "--pandas-kwargs",
        help="JSON string of kwargs to forward to the underlying pandas reader.",
    )
    args = parser.parse_args()

    pandas_kwargs = parse_pandas_kwargs(args.pandas_kwargs)

    if args.nrows and "nrows" not in pandas_kwargs:
        pandas_kwargs["nrows"] = args.nrows

    if not has_kaggle_credentials():
        parser.error(
            "Kaggle credentials not found. Set KAGGLE_API_TOKEN or place your kaggle.json/access_token in ~/.kaggle."
        )

    print(f"Downloading {args.dataset} (full dataset) with pandas kwargs {pandas_kwargs or {}}.")

    base_path = kagglehub.dataset_download(args.dataset)
    base = Path(base_path)
    pandas_kwargs = pandas_kwargs or {}

    if base.is_file() and base.suffix.lower() == ".zip":
        with zipfile.ZipFile(base, "r") as z:
            csv_names = sorted(n for n in z.namelist() if n.lower().endswith(".csv"))
            if not csv_names:
                raise SystemExit(f"No .csv in {base}")
            with z.open(csv_names[0]) as f:
                df = pd.read_csv(f, **pandas_kwargs)
    else:
        zips = list(base.rglob("*.zip"))
        if zips:
            with zipfile.ZipFile(sorted(zips)[0], "r") as z:
                csv_names = sorted(n for n in z.namelist() if n.lower().endswith(".csv"))
                if not csv_names:
                    raise SystemExit(f"No .csv in {zips[0]}")
                with z.open(csv_names[0]) as f:
                    df = pd.read_csv(f, **pandas_kwargs)
        else:
            csvs = list(base.rglob("*.csv"))
            if not csvs:
                raise SystemExit(f"No .zip or .csv under {base_path}")
            df = pd.read_csv(sorted(csvs)[0], **pandas_kwargs)

    print(f"Loaded {len(df)} rows × {len(df.columns)} columns.")
    print(df.head())


if __name__ == "__main__":
    main()

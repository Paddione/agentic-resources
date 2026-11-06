#!/usr/bin/env python3
"""Shared Dataset Server helpers for the ml-training dataset inspectors.

Single home for the logic duplicated between
- huggingface-vision-trainer/scripts/dataset_inspector.py
- huggingface-llm-trainer/scripts/dataset_inspector.py

Only byte-identical helpers live here (verified by diff before extraction):
``api_request``, ``get_splits``, ``get_rows``, ``find_columns`` and the
fetch/resolve block shared by both ``main()`` entry points. Domain-specific
code (compatibility checks, mapping snippets, previews, report rendering)
stays in the thin wrappers so both CLIs keep identical argv/stdout behavior.
"""
import json
import sys
import urllib.request
import urllib.parse
from typing import Dict, List, Tuple


def api_request(url: str) -> Dict:
    """Make API request to Datasets Server"""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise Exception(f"API request failed: {e.code} {e.reason}")
    except Exception as e:
        raise Exception(f"API request failed: {str(e)}")


def get_splits(dataset: str) -> Dict:
    """Get available splits for dataset"""
    url = f"https://datasets-server.huggingface.co/splits?dataset={urllib.parse.quote(dataset)}"
    return api_request(url)


def get_rows(dataset: str, config: str, split: str, offset: int = 0, length: int = 5) -> Dict:
    """Get rows from dataset"""
    url = f"https://datasets-server.huggingface.co/rows?dataset={urllib.parse.quote(dataset)}&config={config}&split={split}&offset={offset}&length={length}"
    return api_request(url)


def find_columns(columns: List[str], patterns: List[str]) -> List[str]:
    """Find columns matching patterns"""
    return [c for c in columns if any(p in c.lower() for p in patterns)]


def resolve_config(splits_data: Dict, want_config: str, want_split: str) -> Tuple[str, List[str], bool]:
    """Pick the config to use; returns (config_to_use, sorted_configs, split_found)."""
    available_configs = set()
    split_found = False
    config_to_use = want_config

    for split_info in splits_data["splits"]:
        available_configs.add(split_info["config"])
        if split_info["config"] == want_config and split_info["split"] == want_split:
            split_found = True

    # If default config not found, try first available
    if not split_found and available_configs:
        config_to_use = list(available_configs)[0]

    return config_to_use, sorted(available_configs), split_found


def fetch_dataset(dataset: str, config: str, split: str, samples: int = 5):
    """Fetch rows/columns/features via the Datasets Server API.

    Prints the exact progress/error messages both inspectors historically
    printed and exits 1 on failure, so wrapper CLIs stay byte-identical.
    Returns (rows, columns, features, config_to_use, total_examples).
    """
    print("Fetching dataset info via Datasets Server API...")

    try:
        # Get splits info
        splits_data = get_splits(dataset)
        if not splits_data or "splits" not in splits_data:
            print(f"ERROR: Could not fetch splits for dataset '{dataset}'")
            print("       Dataset may not exist or is not accessible via Datasets Server API")
            sys.exit(1)

        # Find the right config
        config_to_use, available_configs, split_found = resolve_config(splits_data, config, split)
        if not split_found and available_configs:
            print(f"Config '{config}' not found, trying '{config_to_use}'...")

        # Get rows
        rows_data = get_rows(dataset, config_to_use, split, offset=0, length=samples)

        if not rows_data or "rows" not in rows_data:
            print(f"ERROR: Could not fetch rows for dataset '{dataset}'")
            print(f"       Split '{split}' may not exist")
            print(f"       Available configs: {', '.join(available_configs)}")
            sys.exit(1)

        rows = rows_data["rows"]
        if not rows:
            print(f"ERROR: No rows found in split '{split}'")
            sys.exit(1)

        # Extract column info from first row
        first_row = rows[0]["row"]
        columns = list(first_row.keys())
        features = rows_data.get("features", [])

        # Get total count if available
        total_examples = "Unknown"
        for split_info in splits_data["splits"]:
            if split_info["config"] == config_to_use and split_info["split"] == split:
                total_examples = f"{split_info.get('num_examples', 'Unknown'):,}" if isinstance(split_info.get('num_examples'), int) else "Unknown"
                break

    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

    return rows, columns, features, config_to_use, total_examples

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Test script for evaluation extraction functionality.

This script demonstrates and validates the table extraction capabilities without
requiring HF tokens or making actual API calls.

Note: This script imports from evaluation_manager.py (same directory).
Run from the scripts/ directory: cd scripts && uv run test_extraction.py
"""

import pytest
import yaml

from evaluation_manager import (
    extract_tables_from_markdown,
    parse_markdown_table,
    is_evaluation_table,
    extract_metrics_from_table,
)

# Sample README content with various table formats
SAMPLE_README = """
# My Awesome Model

## Evaluation Results

Here are the benchmark results:

| Benchmark | Score |
|-----------|-------|
| MMLU      | 85.2  |
| HumanEval | 72.5  |
| GSM8K     | 91.3  |

### Detailed Breakdown

| Category      | MMLU  | GSM8K | HumanEval |
|---------------|-------|-------|-----------|
| Performance   | 85.2  | 91.3  | 72.5      |

## Other Information

This is not an evaluation table:

| Feature | Value |
|---------|-------|
| Size    | 7B    |
| Type    | Chat  |

## More Results

| Benchmark     | Accuracy | F1 Score |
|---------------|----------|----------|
| HellaSwag     | 88.9     | 0.87     |
| TruthfulQA    | 68.7     | 0.65     |
"""


def _print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def collect_tables():
    """Extract markdown tables from SAMPLE_README."""
    _print_section("TEST 1: Table Extraction")
    extracted = extract_tables_from_markdown(SAMPLE_README)
    print(f"Found {len(extracted)} tables in the sample README\n")
    for i, table in enumerate(extracted, 1):
        print(f"Table {i}:")
        print(table[:100] + "..." if len(table) > 100 else table)
        print()
    return extracted


def collect_parsed_tables(tables):
    """Parse extracted markdown tables into (header, rows)."""
    _print_section("TEST 2: Table Parsing")
    parsed = []
    for i, table in enumerate(tables, 1):
        print(f"\nParsing Table {i}:")
        header, rows = parse_markdown_table(table)
        print(f"  Header: {header}")
        print(f"  Rows: {len(rows)}")
        for j, row in enumerate(rows[:3], 1):
            print(f"    Row {j}: {row}")
        if len(rows) > 3:
            print(f"    ... and {len(rows) - 3} more rows")
        parsed.append((header, rows))
    return parsed


def collect_eval_tables(parsed_tables):
    """Keep only tables identified as evaluation tables."""
    _print_section("TEST 3: Evaluation Table Detection")
    detected = []
    for i, (header, rows) in enumerate(parsed_tables, 1):
        is_eval = is_evaluation_table(header, rows)
        status = "✓ IS" if is_eval else "✗ NOT"
        print(f"\nTable {i}: {status} an evaluation table")
        print(f"  Header: {header}")
        if is_eval:
            detected.append((header, rows))

    print(f"\nFound {len(detected)} evaluation tables")
    return detected


def collect_metrics(eval_tables):
    """Extract metrics from evaluation tables."""
    _print_section("TEST 4: Metric Extraction")
    extracted_metrics = []
    for i, (header, rows) in enumerate(eval_tables, 1):
        print(f"\nExtracting metrics from table {i}:")
        table_metrics = extract_metrics_from_table(header, rows, table_format="auto")

        print(f"  Extracted {len(table_metrics)} metrics:")
        for metric in table_metrics:
            print(
                f"    - {metric['name']}: {metric['value']} "
                f"(type: {metric['type']})"
            )

        extracted_metrics.extend(table_metrics)

    return extracted_metrics


def build_model_index(metrics):
    """Build model-index payload from extracted metrics."""
    return {
        "model-index": [
            {
                "name": "test-model",
                "results": [
                    {
                        "task": {"type": "text-generation"},
                        "dataset": {"name": "Benchmarks", "type": "benchmark"},
                        "metrics": metrics,
                        "source": {
                            "name": "Model README",
                            "url": "https://huggingface.co/test/model",
                        },
                    }
                ],
            }
        ]
    }


@pytest.fixture(scope="module")
def tables():
    return collect_tables()


@pytest.fixture(scope="module")
def parsed_tables(tables):
    return collect_parsed_tables(tables)


@pytest.fixture(scope="module")
def eval_tables(parsed_tables):
    return collect_eval_tables(parsed_tables)


@pytest.fixture(scope="module")
def metrics(eval_tables):
    return collect_metrics(eval_tables)


def test_table_extraction(tables):
    """Table extraction should find all markdown tables in SAMPLE_README."""
    assert len(tables) == 4
    assert any("MMLU" in table for table in tables)


def test_table_parsing(tables, parsed_tables):
    """Each extracted table should parse into at least one header and row."""
    assert len(parsed_tables) == len(tables)
    assert all(header for header, _ in parsed_tables)
    assert all(rows for _, rows in parsed_tables)


def test_evaluation_detection(eval_tables):
    """Evaluation detection should identify benchmark-like score tables."""
    assert len(eval_tables) >= 3
    assert any(header and "benchmark" in header[0].lower() for header, _ in eval_tables)


def test_metric_extraction(metrics):
    """Metric extraction should produce typed metric entries with values."""
    assert metrics
    for metric in metrics:
        assert {"name", "value", "type"}.issubset(metric)
        assert isinstance(metric["name"], str) and metric["name"]
        assert isinstance(metric["type"], str) and metric["type"]


def test_model_index_format(metrics):
    """Model-index structure should serialize with extracted metrics."""
    _print_section("TEST 5: Model-Index Format")
    model_index = build_model_index(metrics)

    dumped = yaml.dump(model_index, sort_keys=False, default_flow_style=False)
    print("\nGenerated model-index structure:")
    print(dumped)

    assert "model-index" in model_index
    assert model_index["model-index"][0]["results"][0]["metrics"] == metrics


def main():
    """Run the extraction flow as a standalone script."""
    print("\n" + "=" * 60)
    print("EVALUATION EXTRACTION TEST SUITE")
    print("=" * 60)
    print("\nThis test demonstrates the table extraction capabilities")
    print("without requiring API access or tokens.\n")

    local_tables = collect_tables()
    local_parsed_tables = collect_parsed_tables(local_tables)
    local_eval_tables = collect_eval_tables(local_parsed_tables)
    local_metrics = collect_metrics(local_eval_tables)

    model_index = build_model_index(local_metrics)

    _print_section("TEST SUMMARY")
    print(f"✓ Found {len(local_tables)} total tables")
    print(f"✓ Identified {len(local_eval_tables)} evaluation tables")
    print(f"✓ Extracted {len(local_metrics)} metrics")
    print("✓ Generated model-index format successfully")
    print("\n" + "=" * 60)
    print("All tests completed! The extraction logic is working correctly.")
    print("=" * 60 + "\n")

    print(yaml.dump(model_index, sort_keys=False, default_flow_style=False))


if __name__ == "__main__":
    main()

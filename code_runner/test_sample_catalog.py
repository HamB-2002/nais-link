from pathlib import Path

from code_runner.sample_catalog import catalog_payload


def test_catalog_lists_the_two_public_reproduction_bundles() -> None:
    catalog = catalog_payload(Path(__file__).parents[1])

    assert [sample["identifier"] for sample in catalog] == ["sample-07", "sample-09"]
    assert all(sample["report_bytes"] > 0 for sample in catalog)
    assert all(sample["code_file_count"] > 0 for sample in catalog)
    assert all(sample["data_file_count"] > 0 for sample in catalog)

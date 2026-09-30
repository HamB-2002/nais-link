from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict


@dataclass(frozen=True, slots=True)
class SampleBundle:
    identifier: str
    title: str
    report_path: str
    code_entry: str
    data_root: str


class SamplePayload(TypedDict):
    identifier: str
    title: str
    report_path: str
    report_bytes: int
    code_entry: str
    code_file_count: int
    data_root: str
    data_file_count: int


_SAMPLES = (
    SampleBundle(
        "sample-07",
        "Safe Spaces: harassment and stigma",
        "data/samples/sample-07/report.pdf",
        "code/dofiles/analysis/paper/MASTER_paper_results.do",
        "data",
    ),
    SampleBundle(
        "sample-09",
        "Learning Poverty working paper",
        "data/samples/sample-09/report.pdf",
        "code/052_programs/052_run.do",
        "data",
    ),
)


def catalog_payload(repository_root: Path) -> tuple[SamplePayload, ...]:
    return tuple(_to_payload(repository_root, sample) for sample in _SAMPLES)


def _to_payload(repository_root: Path, sample: SampleBundle) -> SamplePayload:
    sample_root = repository_root / "data" / "samples" / sample.identifier
    report = repository_root / sample.report_path
    code_root = sample_root / "code"
    data_root = sample_root / sample.data_root
    return SamplePayload(
        identifier=sample.identifier,
        title=sample.title,
        report_path=sample.report_path,
        report_bytes=report.stat().st_size,
        code_entry=sample.code_entry,
        code_file_count=_file_count(code_root),
        data_root=sample.data_root,
        data_file_count=_file_count(data_root),
    )


def _file_count(directory: Path) -> int:
    return sum(path.is_file() for path in directory.rglob("*"))

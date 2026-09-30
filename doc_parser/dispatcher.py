from dataclasses import dataclass
from pathlib import Path

from doc_parser.adapter import to_collector_blocks
from doc_parser.docx_parser import parse_docx
from doc_parser.errors import ErrorCode
from doc_parser.hwpx_parser import parse_hwpx
from doc_parser.models import SourceFormat
from doc_parser.normalize import RawBlock, normalize_document
from doc_parser.pdf_parser import parse_pdf


@dataclass(slots=True)
class UnsupportedDocumentError(Exception):
    path: Path
    code: ErrorCode = ErrorCode.UNSUPPORTED_FORMAT

    def __str__(self) -> str:
        return f"unsupported document format for {self.path}: {self.code.value}"


def parse_document(path: Path) -> list[dict]:
    match path.suffix.lower():
        case ".docx":
            return _collector_blocks(SourceFormat.DOCX, parse_docx(path))
        case ".hwpx":
            return _collector_blocks(SourceFormat.HWPX, parse_hwpx(path))
        case ".pdf":
            return _collector_blocks(SourceFormat.PDF, parse_pdf(path))
        case _:
            raise UnsupportedDocumentError(path)


def _collector_blocks(source_format: SourceFormat, candidates: tuple[RawBlock, ...]) -> list[dict]:
    return to_collector_blocks(normalize_document(source_format, candidates))

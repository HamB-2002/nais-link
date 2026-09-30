from enum import StrEnum


class ErrorCode(StrEnum):
    UNSUPPORTED_FORMAT = "unsupported_format"
    ENCRYPTED_DOCUMENT = "encrypted_document"
    INVALID_CONTAINER = "invalid_container"
    ARCHIVE_LIMITS_EXCEEDED = "archive_limits_exceeded"
    MALFORMED_XML = "malformed_xml"
    MISSING_REQUIRED_PART = "missing_required_part"
    INVALID_DOCUMENT_STRUCTURE = "invalid_document_structure"
    TEXT_EXTRACTION_FAILED = "text_extraction_failed"
    PDF_TEXT_UNAVAILABLE = "pdf_text_unavailable"
    TABLE_ROWS_UNAVAILABLE = "table_rows_unavailable"
    TABLE_IRREGULAR_ROWS = "table_irregular_rows"
    UNSUPPORTED_ELEMENT = "unsupported_element"
    INVALID_PAGE_REFERENCE = "invalid_page_reference"
    NORMALIZATION_FAILED = "normalization_failed"
    CONTRACT_VALIDATION_FAILED = "contract_validation_failed"

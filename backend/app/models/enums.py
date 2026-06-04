"""PostgreSQL-backed enum types per docs/MCQ_Platform_ERD.md."""

from enum import StrEnum


class UserRole(StrEnum):
    EXAMINER = "EXAMINER"
    EXAMINEE = "EXAMINEE"


class CorrectOption(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class SessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class SelectionMode(StrEnum):
    FIXED_ORDER = "FIXED_ORDER"
    RANDOM_SAMPLE = "RANDOM_SAMPLE"


class SelectedOption(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class ErasureJobStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AuditOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"

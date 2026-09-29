"""CASHNET Unified Data Validation Suite."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .leakage_validation import validate_anti_leakage
from .relational_validation import validate_relational_integrity
from .schema_validation import validate_table_structure
from .temporal_validation import validate_temporal_consistency


@dataclass
class ValidationReport:
    """Consolidated validation execution report."""
    is_valid: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    table_counts: Dict[str, int] = field(default_factory=dict)
    schema_errors: List[str] = field(default_factory=list)
    relational_errors: List[str] = field(default_factory=list)
    temporal_errors: List[str] = field(default_factory=list)
    leakage_errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Returns human-readable text summary of the validation report."""
        lines = [
            "=" * 70,
            "CASHNET SYNTHETIC DATA VALIDATION REPORT",
            "=" * 70,
            f"Overall Status   : {'PASSED [OK]' if self.is_valid else 'FAILED [ERROR]'}",
            f"Total Checks     : {self.total_checks}",
            f"Passed Checks    : {self.passed_checks}",
            f"Failed Checks    : {self.failed_checks}",
            "-" * 70,
            "Dataset Record Counts:",
        ]
        for tbl, count in sorted(self.table_counts.items()):
            lines.append(f"  - {tbl:<25}: {count:>8,d} records")

        if not self.is_valid:
            lines.append("-" * 70)
            lines.append("Validation Failure Details:")
            for err in self.schema_errors + self.relational_errors + self.temporal_errors + self.leakage_errors:
                lines.append(f"  [X] {err}")
        lines.append("=" * 70)
        return "\n".join(lines)


def run_all_validations(datasets: Dict[str, List[Dict[str, Any]]]) -> ValidationReport:
    """Executes structural, relational, temporal, and anti-leakage validations.

    Args:
        datasets: Map of table name to record list.

    Returns:
        ValidationReport instance.
    """
    total_checks = 0
    passed_checks = 0
    failed_checks = 0

    table_counts = {tbl: len(recs) for tbl, recs in datasets.items()}

    # 1. Structural checks
    schema_errors: List[str] = []
    for tbl, recs in datasets.items():
        total_checks += 1
        valid, errs = validate_table_structure(tbl, recs)
        if valid:
            passed_checks += 1
        else:
            failed_checks += 1
            schema_errors.extend(errs)

    # 2. Relational checks
    total_checks += 1
    rel_valid, rel_errs = validate_relational_integrity(datasets)
    if rel_valid:
        passed_checks += 1
    else:
        failed_checks += 1

    # 3. Temporal checks
    total_checks += 1
    temp_valid, temp_errs = validate_temporal_consistency(datasets)
    if temp_valid:
        passed_checks += 1
    else:
        failed_checks += 1

    # 4. Anti-leakage checks
    total_checks += 1
    leak_valid, leak_errs = validate_anti_leakage(datasets)
    if leak_valid:
        passed_checks += 1
    else:
        failed_checks += 1

    all_valid = (failed_checks == 0)

    return ValidationReport(
        is_valid=all_valid,
        total_checks=total_checks,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        table_counts=table_counts,
        schema_errors=schema_errors,
        relational_errors=rel_errs,
        temporal_errors=temp_errs,
        leakage_errors=leak_errs,
    )

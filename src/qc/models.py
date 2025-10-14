"""
Quality Control Data Models

Defines the core data structures for the QC framework.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Issue severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class QCIssue:
    """Represents a quality control issue"""
    severity: Severity
    category: str
    message: str
    file_name: str
    line_number: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QCReport:
    """Quality control report containing all issues"""
    issues: List[QCIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    
    def add_issue(self, issue: QCIssue):
        """Add an issue to the report"""
        self.issues.append(issue)
        if issue.severity.value not in self.summary:
            self.summary[issue.severity.value] = 0
        self.summary[issue.severity.value] += 1
    
    def get_errors(self) -> List[QCIssue]:
        """Get all error-level issues"""
        return [issue for issue in self.issues if issue.severity == Severity.ERROR]
    
    def get_warnings(self) -> List[QCIssue]:
        """Get all warning-level issues"""
        return [issue for issue in self.issues if issue.severity == Severity.WARNING]
    
    def get_info(self) -> List[QCIssue]:
        """Get all info-level issues"""
        return [issue for issue in self.issues if issue.severity == Severity.INFO]
    
    def has_errors(self) -> bool:
        """Check if report contains any errors"""
        return len(self.get_errors()) > 0
    
    def has_warnings(self) -> bool:
        """Check if report contains any warnings"""
        return len(self.get_warnings()) > 0
    
    def total_issues(self) -> int:
        """Get total number of issues"""
        return len(self.issues)
    
    def merge(self, other_report: 'QCReport'):
        """Merge another report into this one"""
        for issue in other_report.issues:
            self.add_issue(issue) 
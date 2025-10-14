"""
LEF File Quality Checker

Validates LEF file data structure including:
- Cell existence and structure validation
- Pin definitions and directions
- Basic LEF format compliance
"""

from typing import Dict, List, Any, Optional
from .models import QCIssue, QCReport, Severity


class LefChecker:
    """Quality checker for LEF file data"""
    
    def __init__(self):
        self.report = QCReport()
    
    def check_lef_data(self, lef_data: Dict[str, Any]) -> QCReport:
        """
        Main entry point for LEF data validation
        
        Args:
            lef_data: Dictionary containing parsed LEF data with 'cell_dict' key
            
        Returns:
            QCReport: Report containing all found issues
        """
        self.report = QCReport()
        
        # Validate basic structure
        self._check_basic_structure(lef_data)
        
        # Check cell dictionary
        if 'cell_dict' in lef_data:
            self._check_cell_dict(lef_data['cell_dict'])
            
        return self.report
    
    def _check_basic_structure(self, lef_data: Dict[str, Any]):
        """Check if LEF data has required basic structure"""
        if 'cell_dict' not in lef_data:
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="STRUCTURE",
                message="Missing required section: cell_dict",
                file_name="lef_file",
                details={"missing_key": "cell_dict"}
            ))
        elif lef_data['cell_dict'] is None:
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="STRUCTURE",
                message="Section cell_dict is None",
                file_name="lef_file",
                details={"null_key": "cell_dict"}
            ))
    
    def _check_cell_dict(self, cell_dict: Dict[str, Any]):
        """Check cell dictionary for quality issues"""
        if not cell_dict:
            self.report.add_issue(QCIssue(
                severity=Severity.WARNING,
                category="CELLS",
                message="No cells found in LEF file",
                file_name="lef_file",
                details={"cell_count": 0}
            ))
            return
        
        # Check cell count
        cell_count = len(cell_dict)
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="CELLS",
            message=f"Found {cell_count} cells",
            file_name="lef_file",
            details={"cell_count": cell_count}
        ))
        
        # Check each cell
        all_cells_unique = True
        cell_names = list(cell_dict.keys())
        
        # Check for uniqueness (should always be true for dict keys, but good to verify)
        if len(cell_names) != len(set(cell_names)):
            all_cells_unique = False
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="CELLS",
                message="Duplicate cell names detected",
                file_name="lef_file",
                details={"cell_names": cell_names}
            ))
        
        if all_cells_unique:
            self.report.add_issue(QCIssue(
                severity=Severity.INFO,
                category="CELLS",
                message="All cells are unique",
                file_name="lef_file",
                details={"unique_cell_count": cell_count}
            ))
        
        # Validate each cell
        total_pins = 0
        input_pins = 0
        output_pins = 0
        other_pins = 0
        
        for cell_name, cell_data in cell_dict.items():
            self._check_single_cell(cell_name, cell_data)
            
            # Count pins by direction
            if 'pins' in cell_data:
                pins = cell_data['pins']
                total_pins += len(pins)
                
                for pin_name, pin_data in pins.items():
                    if 'direction' in pin_data:
                        direction = pin_data['direction']
                        if direction == -1:  # INPUT
                            input_pins += 1
                        elif direction == 1:  # OUTPUT
                            output_pins += 1
                        else:
                            other_pins += 1
                    else:
                        other_pins += 1
        
        # Report pin statistics
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="PINS",
            message=f"Pin statistics: {total_pins} total, {input_pins} inputs, {output_pins} outputs, {other_pins} other",
            file_name="lef_file",
            details={
                "total_pins": total_pins,
                "input_pins": input_pins, 
                "output_pins": output_pins,
                "other_pins": other_pins
            }
        ))
    
    def _check_single_cell(self, cell_name: str, cell_data: Dict[str, Any]):
        """Check a single cell for quality issues"""
        # Check if cell has pins section
        if 'pins' not in cell_data:
            self.report.add_issue(QCIssue(
                severity=Severity.WARNING,
                category="CELLS",
                message=f"Cell {cell_name} has no pins section",
                file_name="lef_file",
                details={"cell_name": cell_name, "missing_section": "pins"}
            ))
            return
        
        pins = cell_data['pins']
        if not isinstance(pins, dict):
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="CELLS",
                message=f"Cell {cell_name} pins section is not a dictionary",
                file_name="lef_file",
                details={"cell_name": cell_name, "pins_type": type(pins).__name__}
            ))
            return
        
        pin_count = len(pins)
        if pin_count == 0:
            self.report.add_issue(QCIssue(
                severity=Severity.WARNING,
                category="CELLS",
                message=f"Cell {cell_name} has no pins",
                file_name="lef_file",
                details={"cell_name": cell_name, "pin_count": 0}
            ))
        
        # Check each pin
        pin_names = set()
        for pin_name, pin_data in pins.items():
            # Check for duplicate pin names (shouldn't happen with dict, but good to check)
            if pin_name in pin_names:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="PINS",
                    message=f"Cell {cell_name} has duplicate pin: {pin_name}",
                    file_name="lef_file",
                    details={"cell_name": cell_name, "duplicate_pin": pin_name}
                ))
            else:
                pin_names.add(pin_name)
            
            # Validate pin data structure
            if not isinstance(pin_data, dict):
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="PINS",
                    message=f"Cell {cell_name} pin {pin_name} data is not a dictionary",
                    file_name="lef_file",
                    details={"cell_name": cell_name, "pin_name": pin_name, "pin_data_type": type(pin_data).__name__}
                ))
                continue
            
            # Check pin direction
            if 'direction' not in pin_data:
                self.report.add_issue(QCIssue(
                    severity=Severity.WARNING,
                    category="PINS",
                    message=f"Cell {cell_name} pin {pin_name} missing direction",
                    file_name="lef_file",
                    details={"cell_name": cell_name, "pin_name": pin_name, "missing_field": "direction"}
                ))
            else:
                direction = pin_data['direction']
                if direction not in [-1, 1]:
                    self.report.add_issue(QCIssue(
                        severity=Severity.WARNING,
                        category="PINS",
                        message=f"Cell {cell_name} pin {pin_name} has unusual direction: {direction}",
                        file_name="lef_file",
                        details={"cell_name": cell_name, "pin_name": pin_name, "direction": direction}
                    ))
    
    def check_all_cells_unique(self, cell_dict: Dict[str, Any]) -> bool:
        """
        Check if all cells are unique (convenience method)
        
        Args:
            cell_dict: Dictionary of cell definitions
            
        Returns:
            bool: True if all cells are unique
        """
        if not cell_dict:
            return True
            
        cell_names = list(cell_dict.keys())
        return len(cell_names) == len(set(cell_names))
    
    def get_cell_list(self, cell_dict: Dict[str, Any]) -> List[str]:
        """
        Get list of all cell names
        
        Args:
            cell_dict: Dictionary of cell definitions
            
        Returns:
            List[str]: List of cell names
        """
        return list(cell_dict.keys()) if cell_dict else [] 
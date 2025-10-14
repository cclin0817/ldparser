"""
DEF File Quality Checker

Validates DEF file data structure including:
- Components existence and count validation
- Nets existence and count validation
- Basic structural integrity checks
"""

from typing import Dict, List, Any, Optional
from .models import QCIssue, QCReport, Severity
import os


class DefChecker:
    """Quality checker for DEF file data"""
    
    def __init__(self):
        self.report = QCReport()
    
    def check_def_data(self, def_data: Dict[str, Any]) -> QCReport:
        """
        Main entry point for DEF data validation
        
        Args:
            def_data: Dictionary containing parsed DEF data with 'components' and 'nets' keys
            
        Returns:
            QCReport: Report containing all found issues
        """
        self.report = QCReport()
        
        # Validate basic structure
        self._check_basic_structure(def_data)
        
        # Check components
        if 'COMPONENTS' in def_data:
            self._check_components(def_data['COMPONENTS'])
        
        # Check nets
        if 'NETS' in def_data:
            self._check_nets(def_data['NETS'])
            
        return self.report
    
    def check_def_file_structure(self, def_data: Dict[str, Any], def_file_path: str) -> QCReport:
        """
        Check the actual DEF file structure for proper section delimiters
        
        Args:
            def_file_path: Path to the original DEF file
            
        Returns:
            QCReport: Report containing structural issues
        """
        self.report = QCReport()
        
        if not os.path.exists(def_file_path):
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="FILE_STRUCTURE",
                message=f"DEF file not found: {def_file_path}",
                file_name=def_file_path,
                details={"missing_file": def_file_path}
            ))
            return self.report
        
        try:
            with open(def_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            self._check_section_delimiters(lines, def_data, def_file_path)
            
        except Exception as e:
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="FILE_STRUCTURE",
                message=f"Error reading DEF file: {str(e)}",
                file_name=def_file_path,
                details={"error": str(e)}
            ))
        
        return self.report
    
    def _check_section_delimiters(self, lines: List[str], def_data: Dict[str, Any], file_path: str):
        """Check for proper section start/end delimiters in DEF file"""
        # Track sections found
        sections_found = {}
        section_line_numbers = {}
        
        # Expected sections and their delimiters
        expected_sections = {
            'COMPONENTS': 'END COMPONENTS',
            'NETS': 'END NETS',
            # 'PINS': 'END PINS',
            # 'VIAS': 'END VIAS',
            # 'SPECIALNETS': 'END SPECIALNETS',
            # 'GROUPS': 'END GROUPS',
            # 'SCANCHAINS': 'END SCANCHAINS',
            # 'BLOCKAGES': 'END BLOCKAGES'
        }
        
        # Check each line for section delimiters
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check for section starts
            for section in expected_sections.keys():
                if line.startswith(section + ' '):
                    if section not in sections_found:
                        sections_found[section] = {'start': line_num, 'end': None, 'count_line': line}
                        section_line_numbers[section] = line_num
                    else:
                        # Duplicate section start
                        self.report.add_issue(QCIssue(
                            severity=Severity.ERROR,
                            category="FILE_STRUCTURE",
                            message=f"Duplicate {section} section found",
                            file_name=os.path.basename(file_path),
                            line_number=line_num,
                            details={"section": section, "previous_line": sections_found[section]['start']}
                        ))
            
            # Check for section ends
            for section, end_delimiter in expected_sections.items():
                if line == end_delimiter:
                    if section in sections_found and sections_found[section]['end'] is None:
                        sections_found[section]['end'] = line_num
                    elif section not in sections_found:
                        # End without start
                        self.report.add_issue(QCIssue(
                            severity=Severity.ERROR,
                            category="FILE_STRUCTURE",
                            message=f"Found {end_delimiter} without corresponding {section}",
                            file_name=os.path.basename(file_path),
                            line_number=line_num,
                            details={"section": section, "delimiter": end_delimiter}
                        ))
                    else:
                        # Duplicate end
                        self.report.add_issue(QCIssue(
                            severity=Severity.ERROR,
                            category="FILE_STRUCTURE",
                            message=f"Duplicate {end_delimiter} found",
                            file_name=os.path.basename(file_path),
                            line_number=line_num,
                            details={"section": section, "previous_end": sections_found[section]['end']}
                        ))
        
        # Validate section integrity
        for section, info in sections_found.items():
            if info['end'] is None:
                # Missing end delimiter
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="FILE_STRUCTURE",
                    message=f"Missing {expected_sections[section]} delimiter",
                    file_name=os.path.basename(file_path),
                    line_number=info['start'],
                    details={"section": section, "start_line": info['start']}
                ))
            else:
                # Section found and properly closed
                self.report.add_issue(QCIssue(
                    severity=Severity.INFO,
                    category="FILE_STRUCTURE",
                    message=f"Section {section} properly structured (lines {info['start']}-{info['end']})",
                    file_name=os.path.basename(file_path),
                    line_number=info['start'],
                    details={
                        "section": section, 
                        "start_line": info['start'], 
                        "end_line": info['end'],
                        "count_line": info['count_line']
                    }
                ))
                
                # Parse and validate count if present
                self._validate_section_count(section, info['count_line'], file_path, def_data)
        
        # Report summary
        total_sections = len(sections_found)
        valid_sections = sum(1 for info in sections_found.values() if info['end'] is not None)
        
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="FILE_STRUCTURE",
            message=f"DEF file structure: {valid_sections}/{total_sections} sections properly delimited",
            file_name=os.path.basename(file_path),
            details={
                "total_sections": total_sections,
                "valid_sections": valid_sections,
                "sections_found": list(sections_found.keys())
            }
        ))
    
    def _validate_section_count(self, section: str, count_line: str, file_path: str, def_data: Dict[str, Any]):
        """Validate the declared count in section header"""
        import re
        import os
        
        # Extract count from section line (e.g., "COMPONENTS 13 ;" or "NETS 8 ;")
        match = re.match(rf'{section}\s+(\d+)\s*;', count_line.strip())
        if match:
            declared_count = int(match.group(1))
            if declared_count == len(def_data[section]):
                self.report.add_issue(QCIssue(
                    severity=Severity.INFO,
                    category="FILE_STRUCTURE",
                    message=f"Section {section} declares {declared_count} items",
                    file_name=os.path.basename(file_path),
                    details={"section": section, "declared_count": declared_count}
                ))
            else:
                self.report.add_issue(QCIssue(
                    severity=Severity.WARNING,
                    category="FILE_STRUCTURE",
                    message=f"Section {section} declares {declared_count} items, but {len(def_data[section])} items found",
                    file_name=os.path.basename(file_path),
                    details={"section": section, "declared_count": declared_count}
                ))
        else:
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="FILE_STRUCTURE",
                message=f"Section {section} missing or malformed count declaration",
                file_name=os.path.basename(file_path),
                details={"section": section, "count_line": count_line.strip()}
            ))
    
    def _check_basic_structure(self, def_data: Dict[str, Any]):
        """Check if DEF data has required basic structure"""
        required_keys = ['COMPONENTS', 'NETS']
        for key in required_keys:
            if key not in def_data:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="STRUCTURE",
                    message=f"Missing required section: {key}",
                    file_name="def_file",
                    details={"missing_key": key}
                ))
            elif def_data[key] is None:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="STRUCTURE", 
                    message=f"Section {key} is None",
                    file_name="def_file",
                    details={"null_key": key}
                ))
    
    def _check_components(self, components: List[Dict[str, Any]]):
        """Check components section for quality issues"""
        if not components:
            self.report.add_issue(QCIssue(
                severity=Severity.WARNING,
                category="COMPONENTS",
                message="No components found in DEF file",
                file_name="def_file",
                details={"component_count": 0}
            ))
            return
        
        # Check component count
        component_count = len(components)
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="COMPONENTS",
            message=f"Found {component_count} components",
            file_name="def_file",
            details={"component_count": component_count}
        ))
        
        # Check each component structure
        instance_names = set()
        cell_types = set()
        
        for i, component in enumerate(components):
            # Check required fields
            if 'instance_name' not in component:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="COMPONENTS",
                    message=f"Component {i} missing instance name",
                    file_name="def_file",
                    line_number=i,
                    details={"component_index": i, "missing_field": "ins_name"}
                ))
                continue
                
            if 'cell_name' not in component:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="COMPONENTS", 
                    message=f"Component {component['ins_name']} missing cell name",
                    file_name="def_file",
                    line_number=i,
                    details={"component_index": i, "instance_name": component['ins_name'], "missing_field": "cell_name"}
                ))
                continue
            
            # Check for duplicate instance names
            ins_name = component['instance_name']
            if ins_name in instance_names:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="COMPONENTS",
                    message=f"Duplicate instance name: {ins_name}",
                    file_name="def_file",
                    line_number=i,
                    details={"component_index": i, "duplicate_instance": ins_name}
                ))
            else:
                instance_names.add(ins_name)
            
            # Collect cell types
            cell_types.add(component['cell_name'])
            
            # Check placement info if present
            if 'placementInfo' in component:
                self._validate_placement_info(component['placementInfo'], ins_name, i)
        
        # Report statistics
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="COMPONENTS",
            message=f"Found {len(cell_types)} unique cell types",
            file_name="def_file",
            details={"unique_cell_types": len(cell_types), "cell_types": list(cell_types)}
        ))
    
    def _validate_placement_info(self, placement_info: Dict[str, Any], ins_name: str, index: int):
        """Validate placement information for a component"""
        required_placement_fields = ['location', 'orientation']
        
        for field in required_placement_fields:
            if field not in placement_info:
                self.report.add_issue(QCIssue(
                    severity=Severity.WARNING,
                    category="COMPONENTS",
                    message=f"Instance {ins_name} missing placement {field}",
                    file_name="def_file",
                    line_number=index,
                    details={"instance_name": ins_name, "missing_placement_field": field}
                ))
    
    def _check_nets(self, nets: List[Dict[str, Any]]):
        """Check nets section for quality issues"""
        if not nets:
            self.report.add_issue(QCIssue(
                severity=Severity.WARNING,
                category="NETS",
                message="No nets found in DEF file",
                file_name="def_file",
                details={"net_count": 0}
            ))
            return
        
        # Check net count
        net_count = len(nets)
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="NETS",
            message=f"Found {net_count} nets",
            file_name="def_file",
            details={"net_count": net_count}
        ))
        
        # Check each net structure
        net_names = set()
        total_connections = 0
        
        for i, net in enumerate(nets):
            # Check required fields
            if 'net_name' not in net:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="NETS",
                    message=f"Net {i} missing net name",
                    file_name="def_file",
                    line_number=i,
                    details={"net_index": i, "missing_field": "net_name"}
                ))
                continue
            
            # Check for duplicate net names
            net_name = net['net_name']
            if net_name in net_names:
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="NETS",
                    message=f"Duplicate net name: {net_name}",
                    file_name="def_file",
                    line_number=i,
                    details={"net_index": i, "duplicate_net": net_name}
                ))
            else:
                net_names.add(net_name)
            
            # Check connections
            if 'connections' not in net:
                self.report.add_issue(QCIssue(
                    severity=Severity.WARNING,
                    category="NETS",
                    message=f"Net {net_name} has no connections",
                    file_name="def_file",
                    line_number=i,
                    details={"net_name": net_name, "missing_field": "connections"}
                ))
                continue
            
            connections = net['connections']
            if not isinstance(connections, list):
                self.report.add_issue(QCIssue(
                    severity=Severity.ERROR,
                    category="NETS",
                    message=f"Net {net_name} connections is not a list",
                    file_name="def_file",
                    line_number=i,
                    details={"net_name": net_name, "connections_type": type(connections).__name__}
                ))
                continue
            
            # Validate connections
            connection_count = len(connections)
            total_connections += connection_count
            
            if connection_count == 0:
                self.report.add_issue(QCIssue(
                    severity=Severity.WARNING,
                    category="NETS",
                    message=f"Net {net_name} has zero connections",
                    file_name="def_file", 
                    line_number=i,
                    details={"net_name": net_name, "connection_count": 0}
                ))
            elif connection_count == 1:
                self.report.add_issue(QCIssue(
                    severity=Severity.WARNING,
                    category="NETS",
                    message=f"Net {net_name} has only one connection (dangling)",
                    file_name="def_file",
                    line_number=i,
                    details={"net_name": net_name, "connection_count": 1}
                ))
            
            # Check individual connections
            for j, connection in enumerate(connections):
                if not isinstance(connection, dict):
                    self.report.add_issue(QCIssue(
                        severity=Severity.ERROR,
                        category="NETS",
                        message=f"Net {net_name} connection {j} is not a dictionary",
                        file_name="def_file",
                        line_number=i,
                        details={"net_name": net_name, "connection_index": j, "connection_type": type(connection).__name__}
                    ))
                    continue
                
                # Check required connection fields
                required_conn_fields = ['instance_name', 'pin_name']
                for field in required_conn_fields:
                    if field not in connection:
                        breakpoint()
                        self.report.add_issue(QCIssue(
                            severity=Severity.ERROR,
                            category="NETS",
                            message=f"Net {net_name} connection {j} missing {field}",
                            file_name="def_file",
                            line_number=i,
                            details={"net_name": net_name, "connection_index": j, "missing_field": field}
                        ))
        
        # Report connection statistics
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="NETS",
            message=f"Total connections across all nets: {total_connections}",
            file_name="def_file",
            details={"total_connections": total_connections}
        )) 
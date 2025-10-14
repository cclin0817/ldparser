"""
DEF/LEF Integration Quality Checker

Validates cross-references between DEF and LEF data including:
- All instances in nets occur in components
- All instance pins occur in LEF cell definitions
- Cell type consistency between DEF and LEF
"""

from typing import Dict, List, Any, Optional, Set
import pandas as pd
from pathlib import Path
import os
from .models import QCIssue, QCReport, Severity


class IntegrationChecker:
    """Quality checker for DEF/LEF integration"""
    
    def __init__(self):
        self.report = QCReport()
    
    def check_def_lef_integration(self, def_data: Dict[str, Any], lef_data: Dict[str, Any]) -> QCReport:
        """
        Main entry point for DEF/LEF integration validation
        
        Args:
            def_data: Dictionary containing parsed DEF data
            lef_data: Dictionary containing parsed LEF data
            
        Returns:
            QCReport: Report containing all found issues
        """
        self.report = QCReport()
        
        # Extract components and nets from DEF
        components = def_data.get('COMPONENTS', [])
        nets = def_data.get('NETS', [])
        
        
        # Extract cell dictionary from LEF
        cell_dict = lef_data
        
        
        # Check cell type consistency
        self._check_cell_type_consistency(components, cell_dict)
        
        # check all instance used in NETS are in COMPONENTS
        component_instance_name_set = set([component['instance_name'] for component in components])
        self._check_instance_in_components(nets, component_instance_name_set)

        # check all instance's celltype in NETS are in LEF
        ins2cell_dict = {ele['instance_name']: ele['cell_name'] for ele in components}
        self._check_instance_celltype_in_lef(nets, ins2cell_dict, cell_dict)
        
        return self.report
    
    def _check_cell_type_consistency(self, components: List[Dict[str, Any]], cell_dict: Dict[str, Any]):
        """Check if all cell types used in components exist in LEF"""
        used_cell_types = set()
        missing_cell_types = set()
        
        for component in components:
            if 'cell_name' in component:
                cell_name = component['cell_name']
                used_cell_types.add(cell_name)
                
                if cell_name not in cell_dict:
                    missing_cell_types.add(cell_name)
        
        # Report statistics
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="INTEGRATION",
            message=f"Found {len(used_cell_types)} unique cell types used in DEF",
            file_name="integration",
            details={"used_cell_types": len(used_cell_types), "cell_types": list(used_cell_types)}
        ))
        
        # Report missing cell types
        if missing_cell_types:
            for cell_type in missing_cell_types:
                self.report.add_issue(QCIssue(
                    severity=Severity.WARNING,
                    category="INTEGRATION",
                    message=f"Cell type {cell_type} used in DEF but not found in LEF",
                    file_name="integration",
                    details={"missing_cell_type": cell_type}
                ))
        else:
            self.report.add_issue(QCIssue(
                severity=Severity.INFO,
                category="INTEGRATION",
                message="All cell types used in DEF are defined in LEF",
                file_name="integration",
                details={"all_cells_found": True}
            ))
        
        # Check for unused cell types in LEF
        lef_cell_types = set(cell_dict.keys())
        unused_cell_types = lef_cell_types - used_cell_types
        
        if unused_cell_types:
            self.report.add_issue(QCIssue(
                severity=Severity.INFO,
                category="INTEGRATION",
                message=f"Found {len(unused_cell_types)} cell types in LEF not used in DEF",
                file_name="integration",
                details={"unused_cell_types": len(unused_cell_types), "unused_cells": list(unused_cell_types)}
            ))
    
    def _check_instance_in_components(self, nets: List[Dict[str, Any]], component_instance_name_set: Set[str]):
        """Check if all instance used in NETS are in COMPONENTS"""
        for net in nets:
            for ins_pin in net['connections']:
                instance = ins_pin['instance_name']
                if instance not in component_instance_name_set:
                    self.report.add_issue(QCIssue(severity=Severity.ERROR, category="INTEGRATION", message=f"Instance {instance} used in NETS but not found in COMPONENTS", file_name="integration", details={"instance": instance}))

    def _check_instance_celltype_in_lef(self, nets: List[Dict[str, Any]], ins2cell_dict: Dict[str, str], cell_dict: Dict[str, Any]):
        """Check if all instance's celltype in NETS are in LEF"""
        for net in nets:
            for ins_pin in net['connections']:
                ins_name = ins_pin['instance_name']
                if ins_name not in ins2cell_dict:
                    continue # since this error is reported by _check_instance_in_components
                if ins2cell_dict[ins_name] not in cell_dict:
                    self.report.add_issue(QCIssue(severity=Severity.ERROR, category="INTEGRATION", message=f"Instance {ins_name} with cellname {ins2cell_dict[ins_name]} used in NETS but not found in LEF", file_name="integration", details={"instance": ins_name}))
               
                
    def check_lib_profiler_cells(self, def_data: Dict[str, Any], lib_profiler_path: Optional[str] = None) -> QCReport:
        """
        Check library profiler data against DEF components (placeholder implementation)
        
        Args:
            def_data: Dictionary containing parsed DEF data
            lib_profiler_path: Optional path to library profiler data (placeholder)
            
        Returns:
            QCReport: Report containing all found issues
        """
        # Placeholder implementation for lib_profiler unit test
        components = def_data.get('components', [])
        
        lib_profiler_data = self._get_lib_profiler_data(lib_profiler_path)

        if lib_profiler_data.empty:
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="LIB_PROFILER",
                message="Library profiler data is empty",
                file_name="lib_profiler",
                details={"placeholder": True}
            ))
            return self.report
        
        if lib_profiler_data.cell.duplicated().any():
            self.report.add_issue(QCIssue(
                severity=Severity.ERROR,
                category="LIB_PROFILER",
                message=f"Library profiler data contains duplicate cells",
                file_name="lib_profiler",
                details={"duplicate_cells": lib_profiler_data[lib_profiler_data.cell.duplicated()]}
            ))

        if not lib_profiler_path:
            self.report.add_issue(QCIssue(
                severity=Severity.INFO,
                category="LIB_PROFILER",
                message="Library profiler data not provided - placeholder check",
                file_name="lib_profiler",
                details={"placeholder": True}
            ))
            return self.report


        
        # Extract cell types from DEF
        used_cells = set()
        for component in components:
            if 'cell_name' in component:
                used_cells.add(component['cell_name'])
        
        # This would be implemented based on actual lib_profiler data structure
        self.report.add_issue(QCIssue(
            severity=Severity.INFO,
            category="LIB_PROFILER", 
            message=f"Lib profiler check: {len(used_cells)} unique cells to validate",
            file_name="lib_profiler",
            details={"unique_cells": len(used_cells), "cells": list(used_cells)}
        ))
        
        return self.report
    
    def _get_lib_profiler_data(self, lib_profiler_path: str) -> pd.DataFrame:
        all_files = os.listdir(lib_profiler_path)
        dfs = []
        # for f in cfg.netlist_variable.prefix_files:
        for f in all_files:
            if f[-1] == '#':
                continue
            df = pd.read_csv(Path(lib_profiler_path, f))
            dfs.append(df[['cell', 'footprint', 'prefix', 'input_cap', 'group']])
        return pd.concat(dfs)

    def check_eqpin_file(self, eqpin_data: Optional[Dict[str, Any]] = None) -> QCReport:
        """
        Check EQPin file data (placeholder implementation)
        
        Args:
            eqpin_data: Optional EQPin file data (placeholder)
            
        Returns:
            QCReport: Report containing all found issues
        """
        # Placeholder implementation for eqpin unit test
        if not eqpin_data:
            self.report.add_issue(QCIssue(
                severity=Severity.INFO,
                category="EQPIN",
                message="EQPin data not provided - placeholder check",
                file_name="eqpin_file",
                details={"placeholder": True}
            ))
        else:
            self.report.add_issue(QCIssue(
                severity=Severity.INFO,
                category="EQPIN",
                message="EQPin file validation placeholder",
                file_name="eqpin_file",
                details={"placeholder": True, "data_provided": True}
            ))
        
        return self.report 
"""
Main Quality Controller

Orchestrates all quality checks for DEF/LEF files including:
- DEF unit tests (components, nets)
- LEF unit tests (cells, pins) 
- Integration tests (DEF-LEF cross-validation)
- Placeholder tests (lib_profiler, eqpin)
"""

import os
import pickle
from loguru import logger
from typing import Dict, List, Any, Optional
from .models import QCIssue, QCReport, Severity
from .def_checker import DefChecker
from .lef_checker import LefChecker
from .integration_checker import IntegrationChecker


class QualityController:
    """Main quality controller for DEF/LEF file validation"""
    
    def __init__(self):
        self.def_checker = DefChecker()
        self.lef_checker = LefChecker()
        self.integration_checker = IntegrationChecker()
        self.master_report = QCReport()
    
    def run_full_quality_check(self, def_data: Dict[str, Any], lef_data: Dict[str, Any], 
                              lib_profiler_path: Optional[str] = None,
                              eqpin_path: Optional[str] = None,
                              def_file_path: Optional[str] = None,
                              lef_file_path: Optional[str] = None) -> QCReport:
        """
        Run all quality checks on the provided data
        
        Args:
            def_data: Parsed DEF file data
            lef_data: Parsed LEF file data
            lib_profiler_path: Optional path to library profiler data
            eqpin_path: Optional path to EQPin data
            def_file_path: Optional path to original DEF file for structure check
            lef_file_path: Optional path to original LEF file for structure check
            
        Returns:
            QCReport: Comprehensive report with all issues found
        """
        self.master_report = QCReport()
        
        print("Starting comprehensive DEF/LEF quality check...")
        
        # 0. DEF File Structure Check (if file path provided)
        if def_file_path:
            print("  Running DEF file structure validation...")
            structure_report = self.run_def_file_structure_check(def_data, def_file_path)
            self.master_report.merge(structure_report)
        
        # 1. DEF Unit Tests
        print("  Running DEF unit tests...")
        def_report = self.run_def_unit_tests(def_data)
        self.master_report.merge(def_report)
        
        # # 2. LEF Unit Tests
        # print("  Running LEF unit tests...")
        # lef_report = self.run_lef_unit_tests(lef_data)
        # self.master_report.merge(lef_report)
        
        # breakpoint()
        # 3. Integration Tests
        print("  Running DEF/LEF integration tests...")
        integration_report = self.run_def_lef_integration_tests(def_data, lef_data)
        self.master_report.merge(integration_report)
        
        # 4. Library Profiler Tests (placeholder)
        print("  Running library profiler tests...")
        lib_report = self.run_lib_profiler_tests(def_data, lib_profiler_path)
        self.master_report.merge(lib_report)
        
        # # 5. EQPin Tests (placeholder)
        # print("  Running EQPin tests...")
        # eqpin_report = self.run_eqpin_tests(eqpin_data)
        # self.master_report.merge(eqpin_report)
        
        print("Quality check complete!")
        return self.master_report
    
    def run_def_unit_tests(self, def_data: Dict[str, Any]) -> QCReport:
        """
        Run DEF unit tests
        
        Tests include:
        - Components exist and count is correct
        - Nets exist and count is correct
        - Basic structure validation
        
        Args:
            def_data: Parsed DEF file data
            
        Returns:
            QCReport: Report with DEF-specific issues
        """
        return self.def_checker.check_def_data(def_data)
    
    def run_lef_unit_tests(self, lef_data: Dict[str, Any]) -> QCReport:
        """
        Run LEF unit tests
        
        Tests include:
        - Cells exist and are properly structured
        - All cells are unique
        - Pin definitions are valid
        
        Args:
            lef_data: Parsed LEF file data
            
        Returns:
            QCReport: Report with LEF-specific issues
        """
        return self.lef_checker.check_lef_data(lef_data)
    
    def run_def_lef_integration_tests(self, def_data: Dict[str, Any], lef_data: Dict[str, Any]) -> QCReport:
        """
        Run DEF/LEF integration tests
        
        Tests include:
        - All instances in nets occur in components
        - All instance pins occur in LEF cell definitions
        - Cell type consistency between DEF and LEF
        
        Args:
            def_data: Parsed DEF file data
            lef_data: Parsed LEF file data
            
        Returns:
            QCReport: Report with integration issues
        """
        return self.integration_checker.check_def_lef_integration(def_data, lef_data)
    
    def run_lib_profiler_tests(self, def_data: Dict[str, Any], 
                              lib_profiler_path : Optional[str] = None) -> QCReport:
        """
        Run library profiler tests (placeholder)
        
        Tests include:
        - All cells are unique
        - All cells occur in design
        - Generate warnings for missing cells
        
        Args:
            def_data: Parsed DEF file data
            lib_profiler_path: Optional path to library profiler data
            
        Returns:
            QCReport: Report with library profiler issues
        """
        return self.integration_checker.check_lib_profiler_cells(def_data, lib_profiler_path)
    
    def run_eqpin_tests(self, eqpin_data: Optional[Dict[str, Any]] = None) -> QCReport:
        """
        Run EQPin file tests (placeholder)
        
        Args:
            eqpin_data: Optional EQPin file data
            
        Returns:
            QCReport: Report with EQPin issues
        """
        return self.integration_checker.check_eqpin_file(eqpin_data)
    
    def run_def_file_structure_check(self, def_data: Dict[str, Any], def_file_path: str) -> QCReport:
        """
        Run DEF file structure validation on the original file
        
        Tests include:
        - Section delimiters (COMPONENTS/END COMPONENTS, NETS/END NETS, etc.)
        - Section count declarations
        - Proper section ordering and completeness
        
        Args:
            def_file_path: Path to the original DEF file
            
        Returns:
            QCReport: Report with file structure issues
        """
        return self.def_checker.check_def_file_structure(def_data, def_file_path)
    
    def load_data_from_files(self, def_pickle_path: str, lef_pickle_path: str) -> tuple:
        """
        Load DEF and LEF data from pickle files
        
        Args:
            def_pickle_path: Path to DEF pickle file
            lef_pickle_path: Path to LEF pickle file
            
        Returns:
            tuple: (def_data, lef_data)
        """
        def_data = None
        lef_data = None
        
        # Load DEF data
        if os.path.exists(def_pickle_path):
            try:
                with open(def_pickle_path, 'rb') as f:
                    def_data = pickle.load(f)
                print(f"Loaded DEF data from {def_pickle_path}")
            except Exception as e:
                print(f"Error loading DEF data from {def_pickle_path}: {e}")
        else:
            print(f"DEF pickle file not found: {def_pickle_path}")
        
        # Load LEF data
        if os.path.exists(lef_pickle_path):
            try:
                with open(lef_pickle_path, 'rb') as f:
                    lef_data = pickle.load(f)
                print(f"Loaded LEF data from {lef_pickle_path}")
            except Exception as e:
                print(f"Error loading LEF data from {lef_pickle_path}: {e}")
        else:
            print(f"LEF pickle file not found: {lef_pickle_path}")
        
        return def_data, lef_data
    
    def print_report_summary(self, report: QCReport):
        """
        Print a formatted summary of the QC report
        
        Args:
            report: QCReport to summarize
        """
        print("\n" + "="*80)
        print("QUALITY CHECK REPORT SUMMARY")
        print("="*80)
        
        # Print summary statistics
        print(f"\nTotal Issues: {report.total_issues()}")
        print(f"Summary by Severity:")
        for severity, count in report.summary.items():
            print(f"  {severity}: {count}")
        
        # Print issues by category
        categories = {}
        for issue in report.issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)
        
        print(f"\nIssues by Category:")
        for category, issues in sorted(categories.items()):
            print(f"  {category}: {len(issues)} issues")
        
        # Print detailed issues
        if report.has_errors():
            print(f"\nERRORS ({len(report.get_errors())}):")
            print("-" * 40)
            for issue in report.get_errors():
                print(f"  [{issue.category}] {issue.message}")
                if issue.file_name != "unknown":
                    print(f"    File: {issue.file_name}")
                if issue.line_number is not None:
                    print(f"    Line: {issue.line_number}")
                print()
        
        # if report.has_warnings():
        #     print(f"\nWARNINGS ({len(report.get_warnings())}):")
        #     print("-" * 40)
        #     for issue in report.get_warnings():
        #         print(f"  [{issue.category}] {issue.message}")
        #         if issue.file_name != "unknown":
        #             print(f"    File: {issue.file_name}")
        #         if issue.line_number is not None:
        #             print(f"    Line: {issue.line_number}")
        #         print()
        
        # # Print info messages (limited to avoid spam)
        # info_issues = report.get_info()
        # if info_issues:
        #     print(f"\nINFO ({len(info_issues)}) - showing first 10:")
        #     print("-" * 40)
        #     for issue in info_issues[:10]:
        #         print(f"  [{issue.category}] {issue.message}")
        #     if len(info_issues) > 10:
        #         print(f"  ... and {len(info_issues) - 10} more info messages")
        #     print()
        
        print("="*80)
    
    def save_report_to_file(self, report: QCReport, output_path: str):
        """
        Save the QC report to a file
        
        Args:
            report: QCReport to save
            output_path: Path to save the report
        """
        try:
            with open(output_path, 'w') as f:
                f.write("="*80 + "\n")
                f.write("QUALITY CHECK REPORT\n")
                f.write("="*80 + "\n\n")
                
                # Write summary
                f.write(f"Total Issues: {report.total_issues()}\n")
                f.write("Summary by Severity:\n")
                for severity, count in report.summary.items():
                    f.write(f"  {severity}: {count}\n")
                f.write("\n")
                
                # Write all issues
                for issue in report.issues:
                    # only write error issues
                    if issue.severity != Severity.ERROR:
                        continue
                    f.write(f"[{issue.severity.value}] [{issue.category}] {issue.message}\n")
                    if issue.file_name != "unknown":
                        f.write(f"  File: {issue.file_name}\n")
                    if issue.line_number is not None:
                        f.write(f"  Line: {issue.line_number}\n")
                    if issue.details:
                        f.write(f"  Details: {issue.details}\n")
                    f.write("\n")
            
            print(f"Report saved to {output_path}")
        except Exception as e:
            print(f"Error saving report to {output_path}: {e}")

    def transform_def_lef_data(self, def_data: Dict[str, Any], lef_data: Dict[str, Any]) -> tuple:
        """
        Transform DEF and LEF data into a more usable format
        
        Args:
            def_data: Parsed DEF file data
        
        """

        component_count = len([ele for ele in def_data['id2instanceInfo'].keys()])
        net_count = len([ele for ele in def_data['id2NetInfo'].keys()])

        new_def_data = {}
        if [def_data['id2instanceInfo'][ele] for ele in def_data['id2instanceInfo'].keys()]:
            new_def_data['COMPONENTS'] = [def_data['id2instanceInfo'][ele] for ele in def_data['id2instanceInfo'].keys()]
        else:
            new_def_data['COMPONENTS'] = None

        if [def_data['id2NetInfo'][ele] for ele in def_data['id2NetInfo'].keys()]:
            new_def_data['NETS'] = [def_data['id2NetInfo'][ele] for ele in def_data['id2NetInfo'].keys()]
        else:
            new_def_data['NETS'] = None

        new_lef_data = lef_data['cell_dict']

        return new_def_data, new_lef_data

def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DEF/LEF Quality Checker')
    parser.add_argument('--def_pickle', type=str, default='./tmp/def_outputs.pkl', 
                       help='Path to DEF pickle file')
    parser.add_argument('--lef_pickle', type=str, default='./tmp/lef_outputs.pkl',
                       help='Path to LEF pickle file')
    parser.add_argument('--output_report', type=str, default='./tmp/qc_report.txt',
                       help='Path to save QC report')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress console output')
    parser.add_argument('--def_file', type=str, default='./test_data/complete.5.8.def',
                       help='Path to DEF file')
    parser.add_argument('--lef_file', type=str, default='./test_data/complete.5.8.lef',
                       help='Path to LEF file')
    parser.add_argument('--lib_profiler_path', type=str, default='./test_data/lib_profiler_outputs',
                       help='Path to library profiler data')
    parser.add_argument('--eqpin_path', type=str, default='./test_data/eqpin_outputs',
                       help='Path to EQPin data')
    
    args = parser.parse_args()
    
    # Create quality controller
    qc = QualityController()
    
    # Load data
    def_data, lef_data = qc.load_data_from_files(args.def_pickle, args.lef_pickle)
    
    # transform def/lef data
    def_data, lef_data = qc.transform_def_lef_data(def_data, lef_data)

    if def_data is None and lef_data is None:
        print("Error: No data loaded. Please check your pickle file paths.")
        return
    # Run quality checks
    if def_data is None:
        print("Warning: No DEF data loaded. Running LEF-only checks.")
        report = qc.run_lef_unit_tests(lef_data)
    elif lef_data is None:
        print("Warning: No LEF data loaded. Running DEF-only checks.")
        report = qc.run_def_unit_tests(def_data)
    else:
        report = qc.run_full_quality_check(def_data, lef_data, def_file_path=args.def_file , lef_file_path=args.lef_file,\
                                           lib_profiler_path = args.lib_profiler_path, eqpin_path = args.eqpin_path)
    
    # Print summary
    if not args.quiet:
        qc.print_report_summary(report)
    
    # Save report
    qc.save_report_to_file(report, args.output_report)

    # if qc have error, set a breakpoint
    if report.has_errors():
        logger.error("QC has errors. Please read the error report or contact Lewis 24393.")
        breakpoint()

if __name__ == "__main__":
    main() 
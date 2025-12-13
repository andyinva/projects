"""
Dependency checker for Bridge Test Tool
Checks for required Python version and modules before starting
"""

import sys
import platform
from typing import Tuple, List, Dict


class DependencyChecker:
    """Check for required dependencies"""

    # Minimum Python version required
    MIN_PYTHON_VERSION = (3, 7)

    # Required standard library modules
    REQUIRED_MODULES = {
        'tkinter': {
            'description': 'GUI framework',
            'critical': True,
            'install_instructions': {
                'linux': 'sudo apt-get install python3-tk  # Debian/Ubuntu\nsudo yum install python3-tkinter  # RedHat/CentOS\nsudo pacman -S tk  # Arch Linux',
                'darwin': 'Tkinter is included with Python on macOS',
                'windows': 'Tkinter is included with Python on Windows'
            }
        },
        'socket': {
            'description': 'Network communication',
            'critical': True,
            'install_instructions': {
                'all': 'Socket is a standard library module and should be included with Python'
            }
        },
        'sqlite3': {
            'description': 'Database support',
            'critical': True,
            'install_instructions': {
                'all': 'SQLite3 is a standard library module and should be included with Python'
            }
        },
        'threading': {
            'description': 'Multi-threading support',
            'critical': True,
            'install_instructions': {
                'all': 'Threading is a standard library module and should be included with Python'
            }
        },
        'json': {
            'description': 'JSON encoding/decoding',
            'critical': True,
            'install_instructions': {
                'all': 'JSON is a standard library module and should be included with Python'
            }
        }
    }

    def __init__(self):
        """Initialize dependency checker"""
        self.missing_modules = []
        self.warnings = []
        self.python_version_ok = False
        self.all_modules_ok = False

    def check_python_version(self) -> Tuple[bool, str]:
        """
        Check if Python version meets minimum requirements

        Returns:
            Tuple of (success: bool, message: str)
        """
        current_version = sys.version_info[:2]
        required_version = self.MIN_PYTHON_VERSION

        if current_version >= required_version:
            self.python_version_ok = True
            return True, f"✓ Python {current_version[0]}.{current_version[1]} (OK)"
        else:
            msg = (f"✗ Python {current_version[0]}.{current_version[1]} is too old\n"
                   f"  Required: Python {required_version[0]}.{required_version[1]}+\n"
                   f"  Please upgrade Python from https://www.python.org/downloads/")
            return False, msg

    def check_module(self, module_name: str) -> Tuple[bool, str]:
        """
        Check if a module can be imported

        Args:
            module_name: Name of the module to check

        Returns:
            Tuple of (success: bool, message: str)
        """
        module_info = self.REQUIRED_MODULES.get(module_name, {})
        description = module_info.get('description', module_name)

        try:
            __import__(module_name)
            return True, f"✓ {module_name} ({description}) - OK"
        except ImportError as e:
            self.missing_modules.append(module_name)
            msg = f"✗ {module_name} ({description}) - MISSING\n"
            msg += f"  Error: {str(e)}\n"

            # Add installation instructions
            install_info = module_info.get('install_instructions', {})
            system = platform.system().lower()

            if system in install_info:
                msg += f"\n  Installation:\n  {install_info[system]}"
            elif 'all' in install_info:
                msg += f"\n  Installation:\n  {install_info['all']}"

            return False, msg

    def check_all_modules(self) -> Tuple[bool, List[str]]:
        """
        Check all required modules

        Returns:
            Tuple of (all_ok: bool, messages: List[str])
        """
        messages = []
        all_ok = True

        for module_name in self.REQUIRED_MODULES.keys():
            success, msg = self.check_module(module_name)
            messages.append(msg)
            if not success:
                all_ok = False

        self.all_modules_ok = all_ok
        return all_ok, messages

    def check_optional_modules(self) -> List[str]:
        """
        Check for optional modules that enhance functionality

        Returns:
            List of messages about optional modules
        """
        optional_modules = {
            'matplotlib': 'Graphing and visualization',
            'numpy': 'Advanced statistics',
            'pandas': 'Data analysis'
        }

        messages = []
        for module_name, description in optional_modules.items():
            try:
                __import__(module_name)
                messages.append(f"✓ {module_name} ({description}) - Available")
            except ImportError:
                messages.append(f"○ {module_name} ({description}) - Not installed (optional)")

        return messages

    def get_system_info(self) -> Dict[str, str]:
        """
        Get system information

        Returns:
            Dictionary with system information
        """
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'architecture': platform.machine()
        }

    def run_full_check(self, verbose: bool = True) -> Tuple[bool, str]:
        """
        Run a complete dependency check

        Args:
            verbose: Whether to include detailed information

        Returns:
            Tuple of (all_ok: bool, report: str)
        """
        report_lines = []

        if verbose:
            report_lines.append("=" * 60)
            report_lines.append("Bridge Test Tool - Dependency Check")
            report_lines.append("=" * 60)
            report_lines.append("")

        # System information
        if verbose:
            report_lines.append("System Information:")
            sys_info = self.get_system_info()
            report_lines.append(f"  Platform: {sys_info['platform']}")
            report_lines.append(f"  Python: {sys_info['python_version']} ({sys_info['python_implementation']})")
            report_lines.append("")

        # Check Python version
        report_lines.append("Checking Python Version:")
        py_ok, py_msg = self.check_python_version()
        report_lines.append(f"  {py_msg}")
        report_lines.append("")

        # Check required modules
        report_lines.append("Checking Required Modules:")
        modules_ok, module_msgs = self.check_all_modules()
        for msg in module_msgs:
            # Indent multi-line messages
            for line in msg.split('\n'):
                report_lines.append(f"  {line}")
        report_lines.append("")

        # Check optional modules
        if verbose:
            report_lines.append("Checking Optional Modules:")
            optional_msgs = self.check_optional_modules()
            for msg in optional_msgs:
                report_lines.append(f"  {msg}")
            report_lines.append("")

        # Summary
        all_ok = py_ok and modules_ok

        report_lines.append("=" * 60)
        if all_ok:
            report_lines.append("✓ All dependencies satisfied - Ready to run!")
        else:
            report_lines.append("✗ Missing dependencies - Please install them first")
            report_lines.append("")

            if not py_ok:
                report_lines.append("Action Required:")
                report_lines.append("  1. Upgrade Python to version 3.7 or higher")
                report_lines.append("     Download from: https://www.python.org/downloads/")

            if self.missing_modules:
                report_lines.append("")
                report_lines.append("Missing Modules:")
                for module in self.missing_modules:
                    module_info = self.REQUIRED_MODULES.get(module, {})
                    desc = module_info.get('description', '')
                    report_lines.append(f"  • {module} ({desc})")

                # Special help for tkinter (most common issue)
                if 'tkinter' in self.missing_modules:
                    report_lines.append("")
                    report_lines.append("Tkinter is usually missing on Linux systems.")
                    report_lines.append("Install it with:")
                    system = platform.system().lower()
                    if system == 'linux':
                        report_lines.append("  sudo apt-get install python3-tk     # Debian/Ubuntu")
                        report_lines.append("  sudo yum install python3-tkinter    # RedHat/CentOS")
                        report_lines.append("  sudo pacman -S tk                   # Arch Linux")

        report_lines.append("=" * 60)

        report = "\n".join(report_lines)
        return all_ok, report


def check_dependencies(verbose: bool = True) -> bool:
    """
    Convenience function to check dependencies

    Args:
        verbose: Whether to print detailed information

    Returns:
        True if all dependencies are satisfied, False otherwise
    """
    checker = DependencyChecker()
    all_ok, report = checker.run_full_check(verbose=verbose)

    if verbose:
        print(report)

    return all_ok


def check_and_exit_if_missing(verbose: bool = True) -> None:
    """
    Check dependencies and exit with error code if any are missing

    Args:
        verbose: Whether to print detailed information
    """
    if not check_dependencies(verbose=verbose):
        sys.exit(1)


if __name__ == '__main__':
    # Run as standalone script
    check_and_exit_if_missing(verbose=True)

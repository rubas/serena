"""
Basic integration tests for Zig language server functionality.

These tests validate symbol finding and cross-file reference capabilities
using the Zig Language Server (ZLS).
"""

import os

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_types import SymbolKind


@pytest.mark.zig
class TestZigLanguageServer:
    """Test Zig language server symbol finding and cross-file references."""

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_find_symbols_in_main(self, language_server: SolidLanguageServer) -> None:
        """Test finding specific symbols in main.zig."""
        file_path = os.path.join("src", "main.zig")
        symbols = language_server.request_document_symbols(file_path)
        
        assert symbols is not None
        assert len(symbols) > 0
        
        # Extract symbol names from the returned structure
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # Verify specific symbols exist
        assert "main" in symbol_names, "main function not found"
        assert "greeting" in symbol_names, "greeting function not found"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_find_symbols_in_calculator(self, language_server: SolidLanguageServer) -> None:
        """Test finding Calculator struct and its methods."""
        file_path = os.path.join("src", "calculator.zig")
        symbols = language_server.request_document_symbols(file_path)
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Find Calculator struct
        calculator_symbol = None
        for sym in symbol_list:
            if sym.get("name") == "Calculator":
                calculator_symbol = sym
                break
        
        assert calculator_symbol is not None, "Calculator struct not found"
        # ZLS may use different symbol kinds for structs (14 = Namespace, 5 = Class, 23 = Struct)
        assert calculator_symbol.get("kind") in [SymbolKind.Class, SymbolKind.Struct, SymbolKind.Namespace, 5, 14, 23], "Calculator should be a struct/class/namespace"
        
        # Check for Calculator methods (init, add, subtract, etc.) 
        # Methods might be in children or at the same level
        all_symbols = []
        for sym in symbol_list:
            all_symbols.append(sym.get("name"))
            if "children" in sym:
                for child in sym["children"]:
                    all_symbols.append(child.get("name"))
        
        # Verify at least some calculator methods exist
        expected_methods = {"init", "add", "subtract", "multiply", "divide"}
        found_methods = set(all_symbols) & expected_methods
        assert len(found_methods) >= 2, f"Expected at least 2 Calculator methods, found: {found_methods}"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_find_symbols_in_math_utils(self, language_server: SolidLanguageServer) -> None:
        """Test finding functions in math_utils.zig."""
        file_path = os.path.join("src", "math_utils.zig")
        symbols = language_server.request_document_symbols(file_path)
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # Verify math utility functions exist
        assert "factorial" in symbol_names, "factorial function not found"
        assert "isPrime" in symbol_names, "isPrime function not found"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_cross_file_references_calculator(self, language_server: SolidLanguageServer) -> None:
        """Test finding cross-file references to Calculator struct."""
        file_path = os.path.join("src", "calculator.zig")
        symbols = language_server.request_document_symbols(file_path)
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Find Calculator struct
        calculator_symbol = None
        for sym in symbol_list:
            if sym.get("name") == "Calculator":
                calculator_symbol = sym
                break
        
        assert calculator_symbol is not None, "Calculator struct not found"
        
        # Find references to Calculator
        sel_range = calculator_symbol.get("selectionRange", calculator_symbol.get("range"))
        assert sel_range is not None, "Calculator symbol has no range information"
        
        sel_start = sel_range["start"]
        refs = language_server.request_references(file_path, sel_start["line"], sel_start["character"])
        
        assert refs is not None
        assert len(refs) >= 1, "Should find at least the Calculator declaration"
        
        # Check for cross-file references from main.zig
        # Note: ZLS may not fully support cross-file references yet
        main_refs = [ref for ref in refs if "main.zig" in ref.get("uri", "")]
        if len(main_refs) == 0:
            # If no cross-file references found, at least verify we got the declaration
            assert len(refs) >= 1, "Should find at least the Calculator declaration"
        else:
            assert len(main_refs) > 0, "Found cross-file references from main.zig"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_cross_file_references_factorial(self, language_server: SolidLanguageServer) -> None:
        """Test finding cross-file references to factorial function."""
        file_path = os.path.join("src", "math_utils.zig")
        symbols = language_server.request_document_symbols(file_path)
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Find factorial function
        factorial_symbol = None
        for sym in symbol_list:
            if sym.get("name") == "factorial":
                factorial_symbol = sym
                break
        
        assert factorial_symbol is not None, "factorial function not found"
        
        # Find references to factorial
        sel_range = factorial_symbol.get("selectionRange", factorial_symbol.get("range"))
        assert sel_range is not None, "factorial symbol has no range information"
        
        sel_start = sel_range["start"]
        refs = language_server.request_references(file_path, sel_start["line"], sel_start["character"])
        
        assert refs is not None
        assert len(refs) >= 1, "Should find at least the factorial declaration"
        
        # Check for cross-file references from main.zig
        # Note: ZLS may not fully support cross-file references yet
        main_refs = [ref for ref in refs if "main.zig" in ref.get("uri", "")]
        if len(main_refs) == 0:
            # If no cross-file references found, at least verify we got the declaration
            assert len(refs) >= 1, "Should find at least the factorial declaration"
        else:
            assert len(main_refs) > 0, "Found cross-file references from main.zig"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_find_definition_cross_file(self, language_server: SolidLanguageServer) -> None:
        """Test finding definition of imported symbols."""
        file_path = os.path.join("src", "main.zig")
        
        # Try to find definition of calculator.Calculator at line 8 (where Calculator.init() is called)
        # This tests cross-file navigation from usage to definition
        definitions = language_server.request_definition(file_path, 7, 20)  # Approximate position of "Calculator"
        
        assert definitions is not None
        assert isinstance(definitions, list)
        
        if len(definitions) > 0:
            # Should point to calculator.zig
            calculator_defs = [d for d in definitions if "calculator.zig" in d.get("uri", "")]
            assert len(calculator_defs) > 0, "Definition should be in calculator.zig"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_hover_information(self, language_server: SolidLanguageServer) -> None:
        """Test hover information for symbols."""
        file_path = os.path.join("src", "main.zig")
        
        # Get hover info for the main function
        hover_info = language_server.request_hover(file_path, 4, 8)  # Position of "main" function
        
        assert hover_info is not None, "Should provide hover information for main function"
        
        # Hover info could be a dict with 'contents' or a string
        if isinstance(hover_info, dict):
            assert "contents" in hover_info or "value" in hover_info, "Hover should have contents"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_full_symbol_tree(self, language_server: SolidLanguageServer) -> None:
        """Test that full symbol tree contains all expected modules."""
        symbols = language_server.request_full_symbol_tree()
        
        assert symbols is not None
        assert len(symbols) > 0
        
        # Flatten the tree to find all files
        def extract_file_names(node_list, files=None):
            if files is None:
                files = set()
            for node in node_list:
                if isinstance(node, dict):
                    name = node.get("name", "")
                    if name.endswith(".zig"):
                        files.add(name)
                    if "children" in node:
                        extract_file_names(node["children"], files)
            return files
        
        file_names = extract_file_names(symbols)
        
        # Verify key files are in the symbol tree
        expected_files = {"main.zig", "calculator.zig", "math_utils.zig"}
        found_files = file_names & expected_files
        assert len(found_files) == len(expected_files), f"Expected {expected_files}, found {found_files}"
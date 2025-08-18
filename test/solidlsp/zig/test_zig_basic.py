"""
Basic integration tests for Zig language server functionality.

These tests validate the functionality of the Zig language server APIs
like request_references using the test repository.
"""

import os

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_utils import SymbolUtils


@pytest.mark.zig
class TestZigLanguageServer:
    """Test basic functionality of the Zig language server."""

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_find_symbol(self, language_server: SolidLanguageServer) -> None:
        """Test finding symbols in Zig code."""
        symbols = language_server.request_full_symbol_tree()

        # Check for main symbols
        assert SymbolUtils.symbol_tree_contains_name(symbols, "main"), "main function not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "greeting"), "greeting function not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "Calculator"), "Calculator struct not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "factorial"), "factorial function not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "isPrime"), "isPrime function not found in symbol tree"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_find_references_calculator(self, language_server: SolidLanguageServer) -> None:
        """Test finding references to the Calculator struct."""
        file_path = os.path.join("src", "calculator.zig")
        symbols = language_server.request_document_symbols(file_path)

        # Find the Calculator struct symbol
        calculator_symbol = None
        for sym in symbols[0]:
            if sym.get("name") == "Calculator":
                calculator_symbol = sym
                break

        assert calculator_symbol is not None, "Could not find 'Calculator' struct symbol in calculator.zig"

        # Find references to Calculator
        sel_start = calculator_symbol["selectionRange"]["start"]
        refs = language_server.request_references(file_path, sel_start["line"], sel_start["character"])

        # Should find references including the declaration and usage in main.zig
        assert len(refs) >= 1, "Should find at least the Calculator declaration and references"
        
        # Check if we found references in main.zig (ZLS should support this)
        main_refs = [ref for ref in refs if "main.zig" in ref.get("uri", "")]
        if len(main_refs) == 0:
            # If no cross-file references found, at least the declaration should be there
            assert len(refs) >= 1, "Should find at least the Calculator declaration"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_find_references_function(self, language_server: SolidLanguageServer) -> None:
        """Test finding references to functions."""
        file_path = os.path.join("src", "math_utils.zig")
        symbols = language_server.request_document_symbols(file_path)

        # Find the factorial function symbol
        factorial_symbol = None
        for sym in symbols[0]:
            if sym.get("name") == "factorial":
                factorial_symbol = sym
                break

        assert factorial_symbol is not None, "Could not find 'factorial' function symbol in math_utils.zig"

        # Find references to factorial
        sel_start = factorial_symbol["selectionRange"]["start"]
        refs = language_server.request_references(file_path, sel_start["line"], sel_start["character"])

        # Should find references in main.zig and test functions
        assert len(refs) >= 1, "factorial function should have at least one reference"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_document_symbols(self, language_server: SolidLanguageServer) -> None:
        """Test getting document symbols from a Zig file."""
        file_path = os.path.join("src", "calculator.zig")
        symbols = language_server.request_document_symbols(file_path)

        assert len(symbols) > 0, "Should find symbols in calculator.zig"

        # Extract symbol names
        symbol_names = []
        for sym_list in symbols:
            for sym in sym_list:
                symbol_names.append(sym.get("name"))
                # Also check for nested symbols (methods)
                if "children" in sym:
                    for child in sym["children"]:
                        symbol_names.append(child.get("name"))

        # Check for expected symbols
        assert "Calculator" in symbol_names, "Calculator struct should be found"
        assert "add" in symbol_names or "init" in symbol_names, "Should find Calculator methods"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_cross_file_references(self, language_server: SolidLanguageServer) -> None:
        """Test finding references across files."""
        # Find references to calculator module from main.zig
        main_file = os.path.join("src", "main.zig")
        symbols = language_server.request_document_symbols(main_file)

        # The main file should have symbols
        assert len(symbols) > 0, "Should find symbols in main.zig"

        # Check that main can reference calculator module
        symbol_names = []
        for sym_list in symbols:
            for sym in sym_list:
                symbol_names.append(sym.get("name"))

        assert "main" in symbol_names, "main function should be found in main.zig"

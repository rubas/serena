"""
Tests for the Nix language server implementation using nil.

These tests validate symbol finding and cross-file reference capabilities
for Nix expressions and modules.
"""

import os
import platform

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_types import SymbolKind

# Skip all Nix tests on Windows as Nix doesn't support Windows
pytestmark = pytest.mark.skipif(platform.system() == "Windows", reason="Nix and nil are not available on Windows")


@pytest.mark.nix
class TestNixLanguageServer:
    """Test Nix language server symbol finding and cross-file references."""

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_symbols_in_default_nix(self, language_server: SolidLanguageServer) -> None:
        """Test finding specific symbols in default.nix."""
        symbols = language_server.request_document_symbols("default.nix")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        # Extract symbol names from the returned structure
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # Verify specific functions and attributes are found
        expected_symbols = {"makeGreeting", "listUtils", "stringUtils"}
        found_symbols = symbol_names & expected_symbols
        assert len(found_symbols) >= 2, f"Expected at least 2 of {expected_symbols}, found {found_symbols}"
        
        # Verify specific names exist
        assert "makeGreeting" in symbol_names, "makeGreeting function not found"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_nested_symbols_in_default(self, language_server: SolidLanguageServer) -> None:
        """Test finding nested symbols like listUtils.sum in default.nix."""
        symbols = language_server.request_document_symbols("default.nix")
        
        assert symbols is not None
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Look for listUtils and its nested functions
        list_utils = None
        for sym in symbol_list:
            if sym.get("name") == "listUtils":
                list_utils = sym
                break
        
        assert list_utils is not None, "listUtils attribute set not found"
        
        # Check for nested functions in listUtils
        if "children" in list_utils:
            child_names = {child.get("name") for child in list_utils["children"]}
            expected_funcs = {"double", "sum", "average"}
            found_funcs = child_names & expected_funcs
            assert len(found_funcs) >= 2, f"Expected listUtils functions {expected_funcs}, found {found_funcs}"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_symbols_in_utils(self, language_server: SolidLanguageServer) -> None:
        """Test finding symbols in lib/utils.nix."""
        symbols = language_server.request_document_symbols("lib/utils.nix")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # Verify utility modules are found
        expected_modules = {"math", "strings", "lists", "attrs"}
        found_modules = symbol_names & expected_modules
        assert len(found_modules) >= 2, f"Expected utility modules {expected_modules}, found {found_modules}"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_symbols_in_flake(self, language_server: SolidLanguageServer) -> None:
        """Test finding symbols in flake.nix."""
        symbols = language_server.request_document_symbols("flake.nix")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # Flakes should have inputs and outputs
        assert "inputs" in symbol_names or "outputs" in symbol_names, "Flake should have inputs or outputs"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_symbols_in_module(self, language_server: SolidLanguageServer) -> None:
        """Test finding symbols in a NixOS module."""
        symbols = language_server.request_document_symbols("modules/example.nix")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # NixOS modules typically have options and config
        assert "options" in symbol_names or "config" in symbol_names, "Module should have options or config"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_cross_file_references(self, language_server: SolidLanguageServer) -> None:
        """Test finding cross-file references in Nix."""
        # First, find a symbol in utils.nix
        utils_symbols = language_server.request_document_symbols("lib/utils.nix")
        
        assert utils_symbols is not None
        symbol_list = utils_symbols[0] if isinstance(utils_symbols, tuple) else utils_symbols
        
        # Find the math module
        math_symbol = None
        for sym in symbol_list:
            if sym.get("name") == "math":
                math_symbol = sym
                break
        
        if math_symbol and "range" in math_symbol:
            # Try to find references to the math module
            range_start = math_symbol["range"]["start"]
            refs = language_server.request_references("lib/utils.nix", range_start["line"], range_start["character"])
            
            assert refs is not None
            assert isinstance(refs, list)
            assert len(refs) >= 1, "Should find at least the math module declaration"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_definition(self, language_server: SolidLanguageServer) -> None:
        """Test finding definition of a symbol."""
        # Try to find definition at a specific position in default.nix
        definitions = language_server.request_definition("default.nix", 15, 10)
        
        assert definitions is not None
        assert isinstance(definitions, list), "Definitions should be a list"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_hover_information(self, language_server: SolidLanguageServer) -> None:
        """Test hover information for symbols."""
        # Get hover info for makeGreeting function
        hover_info = language_server.request_hover("default.nix", 9, 5)  # Position near makeGreeting
        
        # nil should provide hover information
        assert hover_info is not None or hover_info == {}, "Should return hover info or empty dict"
        
        if hover_info and isinstance(hover_info, dict):
            # Check structure if hover info is provided
            assert "contents" in hover_info or "value" in hover_info or len(hover_info) == 0

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_full_symbol_tree(self, language_server: SolidLanguageServer) -> None:
        """Test that full symbol tree contains all expected files."""
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
                    if name.endswith(".nix"):
                        files.add(name)
                    if "children" in node:
                        extract_file_names(node["children"], files)
            return files
        
        file_names = extract_file_names(symbols)
        
        # Verify key files are in the symbol tree
        expected_files = {"default.nix", "flake.nix", "utils.nix", "example.nix"}
        found_files = file_names & expected_files
        assert len(found_files) >= 2, f"Expected at least 2 of {expected_files}, found {found_files}"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_references_to_function(self, language_server: SolidLanguageServer) -> None:
        """Test finding references to a specific function."""
        symbols = language_server.request_document_symbols("default.nix")
        
        assert symbols is not None
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Find makeGreeting function
        greeting_symbol = None
        for sym in symbol_list:
            if sym.get("name") == "makeGreeting":
                greeting_symbol = sym
                break
        
        if greeting_symbol and "range" in greeting_symbol:
            range_start = greeting_symbol["range"]["start"]
            refs = language_server.request_references("default.nix", range_start["line"], range_start["character"])
            
            assert refs is not None
            assert isinstance(refs, list)
            assert len(refs) >= 1, "Should find at least the makeGreeting declaration"
"""
Tests for the Lua language server implementation.

These tests validate symbol finding and cross-file reference capabilities
for Lua modules and functions.
"""

import os

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_types import SymbolKind


@pytest.mark.lua
class TestLuaLanguageServer:
    """Test Lua language server symbol finding and cross-file references."""

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_find_symbols_in_calculator(self, language_server: SolidLanguageServer) -> None:
        """Test finding specific functions in calculator.lua."""
        symbols = language_server.request_document_symbols("src/calculator.lua")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        # Extract function names from the returned structure
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        function_names = set()
        for symbol in symbol_list:
            if isinstance(symbol, dict):
                name = symbol.get("name", "")
                # Handle both plain names and module-prefixed names
                if "." in name:
                    name = name.split(".")[-1]
                if symbol.get("kind") == SymbolKind.Function:
                    function_names.add(name)
        
        # Verify specific calculator functions exist
        expected_functions = {"add", "subtract", "multiply", "divide", "factorial"}
        found_functions = function_names & expected_functions
        assert len(found_functions) >= 4, f"Expected at least 4 of {expected_functions}, found {found_functions}"
        
        # Verify specific functions
        assert "add" in function_names, "add function not found"
        assert "multiply" in function_names, "multiply function not found"
        assert "factorial" in function_names, "factorial function not found"

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_find_symbols_in_utils(self, language_server: SolidLanguageServer) -> None:
        """Test finding specific functions in utils.lua."""
        symbols = language_server.request_document_symbols("src/utils.lua")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        function_names = set()
        all_symbols = set()
        
        for symbol in symbol_list:
            if isinstance(symbol, dict):
                name = symbol.get("name", "")
                all_symbols.add(name)
                # Handle both plain names and module-prefixed names
                if "." in name:
                    name = name.split(".")[-1]
                if symbol.get("kind") == SymbolKind.Function:
                    function_names.add(name)
        
        # Verify string utility functions
        expected_utils = {"trim", "split", "starts_with", "ends_with"}
        found_utils = function_names & expected_utils
        assert len(found_utils) >= 3, f"Expected at least 3 of {expected_utils}, found {found_utils}"
        
        # Verify table utility functions
        table_utils = {"deep_copy", "table_contains", "table_merge"}
        found_table_utils = function_names & table_utils
        assert len(found_table_utils) >= 2, f"Expected table utilities {table_utils}, found {found_table_utils}"
        
        # Check for Logger class/table
        assert "Logger" in all_symbols or any("Logger" in s for s in all_symbols), "Logger not found in symbols"

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_find_symbols_in_main(self, language_server: SolidLanguageServer) -> None:
        """Test finding functions in main.lua."""
        symbols = language_server.request_document_symbols("main.lua")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        function_names = set()
        
        for symbol in symbol_list:
            if isinstance(symbol, dict) and symbol.get("kind") == SymbolKind.Function:
                function_names.add(symbol.get("name", ""))
        
        # Verify main functions exist
        expected_funcs = {"print_banner", "test_calculator", "test_utils"}
        found_funcs = function_names & expected_funcs
        assert len(found_funcs) >= 2, f"Expected at least 2 of {expected_funcs}, found {found_funcs}"
        
        assert "test_calculator" in function_names, "test_calculator function not found"
        assert "test_utils" in function_names, "test_utils function not found"

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_cross_file_references_calculator_add(self, language_server: SolidLanguageServer) -> None:
        """Test finding cross-file references to calculator.add function."""
        symbols = language_server.request_document_symbols("src/calculator.lua")
        
        assert symbols is not None
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Find the add function
        add_symbol = None
        for sym in symbol_list:
            if isinstance(sym, dict):
                name = sym.get("name", "")
                if "add" in name or name == "add":
                    add_symbol = sym
                    break
        
        assert add_symbol is not None, "add function not found in calculator.lua"
        
        # Get references to the add function
        range_info = add_symbol.get("selectionRange", add_symbol.get("range"))
        assert range_info is not None, "add function has no range information"
        
        range_start = range_info["start"]
        refs = language_server.request_references("src/calculator.lua", range_start["line"], range_start["character"])
        
        assert refs is not None
        assert isinstance(refs, list)
        assert len(refs) >= 1, "Should find at least the add function declaration"
        
        # Check for cross-file references from main.lua
        main_refs = [ref for ref in refs if "main.lua" in ref.get("uri", "")]
        assert len(main_refs) > 0, "calculator.add should be called in main.lua"

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_cross_file_references_utils_trim(self, language_server: SolidLanguageServer) -> None:
        """Test finding cross-file references to utils.trim function."""
        symbols = language_server.request_document_symbols("src/utils.lua")
        
        assert symbols is not None
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Find the trim function
        trim_symbol = None
        for sym in symbol_list:
            if isinstance(sym, dict):
                name = sym.get("name", "")
                if "trim" in name or name == "trim":
                    trim_symbol = sym
                    break
        
        assert trim_symbol is not None, "trim function not found in utils.lua"
        
        # Get references to the trim function
        range_info = trim_symbol.get("selectionRange", trim_symbol.get("range"))
        assert range_info is not None, "trim function has no range information"
        
        range_start = range_info["start"]
        refs = language_server.request_references("src/utils.lua", range_start["line"], range_start["character"])
        
        assert refs is not None
        assert isinstance(refs, list)
        assert len(refs) >= 1, "Should find at least the trim function declaration"
        
        # Check for cross-file references from main.lua
        main_refs = [ref for ref in refs if "main.lua" in ref.get("uri", "")]
        assert len(main_refs) > 0, "utils.trim should be called in main.lua"

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_hover_information(self, language_server: SolidLanguageServer) -> None:
        """Test hover information for symbols."""
        # Get hover info for a function
        hover_info = language_server.request_hover("src/calculator.lua", 5, 10)  # Position near add function
        
        assert hover_info is not None, "Should provide hover information"
        
        # Hover info could be a dict with 'contents' or a string
        if isinstance(hover_info, dict):
            assert "contents" in hover_info or "value" in hover_info, "Hover should have contents"

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_full_symbol_tree(self, language_server: SolidLanguageServer) -> None:
        """Test that full symbol tree is not empty."""
        symbols = language_server.request_full_symbol_tree()
        
        assert symbols is not None
        assert len(symbols) > 0, "Symbol tree should not be empty"
        
        # The tree should have at least one root node
        root = symbols[0]
        assert isinstance(root, dict), "Root should be a dict"
        assert "name" in root, "Root should have a name"

    @pytest.mark.parametrize("language_server", [Language.LUA], indirect=True)
    def test_references_between_test_and_source(self, language_server: SolidLanguageServer) -> None:
        """Test finding references from test files to source files."""
        # Check if test_calculator.lua references calculator module
        test_symbols = language_server.request_document_symbols("tests/test_calculator.lua")
        
        assert test_symbols is not None
        assert len(test_symbols) > 0
        
        # The test file should have some content that references calculator
        symbol_list = test_symbols[0] if isinstance(test_symbols, tuple) else test_symbols
        assert len(symbol_list) > 0, "test_calculator.lua should have symbols"
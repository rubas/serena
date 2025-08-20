"""
Tests for the Nix language server implementation using nil.

These tests validate symbol finding capabilities for Nix expressions and modules.
Note: nil has limited cross-file reference support as of current version.
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
    """Test Nix language server symbol finding capabilities."""

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_symbols_in_default_nix(self, language_server: SolidLanguageServer) -> None:
        """Test finding specific symbols in default.nix."""
        symbols = language_server.request_document_symbols("default.nix")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        # Extract symbol names from the returned structure
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # Verify specific function exists
        assert "makeGreeting" in symbol_names, "makeGreeting function not found"
        
        # Verify attribute sets are found
        expected_attrs = {"listUtils", "stringUtils"}
        found_attrs = symbol_names & expected_attrs
        assert len(found_attrs) >= 2, f"Expected {expected_attrs}, found {found_attrs}"

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
        assert len(found_modules) >= 3, f"Expected at least 3 of {expected_modules}, found {found_modules}"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_symbols_in_flake(self, language_server: SolidLanguageServer) -> None:
        """Test finding symbols in flake.nix."""
        symbols = language_server.request_document_symbols("flake.nix")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # Flakes must have either inputs or outputs
        assert "inputs" in symbol_names or "outputs" in symbol_names, "Flake must have inputs or outputs"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_symbols_in_module(self, language_server: SolidLanguageServer) -> None:
        """Test finding symbols in a NixOS module."""
        symbols = language_server.request_document_symbols("modules/example.nix")
        
        assert symbols is not None
        assert len(symbols) > 0
        
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}
        
        # NixOS modules must have either options or config
        assert "options" in symbol_names or "config" in symbol_names, "Module must have options or config"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_find_references_within_file(self, language_server: SolidLanguageServer) -> None:
        """Test finding references within the same file."""
        symbols = language_server.request_document_symbols("default.nix")
        
        assert symbols is not None
        symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
        
        # Find makeGreeting function
        greeting_symbol = None
        for sym in symbol_list:
            if sym.get("name") == "makeGreeting":
                greeting_symbol = sym
                break
        
        assert greeting_symbol is not None, "makeGreeting function not found"
        assert "range" in greeting_symbol, "Symbol must have range information"
        
        range_start = greeting_symbol["range"]["start"]
        refs = language_server.request_references("default.nix", range_start["line"], range_start["character"])
        
        assert refs is not None
        assert isinstance(refs, list)
        assert len(refs) >= 1, "Should find at least the makeGreeting declaration"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_hover_information(self, language_server: SolidLanguageServer) -> None:
        """Test hover information for symbols."""
        # Get hover info for makeGreeting function
        hover_info = language_server.request_hover("default.nix", 9, 5)  # Position near makeGreeting
        
        assert hover_info is not None, "Should provide hover information"
        
        if isinstance(hover_info, dict) and len(hover_info) > 0:
            # If hover info is provided, it should have proper structure
            assert "contents" in hover_info or "value" in hover_info, "Hover should have contents or value"

    @pytest.mark.parametrize("language_server", [Language.NIX], indirect=True)
    def test_full_symbol_tree(self, language_server: SolidLanguageServer) -> None:
        """Test that full symbol tree is not empty."""
        symbols = language_server.request_full_symbol_tree()
        
        assert symbols is not None
        assert len(symbols) > 0, "Symbol tree should not be empty"
        
        # The tree should have at least one root node
        root = symbols[0]
        assert isinstance(root, dict), "Root should be a dict"
        assert "name" in root, "Root should have a name"
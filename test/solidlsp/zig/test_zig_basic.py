"""
Basic integration tests for Zig language server functionality.

These tests validate symbol finding and navigation capabilities using the Zig Language Server (ZLS).
Note: ZLS requires files to be open in the editor to find cross-file references (performance optimization).
"""

import os

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_types import SymbolKind


@pytest.mark.zig
class TestZigLanguageServer:
    """Test Zig language server symbol finding and navigation capabilities."""

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
    def test_find_references_within_file(self, language_server: SolidLanguageServer) -> None:
        """Test finding references within the same file."""
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
        
        # Find references to Calculator within the same file
        sel_range = calculator_symbol.get("selectionRange", calculator_symbol.get("range"))
        assert sel_range is not None, "Calculator symbol has no range information"
        
        sel_start = sel_range["start"]
        refs = language_server.request_references(file_path, sel_start["line"], sel_start["character"])
        
        assert refs is not None
        assert isinstance(refs, list)
        # ZLS finds references within the same file (including declaration with includeDeclaration=True)
        assert len(refs) >= 5, f"Should find Calculator references within calculator.zig, found {len(refs)}"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_cross_file_references_with_open_files(self, language_server: SolidLanguageServer) -> None:
        """Test finding cross-file references (requires files to be open in ZLS)."""
        import time
        
        # ZLS only searches for references in open files (performance optimization)
        # So we need to open the files that contain references
        
        # Open build.zig first to trigger project analysis
        with language_server.open_file("build.zig"):
            # Open the source files we want to search
            with language_server.open_file(os.path.join("src", "main.zig")):
                with language_server.open_file(os.path.join("src", "calculator.zig")):
                    # Give ZLS a moment to analyze the open files
                    time.sleep(1)
                    
                    # Now find references to Calculator
                    symbols = language_server.request_document_symbols(os.path.join("src", "calculator.zig"))
                    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
                    
                    calculator_symbol = None
                    for sym in symbol_list:
                        if sym.get("name") == "Calculator":
                            calculator_symbol = sym
                            break
                    
                    assert calculator_symbol is not None, "Calculator struct not found"
                    
                    sel_range = calculator_symbol.get("selectionRange", calculator_symbol.get("range"))
                    assert sel_range is not None, "Calculator symbol has no range information"
                    
                    sel_start = sel_range["start"]
                    refs = language_server.request_references(
                        os.path.join("src", "calculator.zig"), 
                        sel_start["line"], 
                        sel_start["character"]
                    )
                    
                    assert refs is not None
                    assert isinstance(refs, list)
                    
                    # With files open, ZLS should find cross-file references
                    main_refs = [ref for ref in refs if "main.zig" in ref.get("uri", "")]
                    assert len(main_refs) > 0, "Should find Calculator references in main.zig when files are open"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_go_to_definition_cross_file(self, language_server: SolidLanguageServer) -> None:
        """Test go-to-definition from main.zig to calculator.zig (works without opening files)."""
        file_path = os.path.join("src", "main.zig")
        
        # Line 8: const calc = calculator.Calculator.init();
        # Test go-to-definition for Calculator
        definitions = language_server.request_definition(file_path, 7, 25)  # Position of "Calculator"
        
        assert definitions is not None
        assert isinstance(definitions, list)
        assert len(definitions) > 0, "Should find definition of Calculator"
        
        # Should point to calculator.zig
        calc_def = definitions[0]
        assert "calculator.zig" in calc_def.get("uri", ""), "Definition should be in calculator.zig"

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
        """Test that full symbol tree is not empty."""
        symbols = language_server.request_full_symbol_tree()
        
        assert symbols is not None
        assert len(symbols) > 0, "Symbol tree should not be empty"
        
        # The tree should have at least one root node
        root = symbols[0]
        assert isinstance(root, dict), "Root should be a dict"
        assert "name" in root, "Root should have a name"
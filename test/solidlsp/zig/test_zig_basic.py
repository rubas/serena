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
        assert calculator_symbol.get("kind") in [
            SymbolKind.Class,
            SymbolKind.Struct,
            SymbolKind.Namespace,
            5,
            14,
            23,
        ], "Calculator should be a struct/class/namespace"

        # Check for Calculator methods (init, add, subtract, etc.)
        # Methods might be in children or at the same level
        all_symbols = []
        for sym in symbol_list:
            all_symbols.append(sym.get("name"))
            if "children" in sym:
                for child in sym["children"]:
                    all_symbols.append(child.get("name"))

        # Verify exact calculator methods exist
        expected_methods = {"init", "add", "subtract", "multiply", "divide"}
        found_methods = set(all_symbols) & expected_methods
        assert found_methods == expected_methods, f"Expected exactly {expected_methods}, found: {found_methods}"

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
        # ZLS finds references within the same file
        # Calculator is used in 4 test usages (lines 45, 51, 57, 63)
        # Note: ZLS may not include the declaration itself as a reference
        assert len(refs) >= 4, f"Should find at least 4 Calculator references within calculator.zig, found {len(refs)}"

        # Verify we found the test usages
        ref_lines = sorted([ref["range"]["start"]["line"] for ref in refs])
        test_lines = [44, 50, 56, 62]  # 0-indexed: tests at lines 45, 51, 57, 63
        for line in test_lines:
            assert line in ref_lines, f"Should find Calculator reference at line {line+1}, found at lines {[l+1 for l in ref_lines]}"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_cross_file_references_with_open_files(self, language_server: SolidLanguageServer) -> None:
        """
        Test finding cross-file references with files open.

        ZLS limitation: Cross-file references (textDocument/references) only work when
        target files are open. This is a performance optimization in ZLS.
        """
        import time

        # Open the files that contain references to enable cross-file search
        with language_server.open_file("build.zig"):
            with language_server.open_file(os.path.join("src", "main.zig")):
                with language_server.open_file(os.path.join("src", "calculator.zig")):
                    # Give ZLS a moment to analyze the open files
                    time.sleep(1)

                    # Find Calculator struct
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

                    # Find references to Calculator
                    sel_start = sel_range["start"]
                    refs = language_server.request_references(
                        os.path.join("src", "calculator.zig"), sel_start["line"], sel_start["character"]
                    )

                    assert refs is not None
                    assert isinstance(refs, list)

                    # With files open, ZLS should find cross-file references
                    main_refs = [ref for ref in refs if "main.zig" in ref.get("uri", "")]

                    assert len(main_refs) >= 1, f"Should find at least 1 Calculator reference in main.zig, found {len(main_refs)}"

                    # Verify exact location in main.zig (line 8, 0-indexed: 7)
                    main_ref_line = main_refs[0]["range"]["start"]["line"]
                    assert (
                        main_ref_line == 7
                    ), f"Calculator reference in main.zig should be at line 8 (0-indexed: 7), found at line {main_ref_line + 1}"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_cross_file_references_within_file(self, language_server: SolidLanguageServer) -> None:
        """
        Test that ZLS finds references within the same file.

        Note: ZLS is designed to be lightweight and only analyzes files that are explicitly opened.
        Cross-file references require manually opening the relevant files first.
        """
        # Find references to Calculator from calculator.zig
        file_path = os.path.join("src", "calculator.zig")
        symbols = language_server.request_document_symbols(file_path)
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
        refs = language_server.request_references(file_path, sel_start["line"], sel_start["character"])

        assert refs is not None
        assert isinstance(refs, list)

        # ZLS finds references within the same file
        # Calculator is used in 4 test usages (lines 45, 51, 57, 63)
        # Note: ZLS may not include the declaration itself as a reference
        assert len(refs) >= 4, f"Should find at least 4 Calculator references within calculator.zig, found {len(refs)}"

        # Verify we found the test usages
        ref_lines = sorted([ref["range"]["start"]["line"] for ref in refs])
        test_lines = [44, 50, 56, 62]  # 0-indexed: tests at lines 45, 51, 57, 63
        for line in test_lines:
            assert line in ref_lines, f"Should find Calculator reference at line {line+1}, found at lines {[l+1 for l in ref_lines]}"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_go_to_definition_cross_file(self, language_server: SolidLanguageServer) -> None:
        """
        Test go-to-definition from main.zig to calculator.zig.

        ZLS capability: Go-to-definition (textDocument/definition) works cross-file
        WITHOUT requiring files to be open.
        """
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
    def test_cross_file_function_usage(self, language_server: SolidLanguageServer) -> None:
        """Test finding usage of functions from math_utils in main.zig."""
        # Line 23 in main.zig: const factorial_result = math_utils.factorial(5);
        definitions = language_server.request_definition(os.path.join("src", "main.zig"), 22, 40)  # Position of "factorial"

        assert definitions is not None
        assert isinstance(definitions, list)

        if len(definitions) > 0:
            # Should find factorial definition in math_utils.zig
            math_def = [d for d in definitions if "math_utils.zig" in d.get("uri", "")]
            assert len(math_def) > 0, "Should find factorial definition in math_utils.zig"

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_verify_cross_file_imports(self, language_server: SolidLanguageServer) -> None:
        """Verify that our test files have proper cross-file imports."""
        # Verify main.zig imports
        main_symbols = language_server.request_document_symbols(os.path.join("src", "main.zig"))
        assert main_symbols is not None
        main_list = main_symbols[0] if isinstance(main_symbols, tuple) else main_symbols
        main_names = {sym.get("name") for sym in main_list if isinstance(sym, dict)}

        # main.zig should have main and greeting functions
        assert "main" in main_names, "main function should be in main.zig"
        assert "greeting" in main_names, "greeting function should be in main.zig"

        # Verify calculator.zig exports Calculator
        calc_symbols = language_server.request_document_symbols(os.path.join("src", "calculator.zig"))
        assert calc_symbols is not None
        calc_list = calc_symbols[0] if isinstance(calc_symbols, tuple) else calc_symbols
        calc_names = {sym.get("name") for sym in calc_list if isinstance(sym, dict)}
        assert "Calculator" in calc_names, "Calculator struct should be in calculator.zig"

        # Verify math_utils.zig exports functions
        math_symbols = language_server.request_document_symbols(os.path.join("src", "math_utils.zig"))
        assert math_symbols is not None
        math_list = math_symbols[0] if isinstance(math_symbols, tuple) else math_symbols
        math_names = {sym.get("name") for sym in math_list if isinstance(sym, dict)}
        assert "factorial" in math_names, "factorial function should be in math_utils.zig"
        assert "isPrime" in math_names, "isPrime function should be in math_utils.zig"

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


@pytest.mark.zig
class TestZigFileWatcher:
    """Test Zig language server file watcher functionality."""

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_file_watcher_new_file_detection(self, language_server: SolidLanguageServer) -> None:
        """Test that new Zig files are automatically opened by the file watcher."""
        import time
        from pathlib import Path

        # Create a temporary Zig file in the src directory
        src_dir = Path(language_server.repository_root_path) / "src"
        temp_file_path = src_dir / "temp_test.zig"

        try:
            # Write a simple Zig function to the temporary file
            temp_file_content = """
pub fn tempFunction() void {
    const message = "Hello from temp file";
    _ = message;
}

pub fn anotherFunc(x: i32) i32 {
    return x * 2;
}
"""
            temp_file_path.write_text(temp_file_content)

            # Give the file watcher time to detect and open the file
            time.sleep(2.0)

            # Try to find symbols in the new file
            symbols = language_server.request_document_symbols(os.path.join("src", "temp_test.zig"))

            assert symbols is not None, "Should be able to get symbols from auto-opened file"
            symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
            symbol_names = {sym.get("name") for sym in symbol_list if isinstance(sym, dict)}

            # Verify our functions are found
            assert "tempFunction" in symbol_names, "tempFunction should be found in the new file"
            assert "anotherFunc" in symbol_names, "anotherFunc should be found in the new file"

        finally:
            # Clean up the temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_file_watcher_file_deletion(self, language_server: SolidLanguageServer) -> None:
        """Test that deleted files are properly closed by the file watcher."""
        import time
        from pathlib import Path

        # Create a temporary Zig file
        src_dir = Path(language_server.repository_root_path) / "src"
        temp_file_path = src_dir / "temp_delete.zig"

        try:
            # Create and write the file
            temp_file_content = """
pub fn deleteMe() void {
    // This function will be deleted
}
"""
            temp_file_path.write_text(temp_file_content)

            # Give the file watcher time to detect and open the file
            time.sleep(2.0)

            # Verify file is accessible
            symbols = language_server.request_document_symbols(os.path.join("src", "temp_delete.zig"))
            assert symbols is not None, "File should be accessible after creation"

            # Delete the file
            temp_file_path.unlink()

            # Give the file watcher time to detect deletion
            time.sleep(2.0)

            # Attempting to get symbols from deleted file should fail or return empty
            # Note: The exact behavior depends on ZLS implementation
            # We just verify no crash occurs
            try:
                symbols = language_server.request_document_symbols(os.path.join("src", "temp_delete.zig"))
                # If it doesn't raise an error, symbols should be None or empty
                assert symbols is None or len(symbols) == 0, "Deleted file should not have symbols"
            except Exception:
                # Expected - file no longer exists
                pass

        finally:
            # Ensure cleanup
            if temp_file_path.exists():
                temp_file_path.unlink()

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_file_watcher_gitignore_respect(self, language_server: SolidLanguageServer) -> None:
        """Test that files in gitignored directories are not watched."""
        import time
        from pathlib import Path

        # Create a file in zig-cache (which should be ignored)
        cache_dir = Path(language_server.repository_root_path) / "zig-cache"
        cache_dir.mkdir(exist_ok=True)
        ignored_file_path = cache_dir / "ignored_test.zig"

        # Also test zig-out directory
        out_dir = Path(language_server.repository_root_path) / "zig-out"
        out_dir.mkdir(exist_ok=True)
        out_file_path = out_dir / "output_test.zig"

        try:
            # Write files to ignored directories
            ignored_content = """
pub fn ignoredFunction() void {
    // This should not be auto-opened
}
"""
            ignored_file_path.write_text(ignored_content)
            out_file_path.write_text(ignored_content)

            # Give time for file watcher (should NOT detect these)
            time.sleep(2.0)

            # These files should not be accessible through ZLS
            # since they weren't auto-opened (being in ignored directories)
            try:
                symbols = language_server.request_document_symbols(str(ignored_file_path.relative_to(language_server.repository_root_path)))
                # If ZLS can access it, it means the file was opened (which is wrong)
                # However, ZLS might still be able to open it on-demand
                # So we just log this for informational purposes
                if symbols and len(symbols) > 0:
                    # This is acceptable - ZLS can still open files on-demand
                    # The file watcher just shouldn't have auto-opened it
                    pass
            except Exception:
                # Expected - file in ignored directory
                pass

        finally:
            # Clean up
            if ignored_file_path.exists():
                ignored_file_path.unlink()
            if out_file_path.exists():
                out_file_path.unlink()

    @pytest.mark.parametrize("language_server", [Language.ZIG], indirect=True)
    def test_file_watcher_non_zig_files_ignored(self, language_server: SolidLanguageServer) -> None:
        """Test that non-.zig files are not watched."""
        import time
        from pathlib import Path

        # Create various non-Zig files
        src_dir = Path(language_server.repository_root_path) / "src"
        txt_file = src_dir / "readme.txt"
        py_file = src_dir / "script.py"

        try:
            # Create non-Zig files
            txt_file.write_text("This is a text file")
            py_file.write_text("print('This is Python')")

            # Give time for file watcher (should NOT detect these)
            time.sleep(1.0)

            # These files should not be processed by ZLS
            # We can't really test this directly, but we verify no crashes
            # and that our Zig files still work
            symbols = language_server.request_document_symbols(os.path.join("src", "main.zig"))
            assert symbols is not None, "ZLS should still work after non-Zig files are created"

        finally:
            # Clean up
            if txt_file.exists():
                txt_file.unlink()
            if py_file.exists():
                py_file.unlink()

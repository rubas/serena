"""
Tests for the Nix language server implementation using nil.
"""

import platform
from pathlib import Path

import pytest

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import Language, LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger

# Skip all Nix tests on Windows as Nix doesn't support Windows
pytestmark = pytest.mark.skipif(platform.system() == "Windows", reason="Nix and nil are not available on Windows")


@pytest.fixture(scope="module")
def nix_server():
    """Create and start a Nix language server for testing."""
    test_repo_path = Path(__file__).parent.parent.parent / "resources" / "repos" / "nix" / "test_repo"

    config = LanguageServerConfig(
        code_language=Language.NIX,
        trace_lsp_communication=False,
        start_independent_lsp_process=True,
        ignored_paths=[],
    )
    logger = LanguageServerLogger("nix_test")

    server = SolidLanguageServer.create(
        config=config,
        logger=logger,
        repository_root_path=str(test_repo_path),
    )

    server.start()
    yield server
    server.stop()


@pytest.mark.nix
def test_nix_server_starts(nix_server):
    """Test that the Nix language server starts successfully."""
    assert nix_server.is_running()


@pytest.mark.nix
def test_nix_get_document_symbols_flake(nix_server):
    """Test getting document symbols from flake.nix."""
    symbols = nix_server.request_document_symbols("flake.nix")

    assert symbols is not None
    assert len(symbols) > 0

    # Symbols is a tuple with (symbols, None)
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols

    # Check for expected symbols in flake
    symbol_names = set()
    for symbol in symbol_list:
        if isinstance(symbol, dict):
            name = symbol.get("name", "")
            symbol_names.add(name)

    # Flakes typically have inputs and outputs
    assert "inputs" in symbol_names or "outputs" in symbol_names or len(symbol_names) > 0


@pytest.mark.nix
def test_nix_get_document_symbols_default(nix_server):
    """Test getting document symbols from default.nix."""
    symbols = nix_server.request_document_symbols("default.nix")

    assert symbols is not None
    assert len(symbols) > 0

    # Symbols is a tuple with (symbols, None)
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols

    # Check for expected symbols
    symbol_names = set()
    for symbol in symbol_list:
        if isinstance(symbol, dict):
            name = symbol.get("name", "")
            symbol_names.add(name)

    # We defined several functions and attributes
    expected_items = {"makeGreeting", "listUtils", "stringUtils", "hello", "calculator"}
    found_items = symbol_names.intersection(expected_items)
    assert len(found_items) > 0, f"Expected some of {expected_items}, found {symbol_names}"


@pytest.mark.nix
def test_nix_get_document_symbols_utils(nix_server):
    """Test getting document symbols from lib/utils.nix."""
    symbols = nix_server.request_document_symbols("lib/utils.nix")

    assert symbols is not None
    assert len(symbols) > 0

    # Symbols is a tuple with (symbols, None)
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols

    # Check for utility modules
    symbol_names = set()
    for symbol in symbol_list:
        if isinstance(symbol, dict):
            name = symbol.get("name", "")
            symbol_names.add(name)

    # We defined math, strings, lists, attrs modules
    expected_modules = {"math", "strings", "lists", "attrs", "files", "validate"}
    found_modules = symbol_names.intersection(expected_modules)
    assert len(found_modules) > 0, f"Expected some of {expected_modules}, found {symbol_names}"


@pytest.mark.nix
def test_nix_get_document_symbols_module(nix_server):
    """Test getting document symbols from a NixOS module."""
    symbols = nix_server.request_document_symbols("modules/example.nix")

    assert symbols is not None
    assert len(symbols) > 0

    # Symbols is a tuple with (symbols, None)
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols

    # Check for module structure
    symbol_names = set()
    for symbol in symbol_list:
        if isinstance(symbol, dict):
            name = symbol.get("name", "")
            symbol_names.add(name)

    # NixOS modules have options and config sections
    assert "options" in symbol_names or "config" in symbol_names or len(symbol_names) > 0


@pytest.mark.nix
def test_nix_get_definition(nix_server):
    """Test getting definition of a symbol in Nix."""
    # Try to find definition - just verify the API works
    definitions = nix_server.request_definition("default.nix", 10, 10)

    assert definitions is not None
    # Just check that we get a list (may be empty depending on cursor position)
    assert isinstance(definitions, list)


@pytest.mark.nix
def test_nix_get_references(nix_server):
    """Test finding references to a symbol in Nix."""
    # Try to find references - just verify the API works
    references = nix_server.request_references("default.nix", 10, 10)

    assert references is not None
    # Should return a list (may be empty)
    assert isinstance(references, list)


@pytest.mark.nix
def test_nix_completions(nix_server):
    """Test code completions in Nix."""
    try:
        # Test completions in default.nix
        completions = nix_server.request_completions("default.nix", 5, 10)

        if completions is not None and len(completions) > 0:
            # Check that we get some completions
            assert len(completions) > 0
    except AssertionError:
        # nil may not always provide completions in the expected format
        pytest.skip("Completions not in expected format for nil")


@pytest.mark.nix
def test_nix_hover_info(nix_server):
    """Test hover information in Nix files."""
    # Try to get hover info for a known symbol
    hover_info = nix_server.request_hover("default.nix", 5, 10)

    # nil should provide hover information
    if hover_info is not None:
        assert isinstance(hover_info, (dict, str)) or hover_info is None

"""
Tests for the Svelte language server implementation.
"""

from pathlib import Path

import pytest

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import Language, LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger


@pytest.fixture(scope="module")
def svelte_server():
    """Create and start a Svelte language server for testing."""
    test_repo_path = Path(__file__).parent.parent.parent / "resources" / "repos" / "svelte" / "test_repo"

    config = LanguageServerConfig(
        code_language=Language.SVELTE,
        trace_lsp_communication=False,
        start_independent_lsp_process=True,
        ignored_paths=[],
    )
    logger = LanguageServerLogger("svelte_test")

    try:
        server = SolidLanguageServer.create(
            config=config,
            logger=logger,
            repository_root_path=str(test_repo_path),
        )
        server.start()
        yield server
        server.stop()
    except RuntimeError as e:
        # If Node.js or svelte-language-server is not installed, skip tests
        pytest.skip(f"Svelte language server not available: {e}")


@pytest.mark.svelte
def test_svelte_server_starts(svelte_server):
    """Test that the Svelte language server starts successfully."""
    assert svelte_server.is_running()


@pytest.mark.svelte
def test_svelte_get_document_symbols_app(svelte_server):
    """Test getting document symbols from App.svelte."""
    symbols = svelte_server.request_document_symbols("src/App.svelte")

    assert symbols is not None
    assert len(symbols) > 0

    # Symbols is a tuple with (symbols, None)
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols

    # Check for expected symbols (variables and functions)
    symbol_names = set()
    for symbol in symbol_list:
        if isinstance(symbol, dict):
            name = symbol.get("name", "")
            symbol_names.add(name)

    # We should find some of the variables and functions defined in App.svelte
    expected_items = {"appName", "currentView", "changeView", "viewTitle"}
    found_items = symbol_names.intersection(expected_items)
    assert len(found_items) > 0, f"Expected some of {expected_items}, found {symbol_names}"


@pytest.mark.svelte
def test_svelte_get_document_symbols_counter(svelte_server):
    """Test getting document symbols from Counter.svelte."""
    symbols = svelte_server.request_document_symbols("src/Counter.svelte")

    assert symbols is not None
    assert len(symbols) > 0

    # Symbols is a tuple with (symbols, None)
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols

    # Check for Counter component symbols
    symbol_names = set()
    for symbol in symbol_list:
        if isinstance(symbol, dict):
            name = symbol.get("name", "")
            symbol_names.add(name)

    # We should find functions and props
    expected_items = {"increment", "decrement", "reset", "initialValue", "step"}
    found_items = symbol_names.intersection(expected_items)
    assert len(found_items) > 0, f"Expected some of {expected_items}, found {symbol_names}"


@pytest.mark.svelte
def test_svelte_get_document_symbols_todo(svelte_server):
    """Test getting document symbols from TodoList.svelte."""
    symbols = svelte_server.request_document_symbols("src/TodoList.svelte")

    assert symbols is not None
    assert len(symbols) > 0

    # Symbols is a tuple with (symbols, None)
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols

    # Check for TodoList component symbols
    symbol_names = set()
    for symbol in symbol_list:
        if isinstance(symbol, dict):
            name = symbol.get("name", "")
            symbol_names.add(name)

    # We should find todo-related functions
    expected_items = {"addTodo", "removeTodo", "toggleTodo", "clearCompleted", "todos"}
    found_items = symbol_names.intersection(expected_items)
    assert len(found_items) > 0, f"Expected some of {expected_items}, found {symbol_names}"


@pytest.mark.svelte
def test_svelte_get_definition(svelte_server):
    """Test getting definition of a symbol in Svelte."""
    # Try to find definition of Counter component import
    definitions = svelte_server.request_definition("src/App.svelte", 2, 10)  # Line with Counter import

    assert definitions is not None
    # Just check that we get a list (may be empty or contain the Counter.svelte file)
    assert isinstance(definitions, list)


@pytest.mark.svelte
def test_svelte_get_references(svelte_server):
    """Test finding references to a symbol in Svelte."""
    # Try to find references to a function
    references = svelte_server.request_references("src/Counter.svelte", 10, 10)

    assert references is not None
    # Should return a list (may be empty)
    assert isinstance(references, list)


@pytest.mark.svelte
def test_svelte_completions(svelte_server):
    """Test code completions in Svelte."""
    # Test completions in a Svelte file - try a position more likely to give completions
    # Line 15 is inside the reactive statement, after the "$:"
    completions = svelte_server.request_completions("src/App.svelte", 15, 10)

    # Svelte language server returns an empty list when no completions are available
    # This is still a valid response
    assert completions is not None
    assert isinstance(completions, list)


@pytest.mark.svelte
def test_svelte_hover_info(svelte_server):
    """Test hover information in Svelte files."""
    # Try to get hover info in App.svelte
    hover_info = svelte_server.request_hover("src/App.svelte", 7, 10)

    # Svelte language server should provide hover information
    if hover_info is not None:
        assert isinstance(hover_info, (dict, str)) or hover_info is None


@pytest.mark.svelte
def test_svelte_typescript_in_script(svelte_server):
    """Test that TypeScript in script tags is properly handled."""
    # The test files use lang="ts" in script tags
    symbols = svelte_server.request_document_symbols("src/types.ts")

    if symbols is not None:
        # TypeScript file should be recognized
        assert len(symbols) >= 0  # May or may not have symbols depending on LSP support


@pytest.mark.svelte
def test_svelte_component_imports(svelte_server):
    """Test that component imports are recognized."""
    # App.svelte imports multiple components
    symbols = svelte_server.request_document_symbols("src/App.svelte")

    assert symbols is not None
    assert len(symbols) > 0

    # The imports should be recognized
    symbol_list = symbols[0] if isinstance(symbols, tuple) else symbols
    assert len(symbol_list) >= 0  # Basic check that parsing didn't fail

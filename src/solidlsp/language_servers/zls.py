"""
Provides Zig specific instantiation of the LanguageServer class using ZLS (Zig Language Server).
"""

import logging
import os
import pathlib
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional

from overrides import override
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from serena.util.file_system import GitignoreParser
from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings


class ZigFileWatcher(FileSystemEventHandler):
    """
    File system event handler for watching Zig files.

    Monitors for new, modified, and deleted .zig files and sends
    appropriate LSP notifications to keep ZLS in sync.
    """

    def __init__(self, language_server: "ZigLanguageServer", gitignore_parser: Optional[GitignoreParser] = None):
        """
        Initialize the Zig file watcher.

        :param language_server: The ZigLanguageServer instance to notify
        :param gitignore_parser: Optional GitignoreParser to respect gitignore patterns
        """
        self.language_server = language_server
        self.gitignore_parser = gitignore_parser
        self.logger = language_server.logger

    def _should_process_file(self, file_path: str) -> bool:
        """Check if a file should be processed based on extension and gitignore."""
        # Only process .zig files
        if not file_path.endswith(".zig"):
            return False

        # Check gitignore if parser is available
        if self.gitignore_parser:
            try:
                relative_path = Path(file_path).relative_to(self.language_server.repository_root_path)
                if self.gitignore_parser.is_ignored(str(relative_path)):
                    self.logger.log(f"Ignoring gitignored file: {relative_path}", logging.DEBUG)
                    return False
            except Exception as e:
                self.logger.log(f"Error checking gitignore for {file_path}: {e}", logging.WARNING)

        # Check if file is in an ignored directory
        path_parts = Path(file_path).parts
        for part in path_parts:
            if self.language_server.is_ignored_dirname(part):
                return False

        return True

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        if not self._should_process_file(event.src_path):
            return

        self.logger.log(f"New Zig file detected: {event.src_path}", logging.INFO)

        try:
            # Read the new file content
            with open(event.src_path, encoding="utf-8") as f:
                content = f.read()

            # Create URI for the file
            file_uri = Path(event.src_path).as_uri()

            # Send didOpen notification to ZLS
            self.language_server.server.notify.did_open(
                {"textDocument": {"uri": file_uri, "languageId": "zig", "version": 0, "text": content}}
            )

            # Track the opened file
            self.language_server._workspace_files.append({"uri": file_uri, "path": event.src_path})

            self.logger.log(f"Opened new file in ZLS: {event.src_path}", logging.DEBUG)

        except Exception as e:
            self.logger.log(f"Failed to open new file {event.src_path}: {e}", logging.ERROR)

    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return

        if not event.src_path.endswith(".zig"):
            return

        self.logger.log(f"Zig file deleted: {event.src_path}", logging.INFO)

        try:
            file_uri = Path(event.src_path).as_uri()

            # Send didClose notification to ZLS
            self.language_server.server.notify.did_close({"textDocument": {"uri": file_uri}})

            # Remove from tracked files
            self.language_server._workspace_files = [f for f in self.language_server._workspace_files if f["uri"] != file_uri]

            self.logger.log(f"Closed deleted file in ZLS: {event.src_path}", logging.DEBUG)

        except Exception as e:
            self.logger.log(f"Failed to close deleted file {event.src_path}: {e}", logging.ERROR)

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        if not self._should_process_file(event.src_path):
            return

        # For modifications, ZLS typically handles them through didChange notifications
        # But since we're not tracking file contents, we'll skip this for now
        # The IDE/editor should handle modifications through normal LSP flow
        self.logger.log(f"Zig file modified: {event.src_path} (handled by IDE)", logging.DEBUG)


class ZigLanguageServer(SolidLanguageServer):
    """
    Provides Zig specific instantiation of the LanguageServer class using ZLS.
    """

    @override
    def is_ignored_dirname(self, dirname: str) -> bool:
        # For Zig projects, we should ignore:
        # - zig-cache: build cache directory
        # - zig-out: default build output directory
        # - .zig-cache: alternative cache location
        # - node_modules: if the project has JavaScript components
        return super().is_ignored_dirname(dirname) or dirname in ["zig-cache", "zig-out", ".zig-cache", "node_modules", "build", "dist"]

    @staticmethod
    def _get_zig_version():
        """Get the installed Zig version or None if not found."""
        try:
            result = subprocess.run(["zig", "version"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            return None
        return None

    @staticmethod
    def _get_zls_version():
        """Get the installed ZLS version or None if not found."""
        try:
            result = subprocess.run(["zls", "--version"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            return None
        return None

    @staticmethod
    def _check_zls_installed():
        """Check if ZLS is installed in the system."""
        return shutil.which("zls") is not None

    @staticmethod
    def _setup_runtime_dependency():
        """
        Check if required Zig runtime dependencies are available.
        Raises RuntimeError with helpful message if dependencies are missing.
        """
        zig_version = ZigLanguageServer._get_zig_version()
        if not zig_version:
            raise RuntimeError(
                "Zig is not installed. Please install Zig from https://ziglang.org/download/ and make sure it is added to your PATH."
            )

        if not ZigLanguageServer._check_zls_installed():
            zls_version = ZigLanguageServer._get_zls_version()
            if not zls_version:
                raise RuntimeError(
                    "Found Zig but ZLS (Zig Language Server) is not installed.\n"
                    "Please install ZLS from https://github.com/zigtools/zls\n"
                    "You can install it via:\n"
                    "  - Package managers (brew install zls, scoop install zls, etc.)\n"
                    "  - Download pre-built binaries from GitHub releases\n"
                    "  - Build from source with: zig build -Doptimize=ReleaseSafe\n\n"
                    "After installation, make sure 'zls' is added to your PATH."
                )

        return True

    def __init__(
        self, config: LanguageServerConfig, logger: LanguageServerLogger, repository_root_path: str, solidlsp_settings: SolidLSPSettings
    ):
        self._setup_runtime_dependency()

        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd="zls", cwd=repository_root_path),
            "zig",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()
        self.request_id = 0
        # Store opened workspace files to keep them open
        self._workspace_files = []
        # Configuration for auto-opening workspace files (default: enabled)
        self.auto_open_workspace = True  # Enable by default for better cross-file support
        # File watcher for monitoring new/deleted Zig files
        self._file_observer: Optional[Observer] = None
        self._file_watcher: Optional[ZigFileWatcher] = None

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for the Zig Language Server.
        """
        root_uri = pathlib.Path(repository_absolute_path).as_uri()
        initialize_params = {
            "locale": "en",
            "capabilities": {
                "textDocument": {
                    "synchronization": {"didSave": True, "dynamicRegistration": True},
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True},
                    "documentSymbol": {
                        "dynamicRegistration": True,
                        "hierarchicalDocumentSymbolSupport": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                    },
                    "completion": {
                        "dynamicRegistration": True,
                        "completionItem": {
                            "snippetSupport": True,
                            "commitCharactersSupport": True,
                            "documentationFormat": ["markdown", "plaintext"],
                            "deprecatedSupport": True,
                            "preselectSupport": True,
                        },
                    },
                    "hover": {
                        "dynamicRegistration": True,
                        "contentFormat": ["markdown", "plaintext"],
                    },
                },
                "workspace": {
                    "workspaceFolders": True,
                    "didChangeConfiguration": {"dynamicRegistration": True},
                    "configuration": True,
                },
            },
            "processId": os.getpid(),
            "rootPath": repository_absolute_path,
            "rootUri": root_uri,
            "workspaceFolders": [
                {
                    "uri": root_uri,
                    "name": os.path.basename(repository_absolute_path),
                }
            ],
            "initializationOptions": {
                # ZLS specific options based on schema.json
                # Critical paths for ZLS to understand the project
                "zig_exe_path": shutil.which("zig"),  # Path to zig executable
                "zig_lib_path": None,  # Let ZLS auto-detect
                "build_runner_path": None,  # Let ZLS use its built-in runner
                "global_cache_path": None,  # Let ZLS use default cache
                # Build configuration
                "enable_build_on_save": True,  # Enable to analyze project structure
                "build_on_save_args": ["build"],
                # Features
                "enable_snippets": True,
                "enable_argument_placeholders": True,
                "semantic_tokens": "full",
                "warn_style": False,
                "highlight_global_var_declarations": False,
                "skip_std_references": False,
                "prefer_ast_check_as_child_process": True,
                "completion_label_details": True,
                # Inlay hints configuration
                "inlay_hints_show_variable_type_hints": True,
                "inlay_hints_show_struct_literal_field_type": True,
                "inlay_hints_show_parameter_name": True,
                "inlay_hints_show_builtin": True,
                "inlay_hints_exclude_single_argument": True,
                "inlay_hints_hide_redundant_param_names": False,
                "inlay_hints_hide_redundant_param_names_last_token": False,
            },
        }
        return initialize_params

    def _start_server(self):
        """Start ZLS server process"""

        def register_capability_handler(params):
            return

        def window_log_message(msg):
            self.logger.log(f"LSP: window/logMessage: {msg}", logging.INFO)

        def do_nothing(params):
            return

        self.server.on_request("client/registerCapability", register_capability_handler)
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)

        self.logger.log("Starting ZLS server process", logging.INFO)
        self.server.start()
        initialize_params = self._get_initialize_params(self.repository_root_path)

        self.logger.log(
            "Sending initialize request from LSP client to LSP server and awaiting response",
            logging.INFO,
        )
        init_response = self.server.send.initialize(initialize_params)

        # Verify server capabilities
        assert "textDocumentSync" in init_response["capabilities"]
        assert "definitionProvider" in init_response["capabilities"]
        assert "documentSymbolProvider" in init_response["capabilities"]
        assert "referencesProvider" in init_response["capabilities"]

        self.server.notify.initialized({})
        self.completions_available.set()

        # Auto-open workspace files if enabled
        if self.auto_open_workspace:
            self._open_workspace_files()

        # Start file watcher for new/deleted files
        self._start_file_watcher()

        # ZLS server is typically ready immediately after initialization
        self.server_ready.set()
        self.server_ready.wait()

    def _open_workspace_files(self):
        """
        Open all Zig files in the workspace to enable full cross-file reference support.

        ZLS only finds references in files that are currently open. By opening all
        .zig files in the workspace during initialization, we enable complete
        cross-file reference functionality.
        """
        try:
            workspace_path = Path(self.repository_root_path)
            zig_files = []

            self.logger.log("Auto-opening workspace files for ZLS cross-file references", logging.INFO)

            # Find all .zig files in the workspace
            for zig_file in workspace_path.rglob("*.zig"):
                # Skip ignored directories
                relative_path = zig_file.relative_to(workspace_path)

                # Skip build cache and output directories
                skip_dirs = {"zig-cache", "zig-out", ".zig-cache", "node_modules", ".git"}
                if any(part in skip_dirs for part in relative_path.parts):
                    continue

                # Skip if any parent directory should be ignored
                if any(self.is_ignored_dirname(part) for part in relative_path.parts[:-1]):
                    continue

                # Store the relative path as string (will use platform-specific separators)
                zig_files.append(str(relative_path))

            self.logger.log(f"Found {len(zig_files)} Zig files to open", logging.INFO)

            # Open each file by sending didOpen notification to ZLS
            for file_path in zig_files:
                try:
                    full_path = os.path.join(self.repository_root_path, file_path)
                    # Normalize path for consistent handling
                    full_path = os.path.normpath(full_path)

                    # Read file content
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()

                    # Create URI for the file - ensure proper URI format on all platforms
                    file_uri = pathlib.Path(full_path).as_uri()

                    # Track this file as opened
                    self._workspace_files.append({"uri": file_uri, "path": file_path})

                    # Send didOpen notification to ZLS
                    self.server.notify.did_open({"textDocument": {"uri": file_uri, "languageId": "zig", "version": 0, "text": content}})

                    self.logger.log(f"Opened {file_path}", logging.DEBUG)

                except Exception as e:
                    self.logger.log(f"Failed to open {file_path}: {e}", logging.WARNING)

            # Give ZLS time to process the opened files
            if zig_files:
                import platform
                import time

                # Windows needs more time for ZLS to process opened files
                wait_time = 1.0 if platform.system() == "Windows" else 0.5
                time.sleep(wait_time)  # Let ZLS index the files
                self.logger.log(f"Successfully opened {len(self._workspace_files)} workspace files", logging.INFO)

        except Exception as e:
            self.logger.log(f"Error opening workspace files: {e}", logging.WARNING)

    def _start_file_watcher(self):
        """Start watching for new/deleted Zig files in the workspace."""
        try:
            # Initialize gitignore parser if configured
            gitignore_parser = None
            try:
                gitignore_parser = GitignoreParser(self.repository_root_path)
                self.logger.log(f"Initialized gitignore parser with {len(gitignore_parser.get_ignore_specs())} patterns", logging.DEBUG)
            except Exception as e:
                self.logger.log(f"Could not initialize gitignore parser: {e}", logging.WARNING)

            # Create file watcher
            self._file_watcher = ZigFileWatcher(self, gitignore_parser)

            # Create and start observer
            self._file_observer = Observer()
            self._file_observer.schedule(self._file_watcher, self.repository_root_path, recursive=True)
            self._file_observer.start()

            self.logger.log(f"Started file watcher for Zig files in {self.repository_root_path}", logging.INFO)

        except Exception as e:
            self.logger.log(f"Failed to start file watcher: {e}", logging.ERROR)
            self._file_observer = None
            self._file_watcher = None

    def _stop_file_watcher(self):
        """Stop the file watcher if it's running."""
        if self._file_observer and self._file_observer.is_alive():
            try:
                self._file_observer.stop()
                self._file_observer.join(timeout=2.0)
                self.logger.log("Stopped file watcher", logging.DEBUG)
            except Exception as e:
                self.logger.log(f"Error stopping file watcher: {e}", logging.WARNING)

        self._file_observer = None
        self._file_watcher = None

    @override
    def stop(self, shutdown_timeout: float = 2.0) -> None:
        """Stop the language server and clean up resources."""
        # Stop file watcher first
        self._stop_file_watcher()

        # Then call parent stop
        super().stop(shutdown_timeout)

    def __del__(self):
        """Clean up by closing workspace files and stopping file watcher."""
        # Stop file watcher
        self._stop_file_watcher()

        # Close auto-opened files
        if hasattr(self, "_workspace_files") and self._workspace_files:
            try:
                for file_info in self._workspace_files:
                    self.server.notify.did_close({"textDocument": {"uri": file_info["uri"]}})
            except:
                pass  # Ignore errors during cleanup

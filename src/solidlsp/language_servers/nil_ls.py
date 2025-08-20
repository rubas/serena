"""
Provides Nix specific instantiation of the LanguageServer class using nil (NIx Language server).
"""

import logging
import os
import pathlib
import platform
import shutil
import subprocess
import threading
from pathlib import Path

from overrides import override

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings


class NixLanguageServer(SolidLanguageServer):
    """
    Provides Nix specific instantiation of the LanguageServer class using nil.
    """

    @override
    def is_ignored_dirname(self, dirname: str) -> bool:
        # For Nix projects, we should ignore:
        # - result: nix build output symlinks
        # - result-*: multiple build outputs
        # - .direnv: direnv cache
        return super().is_ignored_dirname(dirname) or dirname in ["result", ".direnv"] or dirname.startswith("result-")

    @staticmethod
    def _get_nil_version():
        """Get the installed nil version or None if not found."""
        try:
            result = subprocess.run(["nil", "--version"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                # nil outputs version like: nil 2023-08-09
                return result.stdout.strip()
        except FileNotFoundError:
            return None
        return None

    @staticmethod
    def _check_nil_installed():
        """Check if nil is installed in the system."""
        return shutil.which("nil") is not None

    @staticmethod
    def _get_nil_path():
        """Get the path to nil executable."""
        # First check if it's in PATH
        nil_path = shutil.which("nil")
        if nil_path:
            return nil_path

        # Check common installation locations
        home = Path.home()
        possible_paths = [
            home / ".local" / "bin" / "nil",
            home / ".serena" / "language_servers" / "nil" / "nil",
            home / ".cargo" / "bin" / "nil",
            home / ".nix-profile" / "bin" / "nil",
            Path("/usr/local/bin/nil"),
            Path("/run/current-system/sw/bin/nil"),  # NixOS system profile
        ]

        # Add Windows-specific paths
        if platform.system() == "Windows":
            possible_paths.extend(
                [
                    home / "AppData" / "Local" / "nil" / "nil.exe",
                    home / ".serena" / "language_servers" / "nil" / "nil.exe",
                ]
            )

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    @staticmethod
    def _install_nil_with_cargo():
        """Install nil using cargo if available."""
        # Check if cargo is available
        if not shutil.which("cargo"):
            return None

        print("Installing nil using cargo... This may take a few minutes.")
        try:
            # Install nil to user's cargo bin directory
            result = subprocess.run(
                ["cargo", "install", "--git", "https://github.com/oxalica/nil", "nil"],
                capture_output=True,
                text=True,
                check=False,
                timeout=600,  # 10 minute timeout for building
            )

            if result.returncode == 0:
                # Check if nil is now in PATH
                nil_path = shutil.which("nil")
                if nil_path:
                    print(f"Successfully installed nil at: {nil_path}")
                    return nil_path

                # Check cargo bin directory
                home = Path.home()
                cargo_nil = home / ".cargo" / "bin" / "nil"
                if cargo_nil.exists():
                    print(f"Successfully installed nil at: {cargo_nil}")
                    return str(cargo_nil)
            else:
                print(f"Failed to install nil with cargo: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("Cargo install timed out after 10 minutes")
        except Exception as e:
            print(f"Error installing nil with cargo: {e}")

        return None

    @staticmethod
    def _setup_runtime_dependency():
        """
        Check if required Nix runtime dependencies are available.
        Attempts to install nil if not present.
        """
        nil_path = NixLanguageServer._get_nil_path()

        if not nil_path:
            print("nil not found. Attempting to install...")

            # Try to install with cargo if available
            nil_path = NixLanguageServer._install_nil_with_cargo()

            if not nil_path:
                raise RuntimeError(
                    "nil (Nix Language Server) is not installed.\n"
                    "Please install nil using one of the following methods:\n"
                    "  - Using Nix: nix profile install github:oxalica/nil\n"
                    "  - Using cargo: cargo install --git https://github.com/oxalica/nil nil\n"
                    "  - On macOS with Homebrew: brew install nil\n"
                    "  - From nixpkgs: nix-env -iA nixpkgs.nil\n\n"
                    "After installation, make sure 'nil' is in your PATH."
                )

        # Verify nil works
        try:
            result = subprocess.run([nil_path, "--version"], capture_output=True, text=True, check=False, timeout=5)
            if result.returncode != 0:
                raise RuntimeError(f"nil failed to run: {result.stderr}")
        except Exception as e:
            raise RuntimeError(f"Failed to verify nil installation: {e}")

        return nil_path

    def __init__(
        self, config: LanguageServerConfig, logger: LanguageServerLogger, repository_root_path: str, solidlsp_settings: SolidLSPSettings
    ):
        nil_path = self._setup_runtime_dependency()

        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd=nil_path, cwd=repository_root_path),
            "nix",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()
        self.request_id = 0

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for nil.
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
                    "signatureHelp": {
                        "dynamicRegistration": True,
                        "signatureInformation": {
                            "documentationFormat": ["markdown", "plaintext"],
                            "parameterInformation": {"labelOffsetSupport": True},
                        },
                    },
                    "codeAction": {
                        "dynamicRegistration": True,
                        "codeActionLiteralSupport": {
                            "codeActionKind": {
                                "valueSet": [
                                    "",
                                    "quickfix",
                                    "refactor",
                                    "refactor.extract",
                                    "refactor.inline",
                                    "refactor.rewrite",
                                    "source",
                                    "source.organizeImports",
                                ]
                            }
                        },
                    },
                    "rename": {"dynamicRegistration": True, "prepareSupport": True},
                },
                "workspace": {
                    "workspaceFolders": True,
                    "didChangeConfiguration": {"dynamicRegistration": True},
                    "configuration": True,
                    "symbol": {
                        "dynamicRegistration": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                    },
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
                # nil specific options
                "autoArchive": False,  # Don't automatically eval and build all packages
                "autoEvalInputs": True,  # Automatically eval flake inputs for better completion
            },
        }
        return initialize_params

    def _start_server(self):
        """Start nil server process"""

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

        self.logger.log("Starting nil server process", logging.INFO)
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

        # nil server is typically ready immediately after initialization
        self.server_ready.set()
        self.server_ready.wait()

"""
Provides Svelte specific instantiation of the LanguageServer class using svelte-language-server.
"""

import json
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


class SvelteLanguageServer(SolidLanguageServer):
    """
    Provides Svelte specific instantiation of the LanguageServer class using svelte-language-server.
    """

    @override
    def is_ignored_dirname(self, dirname: str) -> bool:
        # For Svelte projects, we should ignore:
        # - node_modules: npm dependencies
        # - .svelte-kit: SvelteKit build cache
        # - build: build output
        # - dist: distribution files
        return super().is_ignored_dirname(dirname) or dirname in [
            "node_modules",
            ".svelte-kit",
            "build",
            "dist",
            ".vercel",
            ".netlify",
            "coverage",
        ]

    @staticmethod
    def _check_node_installed():
        """Check if Node.js is installed."""
        node_cmd = shutil.which("node")
        if not node_cmd:
            node_cmd = shutil.which("nodejs")
        return node_cmd is not None

    @staticmethod
    def _check_npm_installed():
        """Check if npm is installed."""
        return shutil.which("npm") is not None

    @staticmethod
    def _get_node_version():
        """Get the installed Node.js version."""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        return None

    @staticmethod
    def _get_svelte_ls_path():
        """Get the path to svelte-language-server executable."""
        # First check if it's in PATH (globally installed)
        svelte_ls = shutil.which("svelteserver")
        if svelte_ls:
            return svelte_ls

        # Check common installation locations
        home = Path.home()
        possible_paths = [
            # Global npm install locations
            Path("/usr/local/lib/node_modules/svelte-language-server/bin/server.js"),
            Path("/usr/lib/node_modules/svelte-language-server/bin/server.js"),
            # User npm install locations
            home / ".npm-global" / "lib" / "node_modules" / "svelte-language-server" / "bin" / "server.js",
            # Local project installation
            Path.cwd() / "node_modules" / "svelte-language-server" / "bin" / "server.js",
            # Serena-specific installation
            home / ".serena" / "language_servers" / "svelte" / "node_modules" / "svelte-language-server" / "bin" / "server.js",
        ]

        # Add Windows-specific paths
        if platform.system() == "Windows":
            possible_paths.extend(
                [
                    home / "AppData" / "Roaming" / "npm" / "node_modules" / "svelte-language-server" / "bin" / "server.js",
                    Path("C:/Program Files/nodejs/node_modules/svelte-language-server/bin/server.js"),
                ]
            )

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    @staticmethod
    def _install_svelte_ls():
        """Install svelte-language-server using npm."""
        if not SvelteLanguageServer._check_npm_installed():
            raise RuntimeError(
                "npm is not installed. Please install Node.js and npm first.\n"
                "Visit https://nodejs.org/ to download and install Node.js (which includes npm)."
            )

        # Create installation directory
        install_dir = Path.home() / ".serena" / "language_servers" / "svelte"
        install_dir.mkdir(parents=True, exist_ok=True)

        print("Installing svelte-language-server using npm...")
        try:
            # Create package.json if it doesn't exist
            package_json = install_dir / "package.json"
            if not package_json.exists():
                package_data = {
                    "name": "svelte-language-server-install",
                    "version": "1.0.0",
                    "private": True,
                    "dependencies": {},
                }
                with open(package_json, "w") as f:
                    json.dump(package_data, f, indent=2)

            # Install svelte-language-server
            result = subprocess.run(
                ["npm", "install", "svelte-language-server"],
                cwd=str(install_dir),
                capture_output=True,
                text=True,
                check=False,
                timeout=120,  # 2 minute timeout
            )

            if result.returncode == 0:
                # Check if the installation was successful
                server_js = install_dir / "node_modules" / "svelte-language-server" / "bin" / "server.js"
                if server_js.exists():
                    print(f"Successfully installed svelte-language-server at: {server_js}")
                    return str(server_js)
                else:
                    print("Installation seemed successful but server.js not found")
            else:
                print(f"Failed to install svelte-language-server: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("npm install timed out after 2 minutes")
        except Exception as e:
            print(f"Error installing svelte-language-server: {e}")

        return None

    @staticmethod
    def _setup_runtime_dependency():
        """
        Check if required Svelte runtime dependencies are available.
        Installs svelte-language-server if not present.
        """
        # Check Node.js is installed
        if not SvelteLanguageServer._check_node_installed():
            raise RuntimeError(
                "Node.js is not installed. Please install Node.js first.\n"
                "Visit https://nodejs.org/ to download and install Node.js.\n"
                "Svelte language server requires Node.js 12 or later."
            )

        # Check Node.js version
        node_version = SvelteLanguageServer._get_node_version()
        if node_version:
            # Extract major version number
            try:
                major_version = int(node_version.strip("v").split(".")[0])
                if major_version < 12:
                    raise RuntimeError(
                        f"Node.js version {node_version} is too old.\n"
                        "Svelte language server requires Node.js 12 or later.\n"
                        "Please update Node.js from https://nodejs.org/"
                    )
            except (ValueError, IndexError):
                pass  # Couldn't parse version, continue anyway

        # Check if svelte-language-server is installed
        svelte_ls_path = SvelteLanguageServer._get_svelte_ls_path()

        if not svelte_ls_path:
            print("svelte-language-server not found. Installing...")
            svelte_ls_path = SvelteLanguageServer._install_svelte_ls()

            if not svelte_ls_path:
                raise RuntimeError(
                    "svelte-language-server is not installed.\n"
                    "Please install it using one of the following methods:\n"
                    "  - Global: npm install -g svelte-language-server\n"
                    "  - Local: npm install svelte-language-server\n\n"
                    "After installation, make sure the server is accessible."
                )

        return svelte_ls_path

    def __init__(
        self, config: LanguageServerConfig, logger: LanguageServerLogger, repository_root_path: str, solidlsp_settings: SolidLSPSettings
    ):
        svelte_ls_path = self._setup_runtime_dependency()

        # svelte-language-server is a Node.js script, so we need to run it with node
        if svelte_ls_path.endswith(".js"):
            node_cmd = shutil.which("node") or shutil.which("nodejs")
            if not node_cmd:
                raise RuntimeError("Node.js executable not found in PATH")
            # Properly quote paths on Windows to handle spaces
            if platform.system() == "Windows":
                cmd = f'"{node_cmd}" "{svelte_ls_path}"'
            else:
                cmd = f"{node_cmd} {svelte_ls_path}"
        else:
            # Quote the path on Windows if it contains spaces
            if platform.system() == "Windows" and " " in svelte_ls_path:
                cmd = f'"{svelte_ls_path}"'
            else:
                cmd = svelte_ls_path

        # Add --stdio flag for svelte-language-server
        cmd = f"{cmd} --stdio"

        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd=cmd, cwd=repository_root_path),
            "svelte",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()
        self.request_id = 0

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for the Svelte Language Server.
        """
        root_uri = pathlib.Path(repository_absolute_path).as_uri()
        initialize_params = {
            "locale": "en",
            "capabilities": {
                "textDocument": {
                    "synchronization": {"didSave": True, "dynamicRegistration": True},
                    "definition": {"dynamicRegistration": True, "linkSupport": True},
                    "references": {"dynamicRegistration": True},
                    "documentSymbol": {
                        "dynamicRegistration": True,
                        "hierarchicalDocumentSymbolSupport": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                        "tagSupport": {"valueSet": [1]},
                    },
                    "completion": {
                        "dynamicRegistration": True,
                        "completionItem": {
                            "snippetSupport": True,
                            "commitCharactersSupport": True,
                            "documentationFormat": ["markdown", "plaintext"],
                            "deprecatedSupport": True,
                            "preselectSupport": True,
                            "tagSupport": {"valueSet": [1]},
                            "insertReplaceSupport": True,
                            "resolveSupport": {"properties": ["documentation", "detail", "additionalTextEdits"]},
                        },
                        "contextSupport": True,
                        "completionItemKind": {"valueSet": list(range(1, 26))},
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
                            "activeParameterSupport": True,
                        },
                        "contextSupport": True,
                    },
                    "codeAction": {
                        "dynamicRegistration": True,
                        "isPreferredSupport": True,
                        "disabledSupport": True,
                        "dataSupport": True,
                        "resolveSupport": {"properties": ["edit"]},
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
                        "honorsChangeAnnotations": False,
                    },
                    "rename": {"dynamicRegistration": True, "prepareSupport": True},
                    "formatting": {"dynamicRegistration": True},
                    "rangeFormatting": {"dynamicRegistration": True},
                },
                "workspace": {
                    "workspaceFolders": True,
                    "didChangeConfiguration": {"dynamicRegistration": True},
                    "configuration": True,
                    "symbol": {
                        "dynamicRegistration": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                        "tagSupport": {"valueSet": [1]},
                    },
                    "semanticTokens": {"refreshSupport": True},
                    "fileOperations": {
                        "dynamicRegistration": True,
                        "didCreate": True,
                        "didRename": True,
                        "didDelete": True,
                        "willCreate": True,
                        "willRename": True,
                        "willDelete": True,
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
                # Svelte language server specific options
                "configuration": {
                    "svelte": {
                        "enable-ts-plugin": False,  # Don't enable TypeScript plugin for standalone use
                        "format": {
                            "enable": True,
                            "config": {
                                "printWidth": 80,
                                "singleQuote": False,
                                "svelteBracketNewLine": True,
                                "svelteSortOrder": "options-scripts-markup-styles",
                            },
                        },
                        "completions": {
                            "enable": True,
                        },
                        "hover": {
                            "enable": True,
                        },
                        "codeActions": {
                            "enable": True,
                        },
                    },
                    "typescript": {
                        "enable": True,
                        "diagnostics": {"enable": True},
                        "format": {"enable": True},
                        "completions": {"enable": True},
                        "definitions": {"enable": True},
                        "documentSymbols": {"enable": True},
                        "signatureHelp": {"enable": True},
                    },
                    "css": {
                        "enable": True,
                        "globals": "",
                        "completions": {"enable": True},
                        "documentColors": {"enable": True},
                        "documentSymbols": {"enable": True},
                        "selectionRange": {"enable": True},
                    },
                    "html": {
                        "enable": True,
                        "hover": {"enable": True},
                        "completions": {"enable": True, "emmet": True},
                        "tagComplete": {"enable": True},
                        "documentSymbols": {"enable": True},
                        "linkedEditing": {"enable": True},
                    },
                },
            },
        }
        return initialize_params

    def _start_server(self):
        """Start Svelte Language Server process"""

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

        self.logger.log("Starting Svelte Language Server process", logging.INFO)
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

        # Svelte Language Server is typically ready immediately after initialization
        self.server_ready.set()
        self.server_ready.wait()

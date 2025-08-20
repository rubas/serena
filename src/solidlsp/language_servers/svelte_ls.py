"""
Provides Svelte specific instantiation of the LanguageServer class using svelte-language-server.
"""

import logging
import os
import pathlib
import shutil
import threading

from overrides import override
from sensai.util.logging import LogTime

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.ls_utils import PlatformId, PlatformUtils
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings

from .common import RuntimeDependency, RuntimeDependencyCollection


class SvelteLanguageServer(SolidLanguageServer):
    """
    Provides Svelte specific instantiation of the LanguageServer class using svelte-language-server.
    """

    def __init__(
        self, config: LanguageServerConfig, logger: LanguageServerLogger, repository_root_path: str, solidlsp_settings: SolidLSPSettings
    ):
        """
        Creates a SvelteLanguageServer instance. This class is not meant to be instantiated directly. Use LanguageServer.create() instead.
        """
        svelte_lsp_executable_path = self._setup_runtime_dependencies(logger, config, solidlsp_settings)
        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd=svelte_lsp_executable_path, cwd=repository_root_path),
            "svelte",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()
        self.request_id = 0

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

    @classmethod
    def _setup_runtime_dependencies(
        cls, logger: LanguageServerLogger, config: LanguageServerConfig, solidlsp_settings: SolidLSPSettings
    ) -> list[str]:
        """
        Setup runtime dependencies for Svelte Language Server and return the command to start the server.
        """
        platform_id = PlatformUtils.get_platform_id()

        valid_platforms = [
            PlatformId.LINUX_x64,
            PlatformId.LINUX_arm64,
            PlatformId.OSX,
            PlatformId.OSX_x64,
            PlatformId.OSX_arm64,
            PlatformId.WIN_x64,
            PlatformId.WIN_arm64,
        ]
        assert platform_id in valid_platforms, f"Platform {platform_id} is not supported for Svelte language server at the moment"

        deps = RuntimeDependencyCollection(
            [
                RuntimeDependency(
                    id="svelte-language-server",
                    description="svelte-language-server package",
                    command=["npm", "install", "--prefix", "./", "svelte-language-server@0.17.5"],
                    platform_id="any",
                ),
                RuntimeDependency(
                    id="typescript",
                    description="typescript package (required by svelte-language-server)",
                    command=["npm", "install", "--prefix", "./", "typescript@5.5.4"],
                    platform_id="any",
                ),
            ]
        )

        # Verify both node and npm are installed
        is_node_installed = shutil.which("node") is not None
        assert is_node_installed, (
            "node is not installed or isn't in PATH. Please install Node.js and try again.\n"
            "Visit https://nodejs.org/ to download and install Node.js.\n"
            "Svelte language server requires Node.js 12 or later."
        )
        is_npm_installed = shutil.which("npm") is not None
        assert is_npm_installed, "npm is not installed or isn't in PATH. Please install npm and try again."

        # Install svelte-language-server if not already installed
        svelte_ls_dir = os.path.join(cls.ls_resources_dir(solidlsp_settings), "svelte-lsp")
        svelte_executable_path = os.path.join(svelte_ls_dir, "node_modules", ".bin", "svelteserver")

        # On Windows, the executable has a .cmd extension
        if PlatformUtils.get_platform_id().is_windows():
            svelte_executable_path = svelte_executable_path + ".cmd"

        if not os.path.exists(svelte_executable_path):
            logger.log(f"Svelte Language Server executable not found at {svelte_executable_path}. Installing...", logging.INFO)
            with LogTime("Installation of Svelte language server dependencies", logger=logger.logger):
                deps.install(logger, svelte_ls_dir)

        if not os.path.exists(svelte_executable_path):
            raise FileNotFoundError(
                f"svelte-language-server executable not found at {svelte_executable_path}, something went wrong with the installation."
            )
        return [svelte_executable_path, "--stdio"]

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
                        "symbolKind": {"valueSet": list(range(1, 27))},
                        "hierarchicalDocumentSymbolSupport": True,
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
                        "contextSupport": True,
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
                    "foldingRange": {"dynamicRegistration": True},
                    "formatting": {"dynamicRegistration": True},
                    "rangeFormatting": {"dynamicRegistration": True},
                    "onTypeFormatting": {"dynamicRegistration": True},
                },
                "workspace": {
                    "applyEdit": True,
                    "workspaceEdit": {"documentChanges": True},
                    "didChangeConfiguration": {"dynamicRegistration": True},
                    "didChangeWatchedFiles": {"dynamicRegistration": True},
                    "symbol": {"dynamicRegistration": True},
                    "configuration": True,
                },
            },
            "initializationOptions": {
                "configuration": {
                    "svelte": {
                        "enable-ts-plugin": True,
                        "format": {
                            "enable": True,
                            "config": {
                                "svelteStrictMode": False,
                                "svelteIndentScriptAndStyle": True,
                            },
                        },
                    },
                    "typescript": {
                        "inlayHints": {
                            "parameterNames": {"enabled": "none"},
                            "parameterTypes": {"enabled": False},
                            "variableTypes": {"enabled": False},
                            "propertyDeclarationTypes": {"enabled": False},
                            "functionLikeReturnTypes": {"enabled": False},
                            "enumMemberValues": {"enabled": False},
                        },
                    },
                },
                "dontFilterIncompleteCompletions": True,
                "npmPackageInfo": {"includeAllWorkspaceSymbols": True},
            },
            "processId": os.getpid(),
            "rootPath": repository_absolute_path,
            "rootUri": root_uri,
            "workspaceFolders": [{"name": "workspace", "uri": root_uri}],
        }

        return InitializeParams(**initialize_params)

"""MCP server for SonarCloud with hotspot support."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mcp-sonarcloud")
except PackageNotFoundError:
    __version__ = "0+unknown"

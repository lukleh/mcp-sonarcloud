"""Tests for the tool-boundary error translation under mcp SDK 2.x."""

import inspect

import httpx
import pytest
from mcp import MCPError
from mcp.client import Client
from mcp.server.mcpserver.exceptions import ToolError

from mcp_sonarcloud.server import ANTICIPATED_TOOL_ERRORS, mcp, surface_tool_errors


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    """Keep tests away from real config and credentials."""
    for name in ("config", "state", "cache"):
        monkeypatch.setenv(f"MCP_SONARCLOUD_{name.upper()}_DIR", str(tmp_path / name))
    for name in ("TOKEN", "ORGANIZATION", "URL", "TIMEOUT_SEC"):
        monkeypatch.delenv(f"SONARCLOUD_{name}", raising=False)


def _raising(exc: BaseException):
    @surface_tool_errors
    async def tool() -> str:
        raise exc

    return tool


_REQUEST = httpx.Request("GET", "https://sonarcloud.io/api/components/show")


@pytest.mark.parametrize(
    "exc",
    [
        ValueError("SONARCLOUD_TOKEN environment variable is required"),
        httpx.HTTPStatusError(
            "Client error '404 Not Found'",
            request=_REQUEST,
            response=httpx.Response(404, request=_REQUEST),
        ),
        httpx.ConnectError("All connection attempts failed", request=_REQUEST),
        httpx.ReadTimeout("timed out", request=_REQUEST),
        PermissionError("config.toml is not readable"),
    ],
)
@pytest.mark.asyncio
async def test_anticipated_failures_become_tool_errors(exc):
    """Operational failures keep their text and their cause."""
    with pytest.raises(ToolError) as info:
        await _raising(exc)()

    assert str(info.value) == str(exc)
    assert info.value.__cause__ is exc


def test_anticipated_list_matches_parametrized_cases():
    """Guard the allow-list against silent drift."""
    assert ANTICIPATED_TOOL_ERRORS == (ValueError, httpx.HTTPError, OSError)


@pytest.mark.asyncio
async def test_empty_message_falls_back_to_class_name():
    """A bare exception still yields a readable result, not an empty one."""
    with pytest.raises(ToolError, match="^ValueError$"):
        await _raising(ValueError())()


@pytest.mark.parametrize("exc_type", [TypeError, AttributeError, KeyError, RuntimeError])
@pytest.mark.asyncio
async def test_programming_errors_keep_sdk_crash_handling(exc_type):
    """Bugs propagate unchanged so the SDK masks the text and logs the traceback."""
    with pytest.raises(exc_type):
        await _raising(exc_type("internal detail"))()


@pytest.mark.asyncio
async def test_tool_error_passes_through_unchanged():
    """No double wrapping when the body already raised a ToolError."""
    original = ToolError("already anticipated")
    with pytest.raises(ToolError) as info:
        await _raising(original)()

    assert info.value is original


@pytest.mark.asyncio
async def test_protocol_error_passes_through_unchanged():
    """MCPError is a protocol error and must not become an is_error result."""
    original = MCPError(-32600, "invalid request")
    with pytest.raises(MCPError) as info:
        await _raising(original)()

    assert info.value is original


def test_wrapper_keeps_the_signature_the_sdk_reads():
    """The tool schema is built from the wrapped function's signature and docstring."""

    async def show_component(component: str, branch: str | None = None) -> str:
        """Show a component."""
        return component

    wrapped = surface_tool_errors(show_component)

    assert wrapped.__name__ == "show_component"
    assert wrapped.__doc__ == "Show a component."
    assert inspect.signature(wrapped) == inspect.signature(show_component)
    assert inspect.iscoroutinefunction(wrapped)


def test_every_registered_tool_surfaces_errors():
    """A tool registered without the decorator would hide its failures again."""
    wrapper_code = _raising(ValueError()).__code__

    tools = mcp._tool_manager.list_tools()
    assert tools
    unwrapped = [tool.name for tool in tools if tool.fn.__code__ is not wrapper_code]
    assert unwrapped == []


@pytest.mark.asyncio
async def test_client_sees_missing_token_message():
    """The reason reaches the caller through the in-process client."""
    async with Client(mcp) as client:
        result = await client.call_tool("show_component", {"component": "project1"})

    assert result.is_error
    assert result.content[0].text == (
        "Error executing tool show_component: "
        "SONARCLOUD_TOKEN environment variable is required"
    )


@pytest.mark.asyncio
async def test_client_sees_sonarcloud_http_error(monkeypatch, httpx_mock):
    """An HTTP error from SonarCloud reaches the caller with its status and reason."""
    monkeypatch.setenv("SONARCLOUD_TOKEN", "test-token")
    monkeypatch.setenv("SONARCLOUD_ORGANIZATION", "test-org")
    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/show?component=missing&organization=test-org",
        status_code=404,
        json={"errors": [{"msg": "Component key 'missing' not found"}]},
    )

    async with Client(mcp) as client:
        result = await client.call_tool("show_component", {"component": "missing"})

    assert result.is_error
    assert result.content[0].text == (
        "Error executing tool show_component: SonarCloud returned HTTP 404 Not Found: "
        "Component key 'missing' not found"
    )


@pytest.mark.asyncio
async def test_client_sees_status_line_without_error_body(monkeypatch, httpx_mock):
    """Without SonarCloud's errors[] body the caller still gets httpx's status line."""
    monkeypatch.setenv("SONARCLOUD_TOKEN", "test-token")
    monkeypatch.setenv("SONARCLOUD_ORGANIZATION", "test-org")
    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/show?component=missing&organization=test-org",
        status_code=502,
        text="<html>Bad Gateway</html>",
    )

    async with Client(mcp) as client:
        result = await client.call_tool("show_component", {"component": "missing"})

    assert result.is_error
    assert result.content[0].text.startswith(
        "Error executing tool show_component: Server error '502 Bad Gateway' for url "
        "'https://sonarcloud.io/api/components/show?component=missing&organization=test-org'"
    )

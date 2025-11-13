"""Tests for MCP SonarCloud server."""

import os
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "SONARCLOUD_TOKEN": "test-token",
            "SONARCLOUD_ORGANIZATION": "test-org",
            "SONARCLOUD_URL": "https://sonarcloud.io",
        },
    ):
        yield


def test_get_config(mock_env):
    """Test configuration loading from environment."""
    from mcp_sonarcloud.server import get_config

    config = get_config()

    assert config["token"] == "test-token"
    assert config["organization"] == "test-org"
    assert config["base_url"] == "https://sonarcloud.io"


def test_get_config_missing_token():
    """Test configuration fails without token."""
    from mcp_sonarcloud.server import get_config

    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="SONARCLOUD_TOKEN"):
            get_config()


@pytest.mark.asyncio
async def test_search_projects(mock_env, httpx_mock):
    """Test search_my_sonarqube_projects tool."""
    from mcp_sonarcloud.server import search_my_sonarqube_projects

    # Mock the API response
    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/search?p=1&organization=test-org",
        json={
            "components": [
                {"key": "project1", "name": "Project 1"},
                {"key": "project2", "name": "Project 2"},
            ],
            "paging": {"pageIndex": 1, "pageSize": 100, "total": 2},
        },
    )

    result = await search_my_sonarqube_projects(page="1")

    assert len(result.projects) == 2
    assert result.projects[0].key == "project1"
    assert result.projects[0].name == "Project 1"
    assert result.paging.total == 2


@pytest.mark.asyncio
async def test_show_component(mock_env, httpx_mock):
    """Test show_component tool."""
    from mcp_sonarcloud.server import show_component

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/show?component=project1&organization=test-org",
        json={"component": {"key": "project1", "name": "Project 1"}},
    )

    result = await show_component(component="project1")

    assert result["component"]["key"] == "project1"


@pytest.mark.asyncio
async def test_component_tree(mock_env, httpx_mock):
    """Test component_tree tool with qualifiers and sorting."""
    from mcp_sonarcloud.server import component_tree

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/components/tree?component=project1&p=2&ps=50"
            "&qualifiers=FIL,UTS&strategy=children&s=name,path&asc=true&organization=test-org"
        ),
        json={"components": [], "paging": {"pageIndex": 2, "pageSize": 50, "total": 0}},
    )

    result = await component_tree(
        component="project1",
        p=2,
        ps=50,
        qualifiers=["FIL", "UTS"],
        strategy="children",
        sort_fields=["name", "path"],
        asc=True,
    )

    assert result["components"] == []


@pytest.mark.asyncio
async def test_search_hotspots(mock_env, httpx_mock):
    """Test search_hotspots tool."""
    from mcp_sonarcloud.server import search_hotspots

    # Mock the API response - organization is added automatically
    httpx_mock.add_response(
        url="https://sonarcloud.io/api/hotspots/search?projectKey=test-project&p=1&ps=100&organization=test-org",
        json={
            "hotspots": [
                {
                    "key": "AX123",
                    "component": "test.java",
                    "message": "Test hotspot",
                    "status": "TO_REVIEW",
                    "line": 10,
                },
            ],
            "paging": {"pageIndex": 1, "pageSize": 100, "total": 1},
        },
    )

    result = await search_hotspots(projectKey="test-project")

    assert len(result["hotspots"]) == 1
    assert result["hotspots"][0]["key"] == "AX123"
    assert result["paging"]["total"] == 1


@pytest.mark.asyncio
async def test_show_hotspot(mock_env, httpx_mock):
    """Test show_hotspot tool."""
    from mcp_sonarcloud.server import show_hotspot

    # Mock the API response - organization is added automatically
    httpx_mock.add_response(
        url="https://sonarcloud.io/api/hotspots/show?hotspot=AX123&organization=test-org",
        json={
            "key": "AX123",
            "message": "Test hotspot",
            "component": {"key": "test.java", "path": "src/test.java"},
            "status": "TO_REVIEW",
            "author": "user@example.com",
            "rule": {"key": "java:S123", "name": "Test Rule"},
            "canChangeStatus": True,
        },
    )

    result = await show_hotspot(hotspot="AX123")

    assert result.key == "AX123"
    assert result.status == "TO_REVIEW"
    assert result.canChangeStatus is True


@pytest.mark.asyncio
async def test_change_hotspot_status(mock_env, httpx_mock):
    """Test change_hotspot_status tool."""
    from mcp_sonarcloud.server import change_hotspot_status

    # Mock the API response
    httpx_mock.add_response(
        url="https://sonarcloud.io/api/hotspots/change_status?organization=test-org",
        method="POST",
        json={},
    )

    result = await change_hotspot_status(
        hotspot="AX123", status="REVIEWED", resolution="SAFE"
    )

    assert result["success"] is True
    assert "AX123" in result["message"]


@pytest.mark.asyncio
async def test_list_issue_authors(mock_env, httpx_mock):
    """Test list_issue_authors tool."""
    from mcp_sonarcloud.server import list_issue_authors

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/issues/authors?ps=50&project=test-project"
            "&q=dev&organization=test-org"
        ),
        json={"authors": ["dev@example.com"], "paging": {"pageIndex": 1, "pageSize": 50, "total": 1}},
    )

    result = await list_issue_authors(project="test-project", q="dev", ps=50)

    assert result["authors"] == ["dev@example.com"]


@pytest.mark.asyncio
async def test_get_issue_changelog(mock_env, httpx_mock):
    """Test get_issue_changelog tool."""
    from mcp_sonarcloud.server import get_issue_changelog

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/issues/changelog?issue=AX123&organization=test-org",
        json={"changelog": [{"author": "dev", "diffs": []}]},
    )

    result = await get_issue_changelog(issue="AX123")

    assert result["changelog"][0]["author"] == "dev"


@pytest.mark.asyncio
async def test_list_issue_tags(mock_env, httpx_mock):
    """Test list_issue_tags tool."""
    from mcp_sonarcloud.server import list_issue_tags

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/issues/tags?ps=25&project=test-project"
            "&q=security&organization=test-org"
        ),
        json={"tags": ["security", "ai"], "paging": {"pageIndex": 1, "pageSize": 25, "total": 2}},
    )

    result = await list_issue_tags(project="test-project", q="security", ps=25)

    assert "security" in result["tags"]


@pytest.mark.asyncio
async def test_list_quality_gates(mock_env, httpx_mock):
    """Test list_quality_gates tool."""
    from mcp_sonarcloud.server import list_quality_gates

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/qualitygates/list?organization=test-org",
        json={"qualitygates": [{"id": 1, "name": "Sonar way"}]},
    )

    result = await list_quality_gates()

    assert result["qualitygates"][0]["name"] == "Sonar way"


@pytest.mark.asyncio
async def test_show_quality_gate(mock_env, httpx_mock):
    """Test show_quality_gate tool by name."""
    from mcp_sonarcloud.server import show_quality_gate

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/qualitygates/show?name=Sonar+way"
            "&organization=test-org"
        ),
        json={"id": 9, "name": "Sonar way", "conditions": []},
    )

    result = await show_quality_gate(name="Sonar way")

    assert result["id"] == 9


@pytest.mark.asyncio
async def test_show_quality_gate_requires_identifier(mock_env):
    """Ensure show_quality_gate validates input."""
    from mcp_sonarcloud.server import show_quality_gate

    with pytest.raises(ValueError):
        await show_quality_gate()


@pytest.mark.asyncio
async def test_search_quality_gates(mock_env, httpx_mock):
    """Test search_quality_gates tool."""
    from mcp_sonarcloud.server import search_quality_gates

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/qualitygates/search?gateId=9&page=1"
            "&pageSize=50&selected=true&organization=test-org"
        ),
        json={"results": [{"key": "project1"}], "paging": {"pageIndex": 1}},
    )

    result = await search_quality_gates(gateId=9, pageSize=50, selected=True)

    assert result["results"][0]["key"] == "project1"


@pytest.mark.asyncio
async def test_get_quality_gate_by_project(mock_env, httpx_mock):
    """Test get_quality_gate_by_project tool."""
    from mcp_sonarcloud.server import get_quality_gate_by_project

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/qualitygates/get_by_project?project=test-project&organization=test-org",
        json={"qualityGate": {"id": 9, "name": "Sonar way"}},
    )

    result = await get_quality_gate_by_project(project="test-project")

    assert result["qualityGate"]["name"] == "Sonar way"

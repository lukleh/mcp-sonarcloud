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


# Missing tool tests


@pytest.mark.asyncio
async def test_search_sonar_issues_in_projects(mock_env, httpx_mock):
    """Test search_sonar_issues_in_projects tool."""
    from mcp_sonarcloud.server import search_sonar_issues_in_projects

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/issues/search?p=1&ps=50"
            "&projects=project1,project2&pullRequest=123"
            "&impactSeverities=HIGH,BLOCKER&organization=test-org"
        ),
        json={
            "issues": [
                {
                    "key": "AY123",
                    "rule": "java:S1234",
                    "severity": "HIGH",
                    "component": "project1:src/Main.java",
                    "message": "Test issue",
                    "line": 42,
                    "status": "OPEN",
                    "type": "BUG",
                },
            ],
            "total": 1,
            "paging": {"pageIndex": 1, "pageSize": 50, "total": 1},
        },
    )

    result = await search_sonar_issues_in_projects(
        projects=["project1", "project2"],
        pullRequestId="123",
        severities="HIGH,BLOCKER",
        p=1,
        ps=50,
    )

    assert len(result.issues) == 1
    assert result.issues[0].key == "AY123"
    assert result.issues[0].severity == "HIGH"
    assert result.total == 1
    assert result.paging.total == 1


@pytest.mark.asyncio
async def test_get_project_quality_gate_status(mock_env, httpx_mock):
    """Test get_project_quality_gate_status tool."""
    from mcp_sonarcloud.server import get_project_quality_gate_status

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/qualitygates/project_status"
            "?projectKey=test-project&pullRequest=123&organization=test-org"
        ),
        json={
            "projectStatus": {
                "status": "ERROR",
                "conditions": [
                    {
                        "status": "ERROR",
                        "metricKey": "new_coverage",
                        "actualValue": "65.5",
                        "errorThreshold": "80",
                    },
                    {
                        "status": "OK",
                        "metricKey": "new_bugs",
                        "actualValue": "0",
                        "errorThreshold": "0",
                    },
                ],
            }
        },
    )

    result = await get_project_quality_gate_status(
        projectKey="test-project", pullRequest="123"
    )

    assert result.status == "ERROR"
    assert len(result.conditions) == 2
    assert result.conditions[0].status == "ERROR"
    assert result.conditions[0].metricKey == "new_coverage"
    assert result.conditions[0].actualValue == "65.5"


# Error handling tests


@pytest.mark.asyncio
async def test_make_request_401_unauthorized(mock_env, httpx_mock):
    """Test handling of 401 Unauthorized error."""
    from mcp_sonarcloud.server import search_my_sonarqube_projects
    import httpx

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/search?p=1&organization=test-org",
        status_code=401,
        json={"errors": [{"msg": "Unauthorized"}]},
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await search_my_sonarqube_projects(page="1")

    assert exc_info.value.response.status_code == 401


@pytest.mark.asyncio
async def test_make_request_404_not_found(mock_env, httpx_mock):
    """Test handling of 404 Not Found error."""
    from mcp_sonarcloud.server import show_hotspot
    import httpx

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/hotspots/show?hotspot=INVALID&organization=test-org",
        status_code=404,
        json={"errors": [{"msg": "Hotspot not found"}]},
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await show_hotspot(hotspot="INVALID")

    assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_make_request_500_server_error(mock_env, httpx_mock):
    """Test handling of 500 Internal Server Error."""
    from mcp_sonarcloud.server import list_quality_gates
    import httpx

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/qualitygates/list?organization=test-org",
        status_code=500,
        json={"errors": [{"msg": "Internal server error"}]},
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await list_quality_gates()

    assert exc_info.value.response.status_code == 500


@pytest.mark.asyncio
async def test_make_request_403_forbidden(mock_env, httpx_mock):
    """Test handling of 403 Forbidden error."""
    from mcp_sonarcloud.server import get_quality_gate_by_project
    import httpx

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/qualitygates/get_by_project?project=private-project&organization=test-org",
        status_code=403,
        json={"errors": [{"msg": "Insufficient privileges"}]},
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await get_quality_gate_by_project(project="private-project")

    assert exc_info.value.response.status_code == 403


# Edge case tests


@pytest.mark.asyncio
async def test_search_projects_empty_results(mock_env, httpx_mock):
    """Test search_my_sonarqube_projects with no results."""
    from mcp_sonarcloud.server import search_my_sonarqube_projects

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/search?p=1&organization=test-org",
        json={
            "components": [],
            "paging": {"pageIndex": 1, "pageSize": 100, "total": 0},
        },
    )

    result = await search_my_sonarqube_projects(page="1")

    assert len(result.projects) == 0
    assert result.paging.total == 0


@pytest.mark.asyncio
async def test_search_hotspots_with_optional_fields_missing(mock_env, httpx_mock):
    """Test search_hotspots when optional fields are null."""
    from mcp_sonarcloud.server import search_hotspots

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/hotspots/search?projectKey=test-project&p=1&ps=100&organization=test-org",
        json={
            "hotspots": [
                {
                    "key": "AX123",
                    "component": "test.java",
                    "message": "Test hotspot",
                    "status": "TO_REVIEW",
                    # Optional fields missing: author, resolution, line, vulnerabilityProbability
                },
            ],
            "paging": {"pageIndex": 1, "pageSize": 100, "total": 1},
        },
    )

    result = await search_hotspots(projectKey="test-project")

    assert len(result["hotspots"]) == 1
    assert result["hotspots"][0]["author"] is None
    assert result["hotspots"][0]["resolution"] is None
    assert result["hotspots"][0]["line"] is None


@pytest.mark.asyncio
async def test_change_hotspot_status_empty_response(mock_env, httpx_mock):
    """Test change_hotspot_status with empty response body."""
    from mcp_sonarcloud.server import change_hotspot_status

    # Empty response is common for successful POST operations
    httpx_mock.add_response(
        url="https://sonarcloud.io/api/hotspots/change_status?organization=test-org",
        method="POST",
        content=b"",  # Explicitly empty response
    )

    result = await change_hotspot_status(hotspot="AX123", status="TO_REVIEW")

    assert result["success"] is True
    assert "AX123" in result["message"]


@pytest.mark.asyncio
async def test_get_project_quality_gate_status_no_conditions(mock_env, httpx_mock):
    """Test quality gate status with no conditions (edge case)."""
    from mcp_sonarcloud.server import get_project_quality_gate_status

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/qualitygates/project_status?projectKey=test-project&organization=test-org",
        json={
            "projectStatus": {
                "status": "NONE",
                "conditions": [],
            }
        },
    )

    result = await get_project_quality_gate_status(projectKey="test-project")

    assert result.status == "NONE"
    assert len(result.conditions) == 0


# Organization requirement tests


def test_require_organization_missing():
    """Test require_organization fails when SONARCLOUD_ORGANIZATION is not set."""
    from mcp_sonarcloud.server import require_organization

    with patch.dict(os.environ, {"SONARCLOUD_TOKEN": "test-token"}, clear=True):
        with pytest.raises(
            ValueError, match="requires SONARCLOUD_ORGANIZATION to be set"
        ):
            require_organization("test_action")


def test_require_organization_present(mock_env):
    """Test require_organization succeeds when SONARCLOUD_ORGANIZATION is set."""
    from mcp_sonarcloud.server import require_organization

    config = require_organization("test_action")

    assert config["organization"] == "test-org"
    assert config["token"] == "test-token"


@pytest.mark.asyncio
async def test_list_issue_authors_without_organization(httpx_mock):
    """Test list_issue_authors fails without organization set."""
    from mcp_sonarcloud.server import list_issue_authors

    with patch.dict(os.environ, {"SONARCLOUD_TOKEN": "test-token"}, clear=True):
        with pytest.raises(
            ValueError, match="list_issue_authors requires SONARCLOUD_ORGANIZATION"
        ):
            await list_issue_authors()


# Additional parameter combination tests


@pytest.mark.asyncio
async def test_show_component_with_branch(mock_env, httpx_mock):
    """Test show_component with branch parameter."""
    from mcp_sonarcloud.server import show_component

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/show?component=project1&branch=develop&organization=test-org",
        json={"component": {"key": "project1", "name": "Project 1", "branch": "develop"}},
    )

    result = await show_component(component="project1", branch="develop")

    assert result["component"]["key"] == "project1"
    assert result["component"]["branch"] == "develop"


@pytest.mark.asyncio
async def test_show_component_with_pull_request(mock_env, httpx_mock):
    """Test show_component with pullRequest parameter."""
    from mcp_sonarcloud.server import show_component

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/components/show?component=project1&pullRequest=456&organization=test-org",
        json={"component": {"key": "project1", "name": "Project 1", "pullRequest": "456"}},
    )

    result = await show_component(component="project1", pullRequest="456")

    assert result["component"]["key"] == "project1"
    assert result["component"]["pullRequest"] == "456"


@pytest.mark.asyncio
async def test_search_hotspots_with_multiple_files(mock_env, httpx_mock):
    """Test search_hotspots with multiple files filter."""
    from mcp_sonarcloud.server import search_hotspots

    httpx_mock.add_response(
        url=(
            "https://sonarcloud.io/api/hotspots/search?projectKey=test-project&p=1&ps=100"
            "&files=src/main.java,src/util.java&branch=main&organization=test-org"
        ),
        json={
            "hotspots": [],
            "paging": {"pageIndex": 1, "pageSize": 100, "total": 0},
        },
    )

    result = await search_hotspots(
        projectKey="test-project",
        files="src/main.java,src/util.java",
        branch="main",
    )

    assert result["paging"]["total"] == 0


@pytest.mark.asyncio
async def test_get_project_quality_gate_status_by_analysis_id(mock_env, httpx_mock):
    """Test get_project_quality_gate_status using analysisId."""
    from mcp_sonarcloud.server import get_project_quality_gate_status

    httpx_mock.add_response(
        url="https://sonarcloud.io/api/qualitygates/project_status?analysisId=AX999&organization=test-org",
        json={
            "projectStatus": {
                "status": "OK",
                "conditions": [],
            }
        },
    )

    result = await get_project_quality_gate_status(analysisId="AX999")

    assert result.status == "OK"

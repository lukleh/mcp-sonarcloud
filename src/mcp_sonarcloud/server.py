"""MCP server exposing SonarCloud/SonarQube project, issue, quality gate, and hotspot tools."""

import asyncio
import os
from typing import Annotated, Any, Optional
from urllib.parse import urlencode

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field


# Initialize MCP server
mcp = FastMCP("SonarCloud")


# Configuration
def get_config() -> dict[str, str]:
    """Get configuration from environment variables."""
    token = os.getenv("SONARCLOUD_TOKEN")
    org = os.getenv("SONARCLOUD_ORGANIZATION")
    base_url = os.getenv("SONARCLOUD_URL", "https://sonarcloud.io")

    if not token:
        raise ValueError("SONARCLOUD_TOKEN environment variable is required")

    return {
        "token": token,
        "organization": org,
        "base_url": base_url,
    }


# HTTP Client helper
async def make_request(
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
    method: str = "GET",
    body: Optional[str] = None,
    config: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Make an HTTP request to SonarCloud API."""
    config = config or get_config()
    url = f"{config['base_url']}{endpoint}"

    headers = {
        "Authorization": f"Bearer {config['token']}",
    }

    if body:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    # Add organization to params if set
    if params is None:
        params = {}

    if config["organization"]:
        params.setdefault("organization", config["organization"])

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
        elif method == "POST":
            response = await client.post(url, params=params, headers=headers, content=body, timeout=30.0)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        # Handle empty responses (common for successful POST operations)
        if not response.content or len(response.content) == 0:
            return {}

        return response.json()


def require_organization(action_name: str) -> dict[str, str]:
    """Ensure SONARCLOUD_ORGANIZATION is available for org-scoped endpoints."""
    config = get_config()
    if not config["organization"]:
        raise ValueError(
            f"{action_name} requires SONARCLOUD_ORGANIZATION to be set in the environment."
        )
    return config


# Pydantic models for structured responses
class Paging(BaseModel):
    """Pagination information."""
    pageIndex: int = Field(alias="pageIndex")
    pageSize: int = Field(alias="pageSize")
    total: int


class Project(BaseModel):
    """Project information."""
    key: str
    name: str


class SearchProjectsResponse(BaseModel):
    """Response from search_my_sonarqube_projects tool."""
    projects: list[Project]
    paging: Paging


class Issue(BaseModel):
    """Issue information."""
    key: str
    rule: str
    severity: Optional[str] = None
    component: str
    message: str
    line: Optional[int] = None
    status: str
    type: str


class SearchIssuesResponse(BaseModel):
    """Response from search_sonar_issues_in_projects tool."""
    issues: list[Issue]
    total: int
    paging: Paging


class QualityGateCondition(BaseModel):
    """Quality gate condition."""
    status: str
    metricKey: str
    actualValue: Optional[str] = None
    errorThreshold: Optional[str] = None


class QualityGateStatus(BaseModel):
    """Quality gate status."""
    status: str
    conditions: list[QualityGateCondition]


class Hotspot(BaseModel):
    """Security hotspot information."""
    key: str
    component: str
    message: str
    author: Optional[str] = None
    status: str
    resolution: Optional[str] = None
    line: Optional[int] = None
    vulnerabilityProbability: Optional[str] = None


class HotspotDetails(BaseModel):
    """Detailed security hotspot information."""
    key: str
    message: str
    component: dict[str, Any]
    status: str
    resolution: Optional[str] = None
    author: Optional[str] = None
    rule: dict[str, Any]
    canChangeStatus: bool


# MCP Tools

@mcp.tool()
async def search_my_sonarqube_projects(
    page: Annotated[str, Field(default="1", description="Page number to retrieve (1-indexed)")] = "1"
) -> SearchProjectsResponse:
    """Paginated project finder; use when you need keys/names before running other SonarCloud tools.

    Returns a list of projects with their keys and names, plus pagination information.
    Use the project keys returned here for other tools like search_sonar_issues_in_projects or search_hotspots.

    Example: search_my_sonarqube_projects(page="1")
    """
    params = {"p": page}

    # Check if organization is set, otherwise use qualifiers
    config = get_config()
    if not config["organization"]:
        params["qualifiers"] = "TRK"

    result = await make_request("/api/components/search", params=params)

    projects = [
        Project(key=p["key"], name=p["name"])
        for p in result.get("components", [])
    ]

    paging_data = result.get("paging", {})
    paging = Paging(
        pageIndex=paging_data.get("pageIndex", 1),
        pageSize=paging_data.get("pageSize", 100),
        total=paging_data.get("total", 0),
    )

    return SearchProjectsResponse(projects=projects, paging=paging)


@mcp.tool()
async def show_component(
    component: Annotated[str, Field(description="Project key or component key (e.g., 'my-project' or 'my-project:src/main.py')")],
    branch: Annotated[Optional[str], Field(default=None, description="Branch name to retrieve component from (e.g., 'main', 'develop')")] = None,
    pullRequest: Annotated[Optional[str], Field(default=None, description="Pull request ID to retrieve component from (e.g., '123')")] = None,
) -> dict[str, Any]:
    """Return detailed metadata (qualifier, tags, branches) for a specific project/component.

    Returns component information including name, qualifier (TRK for project, FIL for file, etc.),
    tags, and available branches. Use this to inspect project metadata or verify component existence.

    Example: show_component(component="my-project", branch="main")
    """
    params: dict[str, Any] = {"component": component}

    if branch:
        params["branch"] = branch
    if pullRequest:
        params["pullRequest"] = pullRequest

    return await make_request("/api/components/show", params=params)


@mcp.tool()
async def component_tree(
    component: Annotated[str, Field(description="Project key to traverse (e.g., 'my-project')")],
    qualifiers: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Filter by component qualifiers. Valid values: 'BRC' (branch), 'DIR' (directory), 'FIL' (file), 'TRK' (project), 'UTS' (test file). Example: ['FIL', 'DIR']"
        ),
    ] = None,
    branch: Annotated[Optional[str], Field(default=None, description="Branch name (e.g., 'main')")] = None,
    pullRequest: Annotated[Optional[str], Field(default=None, description="Pull request ID (e.g., '123')")] = None,
    q: Annotated[Optional[str], Field(default=None, description="Search query to filter component names (case-insensitive)")] = None,
    strategy: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Tree traversal strategy. Valid values: 'all' (default), 'children' (direct children only), 'leaves' (files only)"
        ),
    ] = None,
    sort_fields: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="Fields to sort by. Valid values: 'name', 'path', 'qualifier'. Example: ['name', 'path']"
        ),
    ] = None,
    asc: Annotated[Optional[bool], Field(default=None, description="Sort ascending (true) or descending (false). Defaults to true")] = None,
    p: Annotated[int, Field(default=1, description="Page number (1-indexed)")] = 1,
    ps: Annotated[int, Field(default=100, description="Page size (max 500)")] = 100,
) -> dict[str, Any]:
    """Traverse modules/files inside a project; supports paging, qualifier filters, and branch/PR context.

    Returns a hierarchical view of project components (directories, files, modules).
    Use this to explore project structure or find specific files.

    Example: component_tree(component="my-project", qualifiers=["FIL"], q="test", branch="main")
    """
    params: dict[str, Any] = {
        "component": component,
        "p": p,
        "ps": ps,
    }

    if qualifiers:
        params["qualifiers"] = ",".join(qualifiers)
    if branch:
        params["branch"] = branch
    if pullRequest:
        params["pullRequest"] = pullRequest
    if q:
        params["q"] = q
    if strategy:
        params["strategy"] = strategy
    if sort_fields:
        params["s"] = ",".join(sort_fields)
    if asc is not None:
        params["asc"] = "true" if asc else "false"

    return await make_request("/api/components/tree", params=params)


@mcp.tool()
async def search_sonar_issues_in_projects(
    projects: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="List of project keys to search in (e.g., ['my-project', 'another-project']). Can be omitted to search across all projects in organization"
        ),
    ] = None,
    pullRequestId: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Filter issues by pull request ID (e.g., '123')"
        ),
    ] = None,
    severities: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Comma-separated impact severity levels. Valid values: 'INFO', 'LOW', 'MEDIUM', 'HIGH', 'BLOCKER'. Example: 'HIGH,BLOCKER'"
        ),
    ] = None,
    p: Annotated[int, Field(default=1, description="Page number (1-indexed)")] = 1,
    ps: Annotated[int, Field(default=100, description="Page size (max 500)")] = 100,
) -> SearchIssuesResponse:
    """Search issues across one or more projects with optional PR, severity, and pagination controls.

    Returns a list of issues matching the filters, with key details like rule, severity, component, and status.
    Use this to find code quality issues, bugs, vulnerabilities, or code smells in your projects.

    Example: search_sonar_issues_in_projects(projects=["my-project"], severities="HIGH,BLOCKER", pullRequestId="123")
    """
    params: dict[str, Any] = {
        "p": p,
        "ps": ps,
    }

    if projects:
        params["projects"] = ",".join(projects)

    if pullRequestId:
        params["pullRequest"] = pullRequestId

    if severities:
        params["impactSeverities"] = severities

    result = await make_request("/api/issues/search", params=params)

    issues = [
        Issue(
            key=i["key"],
            rule=i["rule"],
            severity=i.get("severity"),
            component=i["component"],
            message=i["message"],
            line=i.get("line"),
            status=i["status"],
            type=i["type"],
        )
        for i in result.get("issues", [])
    ]

    paging_data = result.get("paging", {})
    paging = Paging(
        pageIndex=paging_data.get("pageIndex", 1),
        pageSize=paging_data.get("pageSize", 100),
        total=paging_data.get("total", 0),
    )

    return SearchIssuesResponse(
        issues=issues,
        total=result.get("total", len(issues)),
        paging=paging,
    )


@mcp.tool()
async def list_issue_authors(
    project: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Project key to filter authors by (e.g., 'my-project'). Omit to search across entire organization"
        ),
    ] = None,
    q: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Search query to filter author names (case-insensitive partial match)"
        ),
    ] = None,
    ps: Annotated[int, Field(default=100, description="Page size - maximum number of authors to return (max 500)")] = 100,
) -> dict[str, Any]:
    """Discover SCM author accounts used in your org/project; useful for reviewer pickers or stats.

    Returns a list of authors (from source control) who have contributed to issues in the organization or project.
    Requires SONARCLOUD_ORGANIZATION to be set.

    Example: list_issue_authors(project="my-project", q="john")
    """
    config = require_organization("list_issue_authors")
    params: dict[str, Any] = {"ps": ps}

    if project:
        params["project"] = project
    if q:
        params["q"] = q

    return await make_request("/api/issues/authors", params=params, config=config)


@mcp.tool()
async def get_issue_changelog(
    issue: Annotated[str, Field(description="Issue key to retrieve history for (e.g., 'AXabc123def456')")]
) -> dict[str, Any]:
    """Return the change history (status, assignee, severity edits) for the given issue key.

    Returns a chronological list of all changes made to an issue, including who made the change and when.
    Useful for auditing issue lifecycle or understanding how an issue was resolved.

    Example: get_issue_changelog(issue="AXabc123def456")
    """
    params = {"issue": issue}
    return await make_request("/api/issues/changelog", params=params)


@mcp.tool()
async def list_issue_tags(
    project: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Project key to filter tags by (e.g., 'my-project'). Omit to search across entire organization"
        ),
    ] = None,
    q: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Search query to filter tag names (case-insensitive partial match)"
        ),
    ] = None,
    ps: Annotated[int, Field(default=100, description="Page size - maximum number of tags to return (max 500)")] = 100,
) -> dict[str, Any]:
    """List available issue tags (optionally filtered by project or search query) to power tag selectors.

    Returns a list of tags used on issues in the organization or project.
    Tags are custom labels that can be applied to issues for categorization.

    Example: list_issue_tags(project="my-project", q="security")
    """
    params: dict[str, Any] = {"ps": ps}

    if project:
        params["project"] = project
    if q:
        params["q"] = q

    return await make_request("/api/issues/tags", params=params)


@mcp.tool()
async def get_project_quality_gate_status(
    analysisId: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Analysis ID to check quality gate for. Get this from analysis results or API"
        ),
    ] = None,
    projectId: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Numeric project ID (less common, prefer projectKey)"
        ),
    ] = None,
    projectKey: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Project key (e.g., 'my-project'). Most commonly used identifier"
        ),
    ] = None,
    branch: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Branch name to check (e.g., 'main', 'develop')"
        ),
    ] = None,
    pullRequest: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Pull request ID to check (e.g., '123')"
        ),
    ] = None,
) -> QualityGateStatus:
    """Check whether a project/branch/PR passed its assigned quality gate and inspect failing conditions.

    Returns the quality gate status (PASSED, FAILED, ERROR, NONE) and details of any failing conditions.
    At least one of analysisId, projectId, or projectKey must be provided.

    Quality gate status values:
    - OK: All conditions passed
    - ERROR: One or more conditions failed
    - WARN: Warning threshold exceeded (deprecated)
    - NONE: No quality gate set

    Example: get_project_quality_gate_status(projectKey="my-project", pullRequest="123")
    """
    params: dict[str, Any] = {}

    if analysisId:
        params["analysisId"] = analysisId
    if projectId:
        params["projectId"] = projectId
    if projectKey:
        params["projectKey"] = projectKey
    if branch:
        params["branch"] = branch
    if pullRequest:
        params["pullRequest"] = pullRequest

    result = await make_request("/api/qualitygates/project_status", params=params)

    project_status = result.get("projectStatus", {})

    conditions = [
        QualityGateCondition(
            status=c["status"],
            metricKey=c["metricKey"],
            actualValue=c.get("actualValue"),
            errorThreshold=c.get("errorThreshold"),
        )
        for c in project_status.get("conditions", [])
    ]

    return QualityGateStatus(
        status=project_status.get("status", "NONE"),
        conditions=conditions,
    )


@mcp.tool()
async def list_quality_gates() -> dict[str, Any]:
    """Enumerate all gates in the organization along with basic metadata and built-in flags.

    Returns a list of all quality gates available in the organization, including their ID, name,
    and whether they are built-in or custom. Requires SONARCLOUD_ORGANIZATION to be set.

    Example: list_quality_gates()
    """
    config = require_organization("list_quality_gates")
    return await make_request("/api/qualitygates/list", config=config)


@mcp.tool()
async def show_quality_gate(
    name: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Quality gate name (e.g., 'Sonar way', 'My Custom Gate'). Either name or gate_id required"
        ),
    ] = None,
    gate_id: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Quality gate numeric ID. Either name or gate_id required"
        ),
    ] = None,
) -> dict[str, Any]:
    """Fetch full gate definition (conditions, allowed actions) so LLMs can explain or compare them.

    Returns detailed information about a specific quality gate, including all conditions (coverage thresholds,
    bug counts, etc.) and metadata. Requires SONARCLOUD_ORGANIZATION to be set.
    Either name or gate_id must be provided.

    Example: show_quality_gate(name="Sonar way")
    """
    if name is None and gate_id is None:
        raise ValueError("Either name or gate_id must be provided")

    config = require_organization("show_quality_gate")
    params: dict[str, Any] = {}

    if name:
        params["name"] = name
    if gate_id is not None:
        params["id"] = gate_id

    return await make_request("/api/qualitygates/show", params=params, config=config)


@mcp.tool()
async def search_quality_gates(
    gateId: Annotated[int, Field(description="Quality gate ID to search projects for. Get this from list_quality_gates()")],
    query: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Search query to filter project names (case-insensitive partial match)"
        ),
    ] = None,
    page: Annotated[int, Field(default=1, description="Page number (1-indexed)")] = 1,
    pageSize: Annotated[int, Field(default=100, description="Page size (max 500)")] = 100,
    selected: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Filter by association: true=only projects using this gate, false=only projects not using it, null=all projects"
        ),
    ] = None,
) -> dict[str, Any]:
    """Page through projects associated with a gate; supports filtering by selection status and name.

    Returns a list of projects and their association status with the specified quality gate.
    Useful for understanding which projects use which quality gates.
    Requires SONARCLOUD_ORGANIZATION to be set.

    Example: search_quality_gates(gateId=123, selected=True, query="my-project")
    """
    config = require_organization("search_quality_gates")
    params: dict[str, Any] = {
        "gateId": gateId,
        "page": page,
        "pageSize": pageSize,
    }

    if query:
        params["query"] = query
    if selected is not None:
        params["selected"] = "true" if selected else "false"

    return await make_request("/api/qualitygates/search", params=params, config=config)


@mcp.tool()
async def get_quality_gate_by_project(
    project: Annotated[str, Field(description="Project key to get quality gate for (e.g., 'my-project')")]
) -> dict[str, Any]:
    """Return the gate currently bound to a project so workflows can cross-reference status and rules.

    Returns information about which quality gate is assigned to the specified project.
    Use this to determine what quality criteria a project must meet.
    Requires SONARCLOUD_ORGANIZATION to be set.

    Example: get_quality_gate_by_project(project="my-project")
    """
    config = require_organization("get_quality_gate_by_project")
    params = {"project": project}
    return await make_request(
        "/api/qualitygates/get_by_project", params=params, config=config
    )


@mcp.tool()
async def search_hotspots(
    projectKey: Annotated[str, Field(description="Project key to search hotspots in (e.g., 'my-project')")],
    files: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Comma-separated list of file paths to filter by (e.g., 'src/main.java,src/util.java')"
        ),
    ] = None,
    branch: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Branch name to search (e.g., 'main', 'develop')"
        ),
    ] = None,
    pullRequest: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Pull request ID to search (e.g., '123')"
        ),
    ] = None,
    p: Annotated[int, Field(default=1, description="Page number (1-indexed)")] = 1,
    ps: Annotated[int, Field(default=100, description="Page size (max 500)")] = 100,
) -> dict[str, Any]:
    """List hotspots for a project with optional file, branch, or PR filters; returns paging + summaries.

    Security hotspots are security-sensitive pieces of code that need manual review.
    Returns a list of hotspots with their status, component, and vulnerability probability.

    Hotspot status values:
    - TO_REVIEW: Needs review
    - REVIEWED: Has been reviewed (with resolution FIXED, SAFE, or ACKNOWLEDGED)

    Example: search_hotspots(projectKey="my-project", branch="main", files="src/auth.java")
    """
    params: dict[str, Any] = {
        "projectKey": projectKey,
        "p": p,
        "ps": ps,
    }

    if files:
        params["files"] = files
    if branch:
        params["branch"] = branch
    if pullRequest:
        params["pullRequest"] = pullRequest

    result = await make_request("/api/hotspots/search", params=params)

    hotspots = [
        Hotspot(
            key=h["key"],
            component=h["component"],
            message=h["message"],
            author=h.get("author"),
            status=h["status"],
            resolution=h.get("resolution"),
            line=h.get("line"),
            vulnerabilityProbability=h.get("vulnerabilityProbability"),
        ).model_dump()
        for h in result.get("hotspots", [])
    ]

    paging_data = result.get("paging", {})

    return {
        "hotspots": hotspots,
        "paging": {
            "pageIndex": paging_data.get("pageIndex", 1),
            "pageSize": paging_data.get("pageSize", 100),
            "total": paging_data.get("total", 0),
        },
    }


@mcp.tool()
async def show_hotspot(
    hotspot: Annotated[str, Field(description="Hotspot key to retrieve details for (e.g., 'AXabc123def456')")]
) -> HotspotDetails:
    """Return the full hotspot payload (rule, component, author, status) for a specific key.

    Returns detailed information about a security hotspot, including the security rule that triggered it,
    the affected component/file, current status, resolution (if reviewed), and whether you can change its status.

    Example: show_hotspot(hotspot="AXabc123def456")
    """
    params = {"hotspot": hotspot}

    result = await make_request("/api/hotspots/show", params=params)

    return HotspotDetails(
        key=result["key"],
        message=result["message"],
        component=result["component"],
        status=result["status"],
        resolution=result.get("resolution"),
        author=result.get("author"),
        rule=result["rule"],
        canChangeStatus=result.get("canChangeStatus", False),
    )


@mcp.tool()
async def change_hotspot_status(
    hotspot: Annotated[str, Field(description="Hotspot key to change status for (e.g., 'AXabc123def456')")],
    status: Annotated[
        str,
        Field(
            description="New status for the hotspot. Valid values: 'TO_REVIEW' (mark for review), 'REVIEWED' (mark as reviewed, requires resolution parameter)"
        ),
    ],
    resolution: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Resolution when status='REVIEWED' (REQUIRED for REVIEWED status). Valid values: 'FIXED' (vulnerability has been fixed), 'SAFE' (code is safe, not a vulnerability), 'ACKNOWLEDGED' (risk is acknowledged but accepted). Not used when status='TO_REVIEW'"
        ),
    ] = None,
) -> dict[str, Any]:
    """Mark a hotspot TO_REVIEW or REVIEWED (with resolution) so downstream analyses see the new state.

    This updates the status of a security hotspot after manual review.

    Status values:
    - TO_REVIEW: Mark the hotspot as needing review (no resolution required)
    - REVIEWED: Mark as reviewed (resolution parameter is REQUIRED)

    Resolution values (required when status=REVIEWED):
    - FIXED: The vulnerability has been fixed
    - SAFE: The code is safe and not actually a vulnerability
    - ACKNOWLEDGED: The risk is acknowledged but accepted

    Examples:
    - Mark as reviewed and safe: change_hotspot_status(hotspot="AX123", status="REVIEWED", resolution="SAFE")
    - Mark for review: change_hotspot_status(hotspot="AX123", status="TO_REVIEW")
    """
    # Build form data
    body_params = {
        "hotspot": hotspot,
        "status": status,
    }

    if resolution and status == "REVIEWED":
        body_params["resolution"] = resolution

    body = urlencode(body_params)

    await make_request("/api/hotspots/change_status", method="POST", body=body)

    return {
        "success": True,
        "message": f"Hotspot {hotspot} status changed to {status}",
    }


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

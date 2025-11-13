# MCP SonarCloud Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)

A Model Context Protocol (MCP) server implementation for SonarCloud, providing tools to interact with SonarCloud projects, issues, quality gates, and security hotspots.

## Features

This MCP server provides 15 comprehensive tools with detailed parameter documentation and examples:

### Project Management (3 tools)
- **search_my_sonarqube_projects**: List all SonarCloud projects in your organization with pagination
- **show_component**: Get detailed metadata for a specific project or component
- **component_tree**: Traverse the file/directory structure of a project

### Issues (4 tools)
- **search_sonar_issues_in_projects**: Search for issues with filtering by pull request, severity (INFO, LOW, MEDIUM, HIGH, BLOCKER), and more
- **list_issue_authors**: Discover SCM authors who contributed to issues
- **get_issue_changelog**: Retrieve the change history of an issue
- **list_issue_tags**: List available tags used on issues

### Quality Gates (5 tools)
- **get_project_quality_gate_status**: Get the quality gate status (OK, ERROR, WARN, NONE) for a project, branch, or pull request
- **list_quality_gates**: List all quality gates in your organization
- **show_quality_gate**: Get detailed conditions for a specific quality gate
- **search_quality_gates**: Find projects associated with a quality gate
- **get_quality_gate_by_project**: Get the quality gate assigned to a project

### Security Hotspots (3 tools)
- **search_hotspots**: Search for security hotspots in a project with file, branch, or PR filters
- **show_hotspot**: Get detailed information about a specific hotspot
- **change_hotspot_status**: Change the status of a hotspot (TO_REVIEW or REVIEWED with resolution: FIXED, SAFE, ACKNOWLEDGED)

All tools include comprehensive parameter descriptions, valid value documentation, and usage examples for optimal AI agent integration.

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- A SonarCloud account with an API token
- Claude Code or Codex AI client

## Quick Start

### 1. Get Your SonarCloud Token

1. Log in to [SonarCloud](https://sonarcloud.io)
2. Click on your avatar → **My Account** → **Security**
3. Under "Generate Tokens", enter a name (e.g., "MCP Server")
4. Click **Generate**
5. **Copy and save the token** - you won't be able to see it again!

### 2. Find Your Organization Key

1. Go to your organization on SonarCloud
2. Look at the URL: `https://sonarcloud.io/organizations/YOUR-ORG-KEY`
3. The `YOUR-ORG-KEY` part is your organization key

### 3. Install the Server

```bash
# Clone the repository
git clone https://github.com/lukleh/mcp-sonarcloud.git
cd mcp-sonarcloud

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### 4. Configure Your AI Client

**Claude Code:**

```bash
claude mcp add sonarcloud \
  --scope {local, user, or project} \
  -e SONARCLOUD_TOKEN=your-token-here \
  -e SONARCLOUD_ORGANIZATION=your-org-key \
  -- uv --directory /absolute/path/to/mcp-sonarcloud run mcp-sonarcloud
```

**Codex:**

```bash
codex mcp add sonarcloud \
  --env SONARCLOUD_TOKEN=your-token-here \
  --env SONARCLOUD_ORGANIZATION=your-org-key \
  -- uv --directory /absolute/path/to/mcp-sonarcloud run mcp-sonarcloud
```

**Important**: Replace:
- `/absolute/path/to/mcp-sonarcloud` with the actual full path
- `your-token-here` with your SonarCloud token
- `your-org-key` with your organization key

### 5. Restart and Test

1. Restart your AI client
2. Try asking: "Can you list my SonarCloud projects?"

## Detailed Installation

If you've already completed the Quick Start, you can skip to [Usage Examples](#usage-examples).

### Using uv (recommended)

```bash
git clone https://github.com/lukleh/mcp-sonarcloud.git
cd mcp-sonarcloud
uv sync
```

### Using pip

```bash
pip install -e .
```

### Environment Variables

The server requires the following environment variables:

- `SONARCLOUD_TOKEN` (required): Your SonarCloud authentication token
- `SONARCLOUD_ORGANIZATION` (optional): Your SonarCloud organization key
- `SONARCLOUD_URL` (optional): SonarCloud base URL (defaults to `https://sonarcloud.io`)

### Command Line Testing

You can test the server directly:

```bash
# Set environment variables
export SONARCLOUD_TOKEN="your-token"
export SONARCLOUD_ORGANIZATION="your-org"

# Run the server
uv run mcp-sonarcloud
```

## Usage Examples

### Natural Language Queries

Once configured, you can ask your AI client:

1. **List projects**: "Show me all my SonarCloud projects"
2. **Check quality gate**: "What's the quality gate status for project X on PR 123?"
3. **Search hotspots**: "Find all security hotspots in project X"
4. **Get hotspot details**: "Show me details for hotspot AY1234567890"
5. **Update hotspot**: "Mark hotspot AY1234567890 as reviewed and safe"
6. **Search issues**: "Find all blocker issues in project X's pull request 123"

### Tool Examples (Python)

### List Projects

```python
# Get first page of projects
search_my_sonarqube_projects(page="1")
```

### Search Issues in Pull Request

```python
# Search for issues in a specific pull request
search_sonar_issues_in_projects(
    projects=["my-project"],
    pullRequestId="123",
    ps=100
)
```

### Check Quality Gate Status

```python
# Get quality gate status for a pull request
get_project_quality_gate_status(
    projectKey="my-project",
    pullRequest="123"
)
```

### Search Security Hotspots

```python
# Search hotspots in a project
search_hotspots(
    projectKey="my-project",
    pullRequest="123"
)

# Search hotspots in a specific file
search_hotspots(
    projectKey="my-project",
    files="src/main/java/com/example/MyClass.java",
    branch="main"
)
```

### Get Hotspot Details

```python
# Get detailed information about a hotspot
show_hotspot(hotspot="AX1234567890")
```

### Change Hotspot Status

```python
# Mark a hotspot as reviewed and safe
change_hotspot_status(
    hotspot="AX1234567890",
    status="REVIEWED",
    resolution="SAFE"
)

# Mark a hotspot for review
change_hotspot_status(
    hotspot="AX1234567890",
    status="TO_REVIEW"
)
```

**Valid status values:**
- `TO_REVIEW`: Mark for review
- `REVIEWED`: Mark as reviewed (requires resolution)

**Valid resolution values (when status=REVIEWED):**
- `FIXED`: The vulnerability has been fixed
- `SAFE`: The code is safe and not a vulnerability
- `ACKNOWLEDGED`: The risk is acknowledged but accepted

## Troubleshooting

### Common Issues

**"No module named mcp_sonarcloud"**
- Make sure you're using the full absolute path in the config
- Verify you ran `uv pip install -e .` in the project directory

**"SONARCLOUD_TOKEN environment variable is required"**
- Double-check your token is correctly set in the environment variables
- Verify there are no extra spaces or quotes around the token

**"401 Unauthorized"**
- Your token might be invalid or expired
- Generate a new token from SonarCloud and update your configuration

**MCP server not available**
- Verify the server was added: `claude mcp list` or `codex mcp list`
- Check that the path to mcp-sonarcloud is correct and absolute
- Try removing and re-adding the server
- Check your AI client logs for errors

## API Endpoints Used

This server uses the following SonarCloud API endpoints:

### Components / Projects
- `GET /api/components/search` - List projects
- `GET /api/components/show` - Show component metadata
- `GET /api/components/tree` - Traverse component hierarchy

### Issues
- `GET /api/issues/search` - Search issues
- `GET /api/issues/authors` - List issue authors
- `GET /api/issues/changelog` - Get issue change history
- `GET /api/issues/tags` - List issue tags

### Quality Gates
- `GET /api/qualitygates/project_status` - Get quality gate status
- `GET /api/qualitygates/list` - List quality gates
- `GET /api/qualitygates/show` - Show quality gate details
- `GET /api/qualitygates/search` - Search projects by quality gate
- `GET /api/qualitygates/get_by_project` - Get quality gate for project

### Security Hotspots
- `GET /api/hotspots/search` - Search security hotspots
- `GET /api/hotspots/show` - Show hotspot details
- `POST /api/hotspots/change_status` - Change hotspot status

For complete API documentation, see [SONARCLOUD_API_SUPPORT.md](SONARCLOUD_API_SUPPORT.md).

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details

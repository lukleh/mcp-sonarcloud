# Development Notes

## Implementation Details

### Architecture

This MCP server is built using the FastMCP framework from the MCP Python SDK. The architecture follows a simple, straightforward approach:

```
src/mcp_sonarcloud/
├── __init__.py      # Package initialization
└── server.py        # Main server with all tools
```

### API Endpoints Mapping

The server implements 15 tools that map to these SonarCloud API endpoints:

| Tool Name | API Endpoint | HTTP Method | Purpose |
|-----------|--------------|-------------|---------|
| **Components/Projects** | | | |
| `search_my_sonarqube_projects` | `/api/components/search` | GET | List projects |
| `show_component` | `/api/components/show` | GET | Show component metadata |
| `component_tree` | `/api/components/tree` | GET | Traverse component hierarchy |
| **Issues** | | | |
| `search_sonar_issues_in_projects` | `/api/issues/search` | GET | Search issues |
| `list_issue_authors` | `/api/issues/authors` | GET | List issue authors |
| `get_issue_changelog` | `/api/issues/changelog` | GET | Get issue change history |
| `list_issue_tags` | `/api/issues/tags` | GET | List issue tags |
| **Quality Gates** | | | |
| `get_project_quality_gate_status` | `/api/qualitygates/project_status` | GET | Get QG status |
| `list_quality_gates` | `/api/qualitygates/list` | GET | List quality gates |
| `show_quality_gate` | `/api/qualitygates/show` | GET | Show quality gate details |
| `search_quality_gates` | `/api/qualitygates/search` | GET | Search projects by QG |
| `get_quality_gate_by_project` | `/api/qualitygates/get_by_project` | GET | Get QG for project |
| **Security Hotspots** | | | |
| `search_hotspots` | `/api/hotspots/search` | GET | Search hotspots |
| `show_hotspot` | `/api/hotspots/show` | GET | Get hotspot details |
| `change_hotspot_status` | `/api/hotspots/change_status` | POST | Update hotspot status |

### Authentication

The server uses Bearer token authentication:
- Token is provided via `SONARCLOUD_TOKEN` environment variable
- Each request includes: `Authorization: Bearer <token>` header
- Organization is automatically added to requests if `SONARCLOUD_ORGANIZATION` is set

### Design Decisions

1. **Single File Implementation**: All code is in one file for simplicity and easy understanding
2. **Pydantic Models**: Used for type safety and automatic validation of responses
3. **Pydantic Field Annotations**: All tool parameters use Field() with comprehensive descriptions, valid values, formats, and examples for optimal LLM consumption
4. **Async/Await**: All API calls are asynchronous for better performance
5. **Environment-Based Config**: No config files needed, just environment variables
6. **Structured Responses**: Tools return structured data (Pydantic models or dicts) instead of raw JSON
7. **LLM-First Documentation**: Every tool includes examples and explicit documentation of valid values to minimize trial-and-error by AI agents

### Hotspots API Research

The hotspots API was not well-documented publicly, but through research:

1. **Source**: Analyzed SonarLint Core Java implementation
2. **Endpoints Found**:
   - `/api/hotspots/search.protobuf` - Returns protobuf format
   - `/api/hotspots/show.protobuf` - Returns protobuf format
   - `/api/hotspots/change_status` - Form-encoded POST
   - We use the JSON versions (without `.protobuf`)

3. **Status Values**:
   - `TO_REVIEW`: Hotspot needs review
   - `REVIEWED`: Hotspot has been reviewed

4. **Resolution Values** (when status=REVIEWED):
   - `FIXED`: Vulnerability was fixed
   - `SAFE`: Code is safe, not a vulnerability
   - `ACKNOWLEDGED`: Risk is accepted

### Testing Strategy

Tests use `pytest-httpx` to mock HTTP requests:
- Each test mocks the expected API response
- Tests verify both the request format and response parsing
- All tests run without requiring actual SonarCloud credentials

### Comparison with Official Server

| Feature | This Implementation | Official SonarSource Server |
|---------|-------------------|---------------------------|
| Language | Python | Kotlin/Java |
| Lines of Code | ~730 | ~5000+ |
| Tools Count | 15 tools | ~10 tools |
| Hotspot Support | ✅ Full (search, show, change status) | ❌ Missing |
| Quality Gates | ✅ Full (5 tools) | ⚠️ Partial |
| Issues API | ✅ Good (4 tools) | ✅ Yes |
| LLM Documentation | ✅ Comprehensive Field annotations | ⚠️ Basic |
| Code Analysis | ❌ No | ✅ Yes |
| Dependency Risks | ❌ No | ✅ Yes |
| Metrics Search | ❌ No | ✅ Yes |
| Ease of Modification | ✅ Very Easy | ⚠️ Complex |

### Future Enhancements

Potential additions:
1. Add caching for frequently accessed data
2. Support batch operations on hotspots
3. Add more filtering options for issues/hotspots
4. Support for SonarQube Server (not just SonarCloud)
5. Add telemetry/metrics collection
6. Support for SSE transport in addition to stdio

### Known Limitations

1. **No Pagination Automation**: Users must manually page through large result sets
2. **Organization Required**: Works best with SonarCloud organizations
3. **No Rate Limiting**: No built-in rate limiting protection
4. **Limited Error Context**: HTTP errors could be more descriptive
5. **No Retry Logic**: Failed requests are not automatically retried

### Contributing Guidelines

When adding new tools:

1. Add the tool function with `@mcp.tool()` decorator
2. Use type hints and Pydantic `Field()` annotations for all parameters
3. Document valid values, formats, and provide examples in Field descriptions
4. Create a Pydantic model for structured responses if needed
5. Add comprehensive docstring with examples and parameter relationships
6. Write tests for the new tool in `tests/test_server.py`
7. Update README.md and SONARCLOUD_API_SUPPORT.md

Example:
```python
@mcp.tool()
async def new_tool(
    param: str = Field(
        description="Parameter description with example (e.g., 'my-value')"
    ),
    status: str = Field(
        description="Status value. Valid values: 'OPEN', 'CLOSED', 'PENDING'"
    ),
    optional_param: Optional[int] = Field(
        default=None,
        description="Optional parameter (e.g., 123)"
    ),
) -> ResponseModel:
    """Tool description explaining what it does and when to use it.

    Provide context about the tool's purpose, what data it returns,
    and any important constraints or requirements.

    Example: new_tool(param="my-project", status="OPEN", optional_param=100)
    """
    result = await make_request("/api/endpoint", params={"param": param})
    return ResponseModel(**result)
```

**Key Documentation Requirements:**
- Use `Field()` for ALL parameters (including required ones)
- Document valid enum values explicitly (e.g., "Valid values: 'X', 'Y', 'Z'")
- Specify format for complex inputs (e.g., "comma-separated list")
- Include concrete examples in descriptions (e.g., "e.g., 'my-project'")
- Add usage example in docstring showing realistic parameters
- Explain parameter relationships (e.g., "required when X is Y")
- State what the tool returns in the docstring

## Debugging

To debug the server:

```bash
# Enable verbose logging
export SONARCLOUD_TOKEN=your-token
export SONARCLOUD_ORGANIZATION=your-org

# Run with MCP inspector for interactive debugging
uvx mcp-inspector uv run mcp-sonarcloud
```

## Performance Considerations

- All API calls use httpx's async client for concurrency
- Connection pooling is handled by httpx automatically
- Timeout is set to 30 seconds for all requests
- Consider implementing caching for frequently accessed data

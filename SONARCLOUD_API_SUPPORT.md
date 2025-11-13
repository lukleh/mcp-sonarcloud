# SonarCloud Web API Coverage (as of November 13, 2025)

This note verifies that the MCP SonarCloud server (`src/mcp_sonarcloud/server.py`) interacts only with endpoints documented under the public SonarQube/SonarCloud Web API program described at [api-docs.sonarsource.com](https://api-docs.sonarsource.com/sonarqube-cloud/default/landing). When a documented method is not implemented, it is explicitly called out so we can decide whether to add it later.

## Tool Documentation Quality

All implemented tools include comprehensive Pydantic `Field` annotations with:
- **Valid value documentation** for enum-like parameters (e.g., severity levels: INFO, LOW, MEDIUM, HIGH, BLOCKER)
- **Format specifications** for parameters (e.g., comma-separated lists, key formats)
- **Parameter relationships** explicitly stated (e.g., "at least one of X, Y, or Z required")
- **Usage examples** in docstrings showing common patterns
- **Return value descriptions** explaining what data is returned

This makes the MCP server highly consumable by LLM agents, who can understand valid inputs and usage patterns without trial-and-error.

## Reading the tables
- **Doc expectation** is a paraphrase of the official behavior for each REST method.
- **Supported?** indicates whether the MCP server currently calls the endpoint.
- **Implementation / Notes** highlights the relevant tool function or explains the gap.

### Components / Projects API
| Endpoint | HTTP Verb | Doc Expectation | Supported? | Implementation / Notes |
| --- | --- | --- | --- | --- |
| `/api/components/search` | GET | Find projects/components by key, name, or search query; accepts `organization`, paging, and qualifiers. | ✅ | `search_my_sonarqube_projects` builds the search query and injects organization/qualifiers (`src/mcp_sonarcloud/server.py`). |
| `/api/components/show` | GET | Return component metadata (key, name, qualifier, tags). | ✅ | `show_component` exposes this metadata lookup (`src/mcp_sonarcloud/server.py`). |
| `/api/components/tree` | GET | Traverse the component hierarchy for a project or module. | ✅ | `component_tree` supports qualifiers, paging, sorting (`src/mcp_sonarcloud/server.py`). |

### Issues API
| Endpoint | HTTP Verb | Doc Expectation | Supported? | Implementation / Notes |
| --- | --- | --- | --- | --- |
| `/api/issues/search` | GET | Search issues with filters for project(s), severity, PR, branch, etc. | ✅ | `search_sonar_issues_in_projects` covers paging, project filters, PRs, and severity inputs (`src/mcp_sonarcloud/server.py`). |
| `/api/issues/add_comment` | POST | Add a textual comment to the specified issue. | ❌ | Not surfaced; would need user-supplied comment text and issue key plus write permissions. |
| `/api/issues/assign` | POST | Assign or reassign an issue to a user. | ❌ | No tooling yet; keep in mind it requires user identity resolution. |
| `/api/issues/authors` | GET | List authors for issues of a project. | ✅ | `list_issue_authors` wraps the read-only authors index and enforces org requirement. |
| `/api/issues/bulk_change` | POST | Apply transitions or mass edits to multiple issues. | ❌ | Not exposed to avoid accidental sweeping changes. |
| `/api/issues/changelog` | GET | Retrieve an issue’s history. | ✅ | `get_issue_changelog` provides the history feed for a given issue key. |
| `/api/issues/delete_comment` | POST | Remove a comment by its identifier. | ❌ | Not implemented. |
| `/api/issues/do_transition` | POST | Transition an issue (e.g., confirm, resolve). | ❌ | Not implemented to avoid state mutations. |
| `/api/issues/edit_comment` | POST | Edit an existing comment. | ❌ | Not implemented. |
| `/api/issues/set_severity` | POST | Change the severity of an issue. | ❌ | Not implemented. |
| `/api/issues/set_tags` | POST | Replace tags on an issue. | ❌ | Not implemented. |
| `/api/issues/set_type` | POST | Update issue type (bug, vulnerability, code smell). | ❌ | Not implemented. |
| `/api/issues/tags` | GET | List tags used by issues. | ✅ | `list_issue_tags` exposes the tag catalog with optional filtering. |

### Quality Gates API
| Endpoint | HTTP Verb | Doc Expectation | Supported? | Implementation / Notes |
| --- | --- | --- | --- | --- |
| `/api/qualitygates/project_status` | GET | Return the computed quality gate status for a project, branch, PR, or analysisId. | ✅ | `get_project_quality_gate_status` lets the caller pass `analysisId`, project identifiers, branch, or PR (`src/mcp_sonarcloud/server.py`). |
| `/api/qualitygates/list` | GET | List all available quality gates. | ✅ | `list_quality_gates` lists gates for the configured organization. |
| `/api/qualitygates/show` | GET | Show conditions for a single gate. | ✅ | `show_quality_gate` fetches gate metadata by name or ID. |
| `/api/qualitygates/search` | GET | Search for projects linked (or not) to a quality gate. | ✅ | `search_quality_gates` proxies the gate association search (requires `gateId`). |
| `/api/qualitygates/create`, `/copy`, `/rename`, `/destroy`, `/select`, `/deselect`, `/set_as_default`, `/unset_default`, `/create_condition`, `/update_condition`, `/delete_condition` | POST | Manage gates and conditions. | ❌ | No write operations are exposed to avoid destructive changes via MCP. |
| `/api/qualitygates/get_by_project` | GET | Resolve which gate is linked to a project. | ✅ | `get_quality_gate_by_project` exposes this lookup for project keys. |

### Security Hotspots API
| Endpoint | HTTP Verb | Doc Expectation | Supported? | Implementation / Notes |
| --- | --- | --- | --- | --- |
| `/api/hotspots/search` | GET | Search hotspots by project key, optional file filters, status, or branch. | ✅ | `search_hotspots` exposes `projectKey`, optional `files`, `branch`, `pullRequest`, paging (`src/mcp_sonarcloud/server.py`). |
| `/api/hotspots/show` | GET | Fetch full hotspot details (message, component, rule). | ✅ | `show_hotspot` wraps this GET with typed response (`src/mcp_sonarcloud/server.py`). |
| `/api/hotspots/change_status` | POST | Mark hotspot as TO_REVIEW or REVIEWED with optional resolution comment. | ✅ | `change_hotspot_status` posts form data with `hotspot`, `status`, `resolution` when required (`src/mcp_sonarcloud/server.py`). |

## Observations
1. All supported endpoints match the authentication and usage guidance published by SonarSource for Web API v1; we consistently supply the user token via `Authorization: Bearer` per the docs.
2. The MCP server deliberately omits every mutating Issues or Quality Gates method to avoid unreviewed side effects; if needed, each missing row can guide future tool additions.
3. Coverage is strongest for read-only workflows (projects, issues search, quality gates status, hotspots triage); write-heavy workflows remain manual.
4. All 15 implemented tools include comprehensive parameter documentation with valid values, formats, examples, and constraints, making them highly consumable by LLM agents without requiring external documentation lookup.

# Releasing `mcp-sonarcloud`

This project is set up for tag-driven PyPI releases with GitHub Actions and PyPI trusted publishing.

## One-time PyPI setup

1. Create the `mcp-sonarcloud` project on PyPI if it does not exist yet.
2. In PyPI, add a trusted publisher for this repository:
   - Owner: `lukleh`
   - Repository: `mcp-sonarcloud`
   - Workflow: `publish.yml`
   - Environment: `pypi`
3. In GitHub, create an environment named `pypi` if you want environment protection or manual approvals.

## Release steps

1. Update `version` in `pyproject.toml`.
2. Commit the release changes to `main`.
3. Create and push a matching version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

4. GitHub Actions will:
   - run tests
   - build the wheel and sdist
   - smoke test both artifacts with `uvx`
   - publish to PyPI

## Notes

- The publish workflow validates that the Git tag matches `pyproject.toml`.
- The smoke tests exercise the packaged CLI by writing a sample config and printing runtime paths from the built artifacts.

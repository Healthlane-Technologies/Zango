# Zango — Claude Code Guidelines

## Version Update Checklist

When bumping the Zango version (e.g. releasing a new beta or patch), update **all three** of the following files:

### 1. `backend/setup.py`
```python
PLATFORM_VERSION = "1.2.0b2"  # ← update here
```

### 2. `backend/src/zango/__init__.py`
```python
__version__ = "1.2.0b2"  # ← update here
```

### 3. `CHANGELOG.md`
Add a new section at the top (below the `# Changelog` header) following the existing format:

```markdown
## [1.2.0b2] - YYYY-MM-DD

### Added
* ...

### Fixed
* ...

### Changed
* ...
```

**Steps:**
1. Check merged PRs since the last release: `gh pr list --state merged --limit 20`
2. Group changes into Added / Fixed / Changed — keep notes crisp and one line each
3. Link each entry to its PR: `[(#NNN)](https://github.com/Healthlane-Technologies/Zango/pull/NNN)`
4. Update the two version strings and the changelog

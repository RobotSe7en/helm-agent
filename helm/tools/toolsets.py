from __future__ import annotations


DEFAULT_TOOLSETS: dict[str, list[str]] = {
    "filesystem": ["filesystem.list", "filesystem.read", "filesystem.write"],
    "shell": ["shell.run"],
    "git": ["git.status", "git.diff"],
    "delegation": ["delegate_task"],
}


def expand_toolsets(toolsets: list[str]) -> list[str]:
    names: list[str] = []
    for item in toolsets:
        if item in DEFAULT_TOOLSETS:
            names.extend(DEFAULT_TOOLSETS[item])
        else:
            names.append(item)
    return list(dict.fromkeys(names))

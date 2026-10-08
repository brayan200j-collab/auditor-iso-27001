from __future__ import annotations

from pathlib import Path
from string import Template


class FilePromptTemplates:
    """Prompts live in `prompts/<version>/*.md`, never in code. `$name` placeholders are filled in
    a single pass, so text coming from documents is never re-interpreted as a placeholder."""

    def __init__(self, prompts_dir: Path, version: str = "v1") -> None:
        folder = prompts_dir / version
        self.version = version
        self._system = (folder / "system.md").read_text(encoding="utf-8").strip()
        self._evaluation = Template((folder / "evaluation.md").read_text(encoding="utf-8"))

    def system(self) -> str:
        return self._system

    def evaluation(self, values: dict[str, str]) -> str:
        return self._evaluation.substitute(values)

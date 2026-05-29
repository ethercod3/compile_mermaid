from __future__ import annotations

from pathlib import Path

import compile_mermaid.cli as cli


def test_cli_passes_paths_and_no_crop(monkeypatch, tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    captured = {}

    def fake_run(config):
        captured["config"] = config
        return 0

    monkeypatch.setattr(cli, "run", fake_run)

    assert cli.main(["--src", str(src), "--dst", str(dst), "--no-crop", "--max-workers", "2"]) == 0

    config = captured["config"]
    assert config.src == src
    assert config.dst == dst
    assert config.no_crop is True
    assert config.max_workers == 2

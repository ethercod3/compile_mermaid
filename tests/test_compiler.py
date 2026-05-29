from __future__ import annotations

import os
from pathlib import Path

import compile_mermaid.compiler as compiler
from compile_mermaid.compiler import CompileConfig


def test_process_file_crops_generated_pdf(monkeypatch, tmp_path: Path) -> None:
    src = tmp_path / "diagram.mmd"
    out_dir = tmp_path / "figures"
    src.write_text("flowchart TD\nA-->B\n", encoding="utf-8")
    out_dir.mkdir()

    calls: list[tuple[str, ...]] = []

    def fake_run(command: list[str], timeout: int = 0) -> tuple[int, str, str]:
        calls.append(tuple(command))
        if command[0] == "mmdc":
            Path(command[4]).write_text("generated", encoding="utf-8")
        if command[0] == "pdfcrop":
            Path(command[2]).write_text("cropped", encoding="utf-8")
        return 0, "", ""

    monkeypatch.setattr(compiler, "run_external", fake_run)

    result = compiler.process_file(src, out_dir, ["mmdc"], ["pdfcrop"])

    assert result == "[OK] diagram.mmd -> diagram.pdf"
    assert (out_dir / "diagram.pdf").read_text(encoding="utf-8") == "cropped"
    assert calls == [
        ("mmdc", "-i", str(src), "-o", str(out_dir / "diagram.pdf"), "-f"),
        ("pdfcrop", str(out_dir / "diagram.pdf"), str(out_dir / "diagram.pdfcrop-tmp.pdf")),
    ]


def test_process_file_can_skip_crop(monkeypatch, tmp_path: Path) -> None:
    src = tmp_path / "diagram.mmd"
    out_dir = tmp_path / "figures"
    src.write_text("flowchart TD\nA-->B\n", encoding="utf-8")
    out_dir.mkdir()

    calls: list[tuple[str, ...]] = []

    def fake_run(command: list[str], timeout: int = 0) -> tuple[int, str, str]:
        calls.append(tuple(command))
        Path(command[4]).write_text("generated", encoding="utf-8")
        return 0, "", ""

    monkeypatch.setattr(compiler, "run_external", fake_run)

    result = compiler.process_file(src, out_dir, ["mmdc"], None)

    assert result == "[OK] diagram.mmd -> diagram.pdf"
    assert (out_dir / "diagram.pdf").read_text(encoding="utf-8") == "generated"
    assert calls == [("mmdc", "-i", str(src), "-o", str(out_dir / "diagram.pdf"), "-f")]


def test_run_returns_error_when_any_diagram_fails(monkeypatch, tmp_path: Path) -> None:
    src_dir = tmp_path / "mermaid"
    out_dir = tmp_path / "figures"
    src_dir.mkdir()
    src = src_dir / "broken.mmd"
    src.write_text("flowchart TD\nA-->B\n", encoding="utf-8")

    monkeypatch.setattr(compiler, "find_mmdc", lambda: ["mmdc"])
    monkeypatch.setattr(compiler, "find_pdfcrop", lambda: ["pdfcrop"])
    monkeypatch.setattr(
        compiler,
        "process_file",
        lambda f, dst, mmdc, pdfcrop: f"[ERROR] Failed to compile diagram {f.name}",
    )

    assert compiler.run(CompileConfig(src=src_dir, dst=out_dir)) == 1


def test_run_skips_diagrams_when_pdf_is_newer(monkeypatch, tmp_path: Path, capsys) -> None:
    src_dir = tmp_path / "mermaid"
    out_dir = tmp_path / "figures"
    src_dir.mkdir()
    out_dir.mkdir()
    src = src_dir / "diagram.mmd"
    pdf = out_dir / "diagram.pdf"
    src.write_text("flowchart TD\nA-->B\n", encoding="utf-8")
    pdf.write_text("generated", encoding="utf-8")
    os.utime(src, (100, 100))
    os.utime(pdf, (200, 200))

    monkeypatch.setattr(
        compiler,
        "find_mmdc",
        lambda: (_ for _ in ()).throw(AssertionError("mmdc should not be looked up")),
    )

    assert compiler.run(CompileConfig(src=src_dir, dst=out_dir)) == 0
    assert "up to date" in capsys.readouterr().out


def test_run_compiles_newer_diagrams(monkeypatch, tmp_path: Path) -> None:
    src_dir = tmp_path / "mermaid"
    out_dir = tmp_path / "figures"
    src_dir.mkdir()
    out_dir.mkdir()
    src = src_dir / "diagram.mmd"
    pdf = out_dir / "diagram.pdf"
    src.write_text("flowchart TD\nA-->B\n", encoding="utf-8")
    pdf.write_text("old", encoding="utf-8")
    os.utime(src, (200, 200))
    os.utime(pdf, (100, 100))

    calls: list[Path] = []

    monkeypatch.setattr(compiler, "find_mmdc", lambda: ["mmdc"])
    monkeypatch.setattr(compiler, "process_file", lambda f, dst, mmdc, pdfcrop: calls.append(f) or "[OK] done")

    assert compiler.run(CompileConfig(src=src_dir, dst=out_dir, no_crop=True)) == 0
    assert calls == [src]


def test_run_force_compiles_up_to_date_diagrams(monkeypatch, tmp_path: Path) -> None:
    src_dir = tmp_path / "mermaid"
    out_dir = tmp_path / "figures"
    src_dir.mkdir()
    out_dir.mkdir()
    src = src_dir / "diagram.mmd"
    pdf = out_dir / "diagram.pdf"
    src.write_text("flowchart TD\nA-->B\n", encoding="utf-8")
    pdf.write_text("generated", encoding="utf-8")
    os.utime(src, (100, 100))
    os.utime(pdf, (200, 200))

    calls: list[Path] = []

    monkeypatch.setattr(compiler, "find_mmdc", lambda: ["mmdc"])
    monkeypatch.setattr(compiler, "process_file", lambda f, dst, mmdc, pdfcrop: calls.append(f) or "[OK] done")

    assert compiler.run(CompileConfig(src=src_dir, dst=out_dir, no_crop=True, force=True)) == 0
    assert calls == [src]

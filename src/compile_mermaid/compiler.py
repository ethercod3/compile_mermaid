from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

EXTENSIONS = {".mmd", ".mermaid", ".mmdc"}
MAX_WORKERS_LIMIT = 4
TIMEOUT_SECONDS = 60


class CompileError(RuntimeError):
    pass


@dataclass(frozen=True)
class CompileConfig:
    src: Path = Path("mermaid")
    dst: Path = Path("figures")
    no_crop: bool = False
    force: bool = False
    max_workers: int = MAX_WORKERS_LIMIT


def command_path(command: str) -> str | None:
    return shutil.which(command)


def find_mmdc() -> list[str]:
    mmdc = command_path("mmdc") or command_path("mmdc.cmd")
    if mmdc is None:
        raise CompileError(
            "Не найдена программа mmdc для сборки Mermaid-диаграмм. "
            "Установите Mermaid CLI и убедитесь, что команда 'mmdc' доступна в терминале."
        )

    return [mmdc]


def find_pdfcrop() -> list[str]:
    pdfcrop = command_path("pdfcrop") or command_path("pdfcrop.cmd")
    if pdfcrop is None:
        raise CompileError(
            "Не найдена программа pdfcrop для обрезки Mermaid-диаграмм. "
            "Установите TeX Live/MiKTeX с pdfcrop или запустите скрипт с флагом --no-crop."
        )

    return [pdfcrop]


def run_external(command: list[str], timeout: int = TIMEOUT_SECONDS) -> tuple[int, str, str]:
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


def crop_pdf(output_file: Path, pdfcrop: list[str]) -> None:
    cropped_file = output_file.with_name(f"{output_file.stem}.pdfcrop-tmp{output_file.suffix}")
    cmd = [*pdfcrop, str(output_file), str(cropped_file)]

    try:
        code, stdout, stderr = run_external(cmd)
        if code != 0:
            details = (stderr or stdout).strip()
            raise CompileError(f"Не удалось обрезать Mermaid-PDF.\nКоманда: {' '.join(cmd)}\n{details}")
        os.replace(cropped_file, output_file)
    finally:
        if cropped_file.exists():
            cropped_file.unlink()


def process_file(f: Path, dst: Path, mmdc: list[str], pdfcrop: list[str] | None) -> str | None:
    if not f.is_file():
        return None

    if f.suffix.lower() not in EXTENSIONS:
        return None

    output_file = dst / f"{f.stem}.pdf"
    cmd = [*mmdc, "-i", str(f), "-o", str(output_file), "-f"]

    code, stdout, stderr = run_external(cmd)
    if code != 0:
        details = (stderr or stdout).strip()
        return (
            f"[ОШИБКА] Не удалось собрать диаграмму {f.name}\n"
            f"Команда: {' '.join(cmd)}\n"
            f"Обычный вывод:\n{stdout.strip() or 'вывода нет'}\n"
            f"Вывод ошибок:\n{details or 'вывода ошибок нет'}"
        )

    if pdfcrop is not None:
        crop_pdf(output_file, pdfcrop)

    return f"[OK] {f.name} -> {output_file.name}"


def output_path(src_file: Path, dst: Path) -> Path:
    return dst / f"{src_file.stem}.pdf"


def needs_compile(src_file: Path, dst: Path) -> bool:
    pdf_file = output_path(src_file, dst)
    if not pdf_file.exists():
        return True

    return src_file.stat().st_mtime > pdf_file.stat().st_mtime


def run(config: CompileConfig | None = None) -> int:
    config = config or CompileConfig()
    src = config.src.resolve()
    dst = config.dst.resolve()

    if not src.exists():
        raise CompileError(f"Папка с Mermaid-диаграммами не найдена: {src}")

    dst.mkdir(parents=True, exist_ok=True)
    files = [f for f in src.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONS]

    if not files:
        print(f"В папке {src} не найдены Mermaid-файлы для сборки.")
        return 0

    files_to_compile = files if config.force else [f for f in files if needs_compile(f, dst)]

    if not files_to_compile:
        print("Все Mermaid-диаграммы уже актуальны.")
        return 0

    mmdc = find_mmdc()
    pdfcrop = None if config.no_crop else find_pdfcrop()

    max_workers = min(max(1, config.max_workers), len(files_to_compile))
    has_errors = False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f, dst, mmdc, pdfcrop): f for f in files_to_compile}

        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    print(result)
                    if result.startswith("[ОШИБКА]"):
                        has_errors = True
            except Exception as error:
                f = futures[future]
                print(f"[ОШИБКА] Не удалось обработать {f.name}: {error}")
                has_errors = True

    return 1 if has_errors else 0

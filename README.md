# compile-mermaid

Small CLI for compiling Mermaid diagram sources into PDF files.

## Usage

From a project that contains `mermaid/` and `figures/`:

```powershell
uvx --from git+https://github.com/ethercod3/compile_mermaid.git compile-mermaid
```

For local development from this repository:

```powershell
uvx --from . compile-mermaid
```

Options:

```text
--src PATH       Source directory with .mmd/.mermaid/.mmdc files. Default: mermaid
--dst PATH       Output directory for generated PDFs. Default: figures
--no-crop        Skip pdfcrop after mmdc generation.
--force          Rebuild all diagrams, even when PDFs are up to date.
--max-workers N  Maximum parallel workers. Default: 4
```

By default, `compile-mermaid` skips a source file when its output PDF already
exists and is newer than or the same age as the source. Use `--force` to rebuild
all diagrams.

External tools must be available in `PATH`:

- `mmdc` from Mermaid CLI
- `pdfcrop` for cropping, unless `--no-crop` is used

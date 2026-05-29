# compile-mermaid

Small CLI for compiling Mermaid diagram sources into PDF files.

## Usage

From a project that contains `mermaid/` and `figures/`:

```powershell
uvx --from ./compile_mermaid compile-mermaid
```

From another project:

```powershell
uvx --from ../compile_mermaid compile-mermaid
```

Options:

```text
--src PATH       Source directory with .mmd/.mermaid/.mmdc files. Default: mermaid
--dst PATH       Output directory for generated PDFs. Default: figures
--no-crop        Skip pdfcrop after mmdc generation.
--max-workers N  Maximum parallel workers. Default: 4
```

External tools must be available in `PATH`:

- `mmdc` from Mermaid CLI
- `pdfcrop` for cropping, unless `--no-crop` is used

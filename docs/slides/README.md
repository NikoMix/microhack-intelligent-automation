# Slides — Marp deck

The course deck is authored in **[Marp](https://marp.app/)** (Markdown Presentation
Ecosystem, MIT-licensed — no paid tooling). Source: [`slides.md`](slides.md).

## Render / present

### VS Code (recommended)
1. Install the **Marp for VS Code** extension.
2. Open `slides.md` → click the preview icon → *Present* or *Export*.

### CLI (no install beyond npx)

```bash
# HTML (self-contained)
npx @marp-team/marp-cli@latest docs/slides/slides.md -o docs/slides/slides.html

# PDF
npx @marp-team/marp-cli@latest docs/slides/slides.md --pdf -o docs/slides/slides.pdf

# PowerPoint
npx @marp-team/marp-cli@latest docs/slides/slides.md --pptx -o docs/slides/slides.pptx

# Live preview server while editing
npx @marp-team/marp-cli@latest -s docs/slides
```

> The deck references [`../images/architecture.svg`](../images/architecture.svg). Keep the
> relative path intact when exporting so the diagram embeds.

## Customising

- Theme/colors live in the YAML front-matter `style:` block at the top of `slides.md`.
- Speaker notes: add `<!-- notes go here -->` HTML comments under a slide; Marp surfaces
  them in presenter mode and PPTX export.
- Re-brand by swapping the `header`, `footer`, and heading colors.

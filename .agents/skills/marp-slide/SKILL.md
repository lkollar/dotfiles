---
name: marp-slide
description: Create professional Marp presentation slides with seven themes. Use when users ask for slides, presentations, Marp decks, or slide design polish.
---

# Marp Slide Creator

Use this skill when the user asks to create, improve, or theme Marp
presentation slides.

## Workflow

1. Pick a theme from the content and audience.
2. Read `references/marp-syntax.md`.
3. For images, read `references/image-patterns.md`.
4. For quality guidance, read `references/best-practices.md`.
5. Start from the matching `assets/template-*.md`.
6. Save the final Marp file as `.md`.

## Theme Selection

- Technical/developer: `template-tech.md`
- Business/corporate: `template-business.md`
- Creative/event: `template-colorful.md` or `template-gradient.md`
- Academic/simple: `template-minimal.md`
- Dark background: `template-dark.md` or `template-tech.md`
- General/unsure: `template-basic.md`

For more detail, read `references/theme-selection.md`.

## Slide Quality Rules

- Use a title slide with `<!-- _class: lead -->`.
- Keep content slides to one message each.
- Use concise h2 titles.
- Use 3-5 bullets per slide.
- Keep body text short.
- Use whitespace deliberately.
- Embed CSS in the Marp file unless user asks otherwise.
- Use proper Marp image syntax for backgrounds and side images.

## Image Patterns

- Side image: `![bg right:40%](image.png)`
- Centered image: `![w:600px](image.png)`
- Full background: `![bg](image.png)`
- Darkened background: `![bg brightness:0.5](image.png)`

## References

- `references/marp-syntax.md`
- `references/image-patterns.md`
- `references/theme-css-guide.md`
- `references/advanced-features.md`
- `references/official-themes.md`
- `references/theme-selection.md`
- `references/best-practices.md`

## Templates

- `assets/template-basic.md`
- `assets/template-minimal.md`
- `assets/template-colorful.md`
- `assets/template-dark.md`
- `assets/template-gradient.md`
- `assets/template-tech.md`
- `assets/template-business.md`

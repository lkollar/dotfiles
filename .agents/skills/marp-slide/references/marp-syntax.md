# Marp Syntax

Start a deck:

```markdown
---
marp: true
theme: default
paginate: true
---
```

Use `---` for slide breaks.

Common directives:

- `theme: default|gaia|uncover`
- `size: 16:9|4:3|A4`
- `paginate: true`
- `header: 'Text'`
- `footer: 'Text'`
- `class: lead`

Per-slide directives:

```markdown
<!-- _class: lead -->
<!-- _backgroundColor: black -->
<!-- _color: white -->
```

Use `_` for current slide only.

Marp supports inline CSS:

```markdown
<style>
section { background: #f8f8f4; }
</style>
```

Official docs:

- https://marp.app/
- https://marpit.marp.app/directives
- https://marpit.marp.app/theme-css

# Marp Theme CSS Guide

Marp themes style generated `<section>` slides.

Basic embedded style:

```markdown
<style>
section {
  background: #fff;
  color: #333;
  font-size: 24px;
  padding: 60px;
}
h1 { color: #1e40af; }
</style>
```

Standalone theme files need metadata:

```css
/* @theme my-theme */
section { background: #fff; }
```

Useful selectors:

- `section`
- `section.lead`
- `h1`, `h2`, `h3`
- `pre`, `code`
- `table`, `th`, `td`
- `footer`, `header`

Official docs: https://marpit.marp.app/theme-css

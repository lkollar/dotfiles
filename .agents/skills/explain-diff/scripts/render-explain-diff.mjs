#!/usr/bin/env node
import fs from "node:fs/promises";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import MarkdownIt from "markdown-it";
import { JSDOM } from "jsdom";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const skillRoot = path.resolve(__dirname, "..");
const stylePath = path.join(skillRoot, "assets", "style.css");
const quizJsPath = path.join(skillRoot, "assets", "quiz.js");

const REQUIRED_SECTIONS = ["Background", "Intuition", "Code", "Quiz"];

function usage() {
  return [
    "Usage:",
    "  render-explain-diff <input.md> -o /tmp/YYYY-MM-DD-explanation-<slug>.html",
    "  render-explain-diff validate <output.html> --source <input.md>"
  ].join("\n");
}

function fail(message) {
  console.error(`render-explain-diff: ${message}`);
  process.exit(1);
}

function htmlEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function attrEscape(value) {
  return htmlEscape(value).replaceAll("'", "&#39;");
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/<[^>]*>/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "section";
}

function parseAttrs(raw = "") {
  const attrs = {};
  const body = raw.trim().replace(/^\{|\}$/g, "");
  const re = /([A-Za-z][\w-]*)=(?:"([^"]*)"|'([^']*)'|([^\s]+))/g;
  let match;
  while ((match = re.exec(body))) {
    attrs[match[1]] = match[2] ?? match[3] ?? match[4] ?? "";
  }
  return attrs;
}

function parseHighlight(spec = "") {
  const ranges = [];
  for (const part of spec.split(",")) {
    const trimmed = part.trim();
    if (!trimmed) continue;
    const range = trimmed.match(/^(\d+)(?:-(\d+))?$/);
    if (!range) throw new Error(`invalid highlight range: ${part}`);
    const start = Number(range[1]);
    const end = Number(range[2] ?? range[1]);
    if (end < start) throw new Error(`invalid descending highlight range: ${part}`);
    ranges.push([start, end]);
  }
  return ranges;
}

function isHighlighted(lineNo, ranges) {
  return ranges.some(([start, end]) => lineNo >= start && lineNo <= end);
}

function extractBlock(source, name, handler) {
  const re = new RegExp(`:::${name}(\\{[^\\n]*\\})?\\n([\\s\\S]*?)\\n:::`, "g");
  return source.replace(re, (_full, rawAttrs = "", body = "") => handler(parseAttrs(rawAttrs), body));
}

function parseCodeNotes(markdown) {
  const notes = new Map();
  const stripped = extractBlock(markdown, "code-note", (attrs, body) => {
    if (!attrs.target) throw new Error("code-note missing target");
    const list = notes.get(attrs.target) ?? [];
    list.push({ lines: attrs.lines ?? "", html: body.trim() });
    notes.set(attrs.target, list);
    return "";
  });
  return { markdown: stripped, notes };
}

function parseQuizBlocks(markdown) {
  const quizzes = [];
  let index = 0;
  const replaced = extractBlock(markdown, "quiz", (attrs, body) => {
    const quiz = parseQuiz(attrs, body);
    quizzes.push(quiz);
    return `\n@@EXPLAIN_DIFF_QUIZ_${index++}@@\n`;
  });
  return { markdown: replaced, quizzes };
}

function parseQuiz(attrs, body) {
  const lines = body.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const questionLine = lines.find((line) => line.startsWith("? "));
  if (!questionLine) throw new Error(`quiz ${attrs.id ?? ""} missing question`);
  const answerLines = lines.filter((line) => line.startsWith("- "));
  const feedbackLine = lines.find((line) => line.startsWith("! "));
  const answers = answerLines.map((line) => {
    const correct = /\s*\[correct\]\s*$/.test(line);
    return {
      text: line.replace(/^- /, "").replace(/\s*\[correct\]\s*$/, ""),
      correct
    };
  });
  const correctCount = answers.filter((answer) => answer.correct).length;
  if (correctCount !== 1) {
    throw new Error(`quiz ${attrs.id ?? questionLine.slice(2)} must have exactly one correct answer`);
  }
  if (answers.length < 2) throw new Error(`quiz ${attrs.id ?? questionLine.slice(2)} needs at least two answers`);
  return {
    id: attrs.id ?? slugify(questionLine.slice(2)),
    question: questionLine.slice(2),
    answers,
    feedback: feedbackLine ? feedbackLine.slice(2) : ""
  };
}

function renderQuiz(quiz) {
  const buttons = quiz.answers.map((answer) => {
    return `<button class="quiz-option" type="button" data-correct="${answer.correct ? "true" : "false"}">${htmlEscape(answer.text)}</button>`;
  }).join("\n");
  return `<section class="quiz-card" id="${attrEscape(quiz.id)}">
  <div class="quiz-question">${htmlEscape(quiz.question)}</div>
  <div class="quiz-options">${buttons}</div>
  <div class="quiz-feedback" data-feedback="${attrEscape(quiz.feedback)}"></div>
</section>`;
}

function collectHeadings(markdown) {
  const headings = [];
  const seen = new Map();
  const re = /^(#{1,4})\s+(.+)$/gm;
  let match;
  while ((match = re.exec(markdown))) {
    const level = match[1].length;
    const text = match[2].trim().replace(/\s+#*$/, "");
    const base = slugify(text);
    const count = seen.get(base) ?? 0;
    seen.set(base, count + 1);
    headings.push({ level, text, id: count ? `${base}-${count + 1}` : base });
  }
  return headings;
}

function headingRenderer(headings) {
  let index = 0;
  return function (tokens, idx, _options, _env, self) {
    const heading = headings[index++];
    tokens[idx].attrSet("id", heading.id);
    return self.renderToken(tokens, idx, _options);
  };
}

function renderToc(headings) {
  const links = headings
    .filter((heading) => heading.level >= 2 && heading.level <= 3)
    .map((heading) => {
      const indent = heading.level === 3 ? " style=\"padding-left: 14px\"" : "";
      return `<a href="#${attrEscape(heading.id)}"${indent}>${htmlEscape(heading.text)}</a>`;
    })
    .join("\n");
  return `<nav class="toc" aria-label="Table of contents">
  <div class="toc-title">Contents</div>
  ${links}
</nav>`;
}

async function renderCode(lang, rawAttrs, code, notes) {
  const attrs = parseAttrs(rawAttrs);
  const title = attrs.title ?? "";
  const lineStart = Number(attrs.lineStart ?? "1");
  if (!Number.isInteger(lineStart) || lineStart < 1) throw new Error(`invalid lineStart for ${title || lang || "code block"}`);
  const ranges = parseHighlight(attrs.highlight ?? "");
  const language = lang || "text";
  const highlighted = await shikiLines(code, language);
  const sourceLines = code.replace(/\n$/, "").split("\n");
  const htmlLines = highlighted.length === sourceLines.length ? highlighted : sourceLines.map(htmlEscape);
  const rows = htmlLines.map((lineHtml, i) => {
    const lineNo = lineStart + i;
    const cls = isHighlighted(lineNo, ranges) ? " code-line highlighted" : "code-line";
    return `<span class="${cls}"><span class="line-no">${lineNo}</span><span class="line-code">${lineHtml || " "}</span></span>`;
  }).join("");
  const noteItems = [];
  if (attrs.note) noteItems.push({ lines: "", html: htmlEscape(attrs.note) });
  for (const note of notes.get(title) ?? []) {
    noteItems.push({ lines: note.lines, html: renderInlineMarkdown(note.html) });
  }
  const noteHtml = noteItems.length
    ? `<div class="code-notes">${noteItems.map((note) => `<div class="code-note">${note.lines ? `<div class="code-note-lines">Lines ${htmlEscape(note.lines)}</div>` : ""}<div>${note.html}</div></div>`).join("")}</div>`
    : "";
  return `<figure class="code-card">
  <figcaption class="code-header">
    <span class="code-title">${htmlEscape(title || "Code")}</span>
    <span class="code-meta"><span>${htmlEscape(language)}</span><button class="copy-button" type="button">Copy</button></span>
  </figcaption>
  <div class="code-scroll"><pre><code>${rows}</code></pre></div>
  <textarea class="copy-source" aria-hidden="true">${htmlEscape(code.replace(/\n$/, ""))}</textarea>
  ${noteHtml}
</figure>`;
}

async function shikiLines(code, language) {
  try {
    const { codeToHtml } = await import("shiki");
    const html = await codeToHtml(code.replace(/\n$/, ""), {
      lang: language,
      theme: "github-light"
    });
    const inner = html.match(/<code[^>]*>([\s\S]*?)<\/code>/)?.[1];
    if (!inner) return [];
    return inner.replace(/\n$/, "").split("\n");
  } catch {
    return code.replace(/\n$/, "").split("\n").map(htmlEscape);
  }
}

function renderInlineMarkdown(markdown) {
  const md = new MarkdownIt({ html: false, linkify: true });
  return md.renderInline(markdown);
}

async function renderMermaid(source, index) {
  try {
    return await renderMermaidInProcess(source, index);
  } catch (error) {
    const viaCli = await renderMermaidWithCli(source, index, error);
    return viaCli;
  }
}

async function renderMermaidInProcess(source, index) {
  const dom = new JSDOM("<!doctype html><html><body><div id=\"mermaid-root\"></div></body></html>", {
    pretendToBeVisual: true
  });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  Object.defineProperty(globalThis, "navigator", {
    value: dom.window.navigator,
    configurable: true
  });
  globalThis.Element = dom.window.Element;
  globalThis.HTMLElement = dom.window.HTMLElement;
  globalThis.SVGElement = dom.window.SVGElement;
  globalThis.DOMParser = dom.window.DOMParser;
  globalThis.CSSStyleSheet = dom.window.CSSStyleSheet;
  globalThis.getComputedStyle = dom.window.getComputedStyle.bind(dom.window);
  if (!dom.window.SVGElement.prototype.getBBox) {
    dom.window.SVGElement.prototype.getBBox = function () {
      const tag = (this.tagName || "").toLowerCase();
      if (tag === "text" || tag === "tspan") {
        return textBBox(this.textContent || "");
      }
      const width = Number(this.getAttribute?.("width") ?? 0);
      const height = Number(this.getAttribute?.("height") ?? 0);
      if (Number.isFinite(width) && Number.isFinite(height) && (width > 0 || height > 0)) {
        return { x: 0, y: 0, width, height };
      }
      const text = (this.textContent || "").trim();
      if (text) return textBBox(text, { grouped: true });
      return {
        x: 0,
        y: 0,
        width: 64,
        height: 32
      };
    };
  }
  if (!dom.window.SVGElement.prototype.getComputedTextLength) {
    dom.window.SVGElement.prototype.getComputedTextLength = function () {
      return textBBox(this.textContent || "").width;
    };
  }

  const mermaid = (await import("mermaid")).default;
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "neutral"
  });
  const { svg } = await mermaid.render(`explain-diff-diagram-${index}`, source);
  const stripped = stripSvgNamespaces(svg);
  assertUsableMermaidSvg(stripped, "in-process Mermaid");
  return `<figure class="diagram-card">${stripped}</figure>`;
}

function textBBox(text, options = {}) {
  const lines = String(text).split(/\n/);
  const maxChars = options.grouped ? 80 : 120;
  const longest = lines.reduce((max, line) => Math.max(max, line.trim().length), 0);
  const width = Math.min(maxChars, longest) * 8;
  return {
    x: 0,
    y: 0,
    width: Math.max(16, width),
    height: options.grouped ? 64 : Math.max(18, lines.length * 18)
  };
}

async function renderMermaidWithCli(source, index, originalError) {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "explain-diff-mermaid-"));
  const input = path.join(tmp, `diagram-${index}.mmd`);
  const output = path.join(tmp, `diagram-${index}.svg`);
  const config = path.join(tmp, "config.json");
  await fs.writeFile(input, source, "utf8");
  await fs.writeFile(config, JSON.stringify({ securityLevel: "strict", theme: "neutral" }), "utf8");
  const localMmdc = path.join(skillRoot, "node_modules", ".bin", "mmdc");
  const command = existsSync(localMmdc) ? localMmdc : "mmdc";
  const result = spawnSync(command, ["-i", input, "-o", output, "-c", config, "-b", "transparent"], {
    encoding: "utf8"
  });
  if (result.status !== 0) {
    throw new Error(`Mermaid render failed in-process and via CLI.

In-process error:
${originalError.stack || originalError.message}

CLI error:
${result.stderr || result.stdout || "no output"}`);
  }
  const svg = stripSvgNamespaces(await fs.readFile(output, "utf8"));
  assertUsableMermaidSvg(svg, "Mermaid CLI");
  await fs.rm(tmp, { recursive: true, force: true });
  return `<figure class="diagram-card">${svg}</figure>`;
}

function stripSvgNamespaces(svg) {
  return svg
    .replace(/\sxmlns="http:\/\/www\.w3\.org\/2000\/svg"/g, "")
    .replace(/\sxmlns:xlink="http:\/\/www\.w3\.org\/1999\/xlink"/g, "");
}

function assertUsableMermaidSvg(svg, rendererName) {
  const geometry = inspectSvgGeometry(svg);
  if (!geometry.ok) {
    throw new Error(`${rendererName} produced unusable SVG: ${geometry.reason}`);
  }
}

function inspectSvgGeometry(svg) {
  const viewBoxMatch = svg.match(/\bviewBox=["']\s*([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s*["']/);
  if (!viewBoxMatch) return { ok: false, reason: "missing viewBox" };

  const width = Number(viewBoxMatch[3]);
  const height = Number(viewBoxMatch[4]);
  if (!Number.isFinite(width) || !Number.isFinite(height)) {
    return { ok: false, reason: `invalid viewBox ${viewBoxMatch[0]}` };
  }
  if (width < 32 || height < 32) {
    return { ok: false, reason: `viewBox too small (${width}x${height})` };
  }
  if (width > 20000 || height > 20000) {
    return { ok: false, reason: `viewBox too large (${width}x${height})` };
  }
  if (width / height > 80 || height / width > 80) {
    return { ok: false, reason: `extreme viewBox aspect ratio (${width}x${height})` };
  }
  return { ok: true, reason: "" };
}

async function replaceFences(markdown, notes) {
  const blocks = [];
  const fenceRe = /```([A-Za-z0-9_-]+)?\s*(\{[^\n]*\})?\n([\s\S]*?)```/g;
  let index = 0;
  const replaced = markdown.replace(fenceRe, (_full, lang = "", attrs = "", body = "") => {
    const token = `@@EXPLAIN_DIFF_BLOCK_${index++}@@`;
    blocks.push({ token, lang, attrs, body });
    return `\n${token}\n`;
  });

  const rendered = new Map();
  for (let i = 0; i < blocks.length; i++) {
    const block = blocks[i];
    if (block.lang.toLowerCase() === "mermaid") {
      rendered.set(block.token, await renderMermaid(block.body, i));
    } else {
      rendered.set(block.token, await renderCode(block.lang, block.attrs, block.body, notes));
    }
  }

  return { markdown: replaced, rendered };
}

async function renderDocument(source, sourcePath, outputPath) {
  validateMarkdown(source);
  const { markdown: withoutNotes, notes } = parseCodeNotes(source);
  const { markdown: withoutQuizzes, quizzes } = parseQuizBlocks(withoutNotes);
  const callouts = [];
  const diagrams = [];
  let markdown = extractBlock(withoutQuizzes, "callout", (attrs, body) => {
    const token = `@@EXPLAIN_DIFF_CALLOUT_${callouts.length}@@`;
    callouts.push(renderCallout(attrs, body));
    return `\n${token}\n`;
  });
  markdown = extractBlock(markdown, "diagram", (attrs, body) => {
    const token = `@@EXPLAIN_DIFF_DIAGRAM_${diagrams.length}@@`;
    diagrams.push(renderHtmlDiagram(attrs, body));
    return `\n${token}\n`;
  });
  const fenceResult = await replaceFences(markdown, notes);
  markdown = fenceResult.markdown;

  const headings = collectHeadings(markdown);
  const md = new MarkdownIt({ html: false, linkify: true, typographer: true });
  md.renderer.rules.heading_open = headingRenderer(headings);
  let content = md.render(markdown);

  for (let i = 0; i < callouts.length; i++) {
    content = replaceToken(content, `@@EXPLAIN_DIFF_CALLOUT_${i}@@`, callouts[i]);
  }
  for (let i = 0; i < diagrams.length; i++) {
    content = replaceToken(content, `@@EXPLAIN_DIFF_DIAGRAM_${i}@@`, diagrams[i]);
  }
  for (const [token, html] of fenceResult.rendered) {
    content = replaceToken(content, token, html);
  }
  for (let i = 0; i < quizzes.length; i++) {
    content = replaceToken(content, `@@EXPLAIN_DIFF_QUIZ_${i}@@`, renderQuiz(quizzes[i]));
  }

  const title = headings.find((heading) => heading.level === 1)?.text ?? "Code Change Explanation";
  const css = await fs.readFile(stylePath, "utf8");
  const js = await fs.readFile(quizJsPath, "utf8");
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${htmlEscape(title)}</title>
  <style>${css}</style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <h1>${htmlEscape(title)}</h1>
    </div>
    <div class="shell">
      <main>${content.replace(/<h1 id="[^"]+">[\s\S]*?<\/h1>/, "")}</main>
      ${renderToc(headings)}
    </div>
  </div>
  <script>${js}</script>
</body>
</html>
`;
  await fs.writeFile(outputPath, html, "utf8");
  await validateOutput(outputPath, sourcePath);
}

function replaceToken(content, token, html) {
  return content
    .replaceAll(`<p>${token}</p>`, html)
    .replaceAll(token, html);
}

function renderCallout(attrs, body) {
  const type = attrs.type ?? "note";
  const title = attrs.title ?? type;
  return `<aside class="callout ${attrEscape(type)}">
  <div class="callout-title">${htmlEscape(title)}</div>
  <div>${renderMarkdownFragment(body)}</div>
</aside>`;
}

function renderHtmlDiagram(attrs, body) {
  const title = attrs.title ? `<div class="diagram-title">${htmlEscape(attrs.title)}</div>` : "";
  return `<figure class="diagram-card">${title}${body.trim()}</figure>`;
}

function renderMarkdownFragment(markdown) {
  const md = new MarkdownIt({ html: false, linkify: true, typographer: true });
  return md.render(markdown);
}

function validateMarkdown(source) {
  const missing = REQUIRED_SECTIONS.filter((section) => !new RegExp(`^##\\s+${section}\\s*$`, "m").test(source));
  if (missing.length) throw new Error(`missing required sections: ${missing.join(", ")}`);

  const quizBlocks = [...source.matchAll(/:::quiz(\{[^\n]*\})?\n([\s\S]*?)\n:::/g)];
  for (const match of quizBlocks) {
    parseQuiz(parseAttrs(match[1] ?? ""), match[2]);
  }
  if (quizBlocks.length && quizBlocks.length !== 5) {
    throw new Error(`expected exactly five quiz blocks, found ${quizBlocks.length}`);
  }
}

async function validateOutput(outputPath, sourcePath) {
  const errors = [];
  const base = path.basename(outputPath);
  if (path.dirname(outputPath) !== "/tmp" || !/^\d{4}-\d{2}-\d{2}-explanation-[a-z0-9-]+\.html$/.test(base)) {
    errors.push("output path must be /tmp/YYYY-MM-DD-explanation-<slug>.html");
  }
  if (!existsSync(outputPath)) errors.push("HTML file does not exist");
  const html = existsSync(outputPath) ? await fs.readFile(outputPath, "utf8") : "";
  const htmlWithoutNamespaces = html.replace(/https?:\/\/www\.w3\.org\/[^"'\s)<>]+/gi, "");
  if (/https?:\/\//i.test(htmlWithoutNamespaces)) errors.push("HTML contains external http(s) reference");
  if (/<link\b[^>]*rel=["']?stylesheet/i.test(html)) errors.push("HTML links external stylesheet");
  if (/<script\b[^>]*\bsrc=/i.test(html)) errors.push("HTML links external script");
  if (!/<style>[\s\S]+<\/style>/.test(html)) errors.push("missing inline CSS");
  if (!/<script>[\s\S]+<\/script>/.test(html)) errors.push("missing inline JavaScript");
  if (/```mermaid|language-mermaid|<pre><code>[\s\S]*sequenceDiagram/.test(html)) errors.push("Mermaid block appears unrendered");
  for (const [index, match] of [...html.matchAll(/<svg\b[\s\S]*?<\/svg>/g)].entries()) {
    const geometry = inspectSvgGeometry(match[0]);
    if (!geometry.ok) errors.push(`inline SVG ${index + 1} has unusable geometry: ${geometry.reason}`);
  }
  if (/<pre\b/.test(html) && !/white-space:\s*pre/.test(html)) errors.push("code CSS must preserve whitespace");
  if (!/<svg[\s\S]*<\/svg>/.test(html) && sourcePath) {
    const source = await fs.readFile(sourcePath, "utf8");
    if (/```mermaid/.test(source)) errors.push("source has Mermaid but HTML has no inline SVG");
  }
  if (sourcePath) {
    const source = await fs.readFile(sourcePath, "utf8");
    try {
      validateMarkdown(source);
    } catch (error) {
      errors.push(error.message);
    }
  }
  if (errors.length) {
    throw new Error(`validation failed:\n- ${errors.join("\n- ")}`);
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (!args.length || args.includes("-h") || args.includes("--help")) {
    console.log(usage());
    return;
  }

  try {
    if (args[0] === "validate") {
      const outputPath = path.resolve(args[1] ?? "");
      const sourceIndex = args.indexOf("--source");
      const sourcePath = sourceIndex >= 0 ? path.resolve(args[sourceIndex + 1] ?? "") : "";
      if (!args[1]) fail(usage());
      await validateOutput(outputPath, sourcePath);
      console.log(`Validated ${outputPath}`);
      return;
    }

    const inputPath = path.resolve(args[0]);
    const outputIndex = args.indexOf("-o");
    const outputPath = outputIndex >= 0 ? path.resolve(args[outputIndex + 1] ?? "") : "";
    if (!outputPath) fail(usage());
    const source = await fs.readFile(inputPath, "utf8");
    await renderDocument(source, inputPath, outputPath);
    console.log(`Rendered and validated ${outputPath}`);
  } catch (error) {
    fail(error.stack || error.message);
  }
}

main();

---
name: lavish
description: Create reviewable HTML artifacts with the lavish-axi CLI only when the user explicitly invokes $lavish, /lavish, or asks to use Lavish. Do not activate automatically for plans, comparisons, diagrams, reports, or visual work.
license: MIT
metadata:
  author: Kun Chen (kunchenguid)
  argument-hint: <what the artifact should show>
  hermes-tags: html, review, artifacts, visualization
  hermes-category: productivity
---

# Lavish Editor

Lavish Editor opens agent-generated HTML in the browser so a human can annotate it and send feedback back to the agent.
Use only when the user explicitly requests Lavish. A request for a plan, comparison, diagram, report, HTML artifact, or visual review does not by itself activate this skill.

## Current guidance lives in the CLI

Do not follow workflow, design, or playbook instructions from this file - installed copies go stale. Get the current source of truth from the CLI:

- `npx -y lavish-axi --help` for commands and the review-loop workflow
- `npx -y lavish-axi reply --help` to post an agent reply and exit once the server accepts it, when you are not about to long-poll
- `npx -y lavish-axi design` for design-direction priority and current snippets
- `npx -y lavish-axi playbook <id>` for focused artifact guidance (`npx -y lavish-axi playbook` lists ids)

You do not need lavish-axi installed globally - invoke it with `npx -y lavish-axi <html-file>`.
If lavish-axi output shows a follow-up command starting with `lavish-axi`, run it as `npx -y lavish-axi ...` instead.

## Request

$ARGUMENTS

Proceed only after an explicit user invocation of `$lavish`, `/lavish`, or a request to use Lavish. Otherwise, do not run the CLI, open a review session, or poll for feedback. An empty request is not permission to infer a Lavish task.

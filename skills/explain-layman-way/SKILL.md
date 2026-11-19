---
name: explain-layman-way
description: 'Explain a research paper or technical topic in plain language from first principles: a layered dependency map of every concept, every jargon term defined, toy-number worked examples, metrics explained before results, honest trade-offs, and a link to the reader''s goal. Use when: explain this paper, help me understand, layman terms, explain simply, first principles, worked examples, ELI5 research, I do not understand this topic, break down this paper.'
argument-hint: 'Paper link or topic; optional: my background, my goal (e.g. write a question to the author, reproduce it, prepare for an interview)'
---

# Explain Layman Way

Teach a research paper or a technical topic to a smart reader who does not know its field.
Build from the most basic idea up to the reader's goal. Every new word is explained. Every
concept gets a tiny worked example.

## When to Use

- "Help me understand this paper / this topic."
- "Explain it in layman terms / from first principles / with worked examples."
- "I read the abstract and did not understand it."
- Preparing to talk to an author, a professor or an interviewer about a paper.

## Inputs

| Input | Required | Default when missing |
|---|---|---|
| Paper link, PDF, or topic | **Yes**: ask if it is missing | — |
| Reader's background | No | Use what the conversation already says. If nothing, ask one short question. |
| Reader's goal | No | "Understand it well enough to explain it to someone else." |

## Before You Explain

1. Read the **full text**, not only the abstract. For arXiv, open the PDF or HTML version
   (`arxiv.org/pdf/<id>`). Note the exact numbers, equations and stated limitations.
2. List every concept the paper depends on, then sort them into layers (foundations first).
3. Check any related work you plan to mention (it must exist and say what you claim).

## Rules

- Assume I don't know any term the paper uses. Explain every technical word and acronym
  the first time it appears, in one plain sentence. Never use a new term without explaining it.
- Use first principles: start from the most basic idea and build up. Short sentences, simple English.
- Give every concept a tiny worked example with small made-up numbers (2D vectors, single
  digits). Label made-up numbers as "toy numbers" and the paper's numbers as "paper numbers".
- Don't invent facts or results. If you can't find something in the paper, say so.

## Structure

1. **One-sentence summary**: what problem the paper solves and why anyone cares.
2. **Dependency map**: draw a diagram of every concept needed to understand the paper, in
   layers, with foundations at the top and my goal at the bottom (for example: math basics →
   model basics → the paper's idea → how results are measured → links to my field → my goal).
   Each layer depends on the one above.
3. **Walk through the map** layer by layer, in that order. For each concept: what it means,
   a worked example, and one line on why the paper needs it.
4. **The paper's core idea**: the problem, the cause the authors found, and their fix, each
   with a toy-number example. Translate each key equation symbol by symbol into words.
5. **How results are measured**: before giving any result, explain each metric (what it
   measures, whether lower or higher is better, and a worked example). Then give the main
   paper numbers and what they mean in plain words.
6. **The honest picture**: trade-offs, where it doesn't win, and the authors' stated limitations.
7. **Connection to me**: how this links to my background, and any closely related work from
   other fields I should know about (explain those terms too).
8. **My goal**: use everything above to deliver my goal (a question, a plan or a summary),
   and tell me which terms I must be able to explain before I use it.
9. **Check my understanding**: end with 3 short questions I should be able to answer now,
   with answers hidden at the bottom.

## Output Notes

- **The diagram**: if an inline visual or diagram tool is available, draw the dependency map
  with it (one box per concept, one row per layer, arrows between layers). Otherwise use a
  Mermaid `flowchart TD` block or an ASCII tree.
- **Concept format**: `**Name**: plain meaning.` then a bullet with the worked example, then
  one line on why the paper needs it.
- **Hidden answers**: put them under a final `Answers` heading, or inside
  `<details><summary>Answers</summary> … </details>` where Markdown supports it.
- **Topic instead of a paper**: same structure. In steps 4 to 6, use the key method or
  result of the topic in place of "the paper".
- Cite the paper (and any related work) with links so the reader can check every number.

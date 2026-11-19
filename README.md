# ai-toolkit

Personal AI agent skills for GitHub Copilot (CLI and VS Code) and other
[Agent Plugins](https://agent-plugins.org) clients. Keep the skills in one repo, install them once,
and use them on every PC.

## Skills

| Skill | What it does | Use it |
|---|---|---|
| [ideal-candidate-resume](./skills/ideal-candidate-resume/SKILL.md) | Builds a fictional benchmark resume that a job description would hire. It covers 100% of the JD keywords, obeys constraints (years, companies, date ranges), and ends with an evidence report. Output: Markdown, DOCX, or PDF. | `/ideal-candidate-resume <paste JD>` |
| [explain-layman-way](./skills/explain-layman-way/SKILL.md) | Explains a research paper or topic from first principles. It draws a dependency map of every concept, defines every jargon term, gives toy-number worked examples, explains metrics before results, and ends at your goal with 3 check questions. | `/explain-layman-way <paper link or topic>` |

## How it works (first principles)

1. A **skill** is a folder with a `SKILL.md` file. The agent reads the `description` line to
   decide when to load the skill. Then the agent follows the steps in the body. Extra files
   (`references/`, `assets/`, `scripts/`) load only when a step needs them.
2. A **plugin** is a folder with a `plugin.json` file and a `skills/` folder. Install the
   plugin and you get all of its skills.
3. A **marketplace** is a catalog file (`marketplace.json`) that lists plugins. Add the
   catalog one time. Then install and update plugins by name.

This repo is all three at the same time:

```text
 brkuhgk/ai-toolkit (GitHub)
 ├── .github/plugin/marketplace.json ──► catalog "brkuhgk"   (lists the plugin "ai-toolkit")
 ├── plugin.json ──────────────────────► plugin  "ai-toolkit" (repo root = plugin root)
 └── skills/<name>/SKILL.md ───────────► one skill per folder
```

## Flows

**Flow 1: Install with Copilot CLI (recommended)**

```text
 copilot plugin install brkuhgk/ai-toolkit
            │
            ▼
 [download repo] ──► [read plugin.json] ──► [load skills/*/SKILL.md] ──► /ideal-candidate-resume
```

**Flow 2: Install from the marketplace (update by name)**

```text
 copilot plugin marketplace add brkuhgk/ai-toolkit   ── one time per PC
            │
            ▼
 copilot plugin install ai-toolkit@brkuhgk           ── one time per PC
            │
            ▼
 copilot plugin update ai-toolkit                    ── after each push
```

**Flow 3: Copy the folder (VS Code, or any client without plugins)**

```text
 [git clone] ──► [copy skills/<name>/] ──► [~/.copilot/skills/<name>/] ──► [reload VS Code] ──► /<name>
```

**Flow 4: Add a new skill**

```text
 [make skills/<new-name>/SKILL.md] ──► [name: <new-name> = folder name]
            │
            ▼
 [add a row to the Skills table] ──► [increase version] ──► [commit + push] ──► copilot plugin update ai-toolkit
```

**Flow 5: Use a skill (example)**

```text
 /ideal-candidate-resume <JD>  max 5 years, output docx
            │
            ▼
 [draft] ──► [validate with scripts] ──► [fix gaps] ──► [evidence report] ──► .md / .docx / .pdf
              ▲                              │
              └──────── repeat until pass ───┘
```

## Install

**Copilot CLI**

```shell
copilot plugin install brkuhgk/ai-toolkit
```

Or use the marketplace:

```shell
copilot plugin marketplace add brkuhgk/ai-toolkit
copilot plugin install ai-toolkit@brkuhgk
```

**Copy the folder: Windows (PowerShell)**

```powershell
git clone https://github.com/brkuhgk/ai-toolkit.git
New-Item -ItemType Directory -Force "$HOME\.copilot\skills" | Out-Null
Copy-Item -Recurse -Force .\ai-toolkit\skills\* "$HOME\.copilot\skills\"
```

**Copy the folder: macOS / Linux**

```bash
git clone https://github.com/brkuhgk/ai-toolkit.git
mkdir -p ~/.copilot/skills && cp -R ai-toolkit/skills/* ~/.copilot/skills/
```

Reload VS Code after the copy. Type `/` in chat to see the skills.

**Optional Python packages** (only for DOCX / PDF output):

```shell
pip install python-docx docx2pdf
```

## Add a new skill

1. Make the folder `skills/<skill-name>/`. Use lowercase letters, digits, and hyphens.
2. Make `SKILL.md` with frontmatter: `name` (same as the folder) and `description`
   (what the skill does, when to use it, and trigger words).
3. Put long docs in `references/`, templates in `assets/`, and helper code in `scripts/`.
   Link to them from `SKILL.md` with relative links.
4. Add a row to the [Skills](#skills) table.
5. Increase `version` in `plugin.json` and in `.github/plugin/marketplace.json`.
6. Commit and push with the personal account. Then run `copilot plugin update ai-toolkit`.

## Repo layout

```text
ai-toolkit/
├── .github/plugin/marketplace.json   catalog for "copilot plugin marketplace add"
├── plugin.json                       plugin manifest (Agent Plugins 1.0)
├── skills/
│   ├── ideal-candidate-resume/
│   │   ├── SKILL.md                  the skill (procedure + rules)
│   │   ├── assets/                   resume template
│   │   ├── references/               demographics rules, evidence report format
│   │   └── scripts/                  validate_resume.py, render_resume.py (optional helpers)
│   └── explain-layman-way/
│       └── SKILL.md                  explain a paper or topic from first principles
├── LICENSE
└── README.md
```

## Commit with the personal account

This repo belongs to the personal account `brkuhgk`. Set the identity for this repo only.
This keeps the global (work) identity the same.

```shell
git config user.name "brkuhgk"
git config user.email "43676649+brkuhgk@users.noreply.github.com"
git remote set-url origin https://brkuhgk@github.com/brkuhgk/ai-toolkit.git
```

The user name in the remote URL tells Git Credential Manager to use the `brkuhgk` login,
not the work login.

## License

[MIT](./LICENSE)

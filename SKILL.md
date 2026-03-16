---
name: notebooklm-codex-bridge
description: Query Google NotebookLM notebooks from local Codex through browser automation for source-grounded, citation-backed answers based on uploaded documents only. Use when the user mentions NotebookLM, shares a NotebookLM notebook URL, explicitly invokes "$NotebookLM Bridge", wants Codex to ask their notebook questions, needs persistent Google authentication, or wants notebook library management such as add/list/activate/search/reset. When invoked from the Codex client, run the workflow internally and return the answer in chat instead of telling the user to use terminal commands.
---

# NotebookLM Codex Bridge

Use this skill to let Codex interact with Google NotebookLM from the local machine instead of copy-pasting between the terminal and the browser.

Prefer this skill when the user wants answers grounded in their uploaded NotebookLM sources, especially for internal docs, manuals, papers, SOPs, or private notes that should not be re-ingested into the model context.

## Quick Start

1. Check auth status:
   `python scripts/run.py auth_manager.py status`
2. If needed, start one-time Google login:
   `python scripts/run.py auth_manager.py setup`
3. Add or inspect notebooks in the local library:
   `python scripts/run.py notebook_manager.py list`
   If the local library is empty, refresh it from NotebookLM home:
   `python scripts/run.py notebook_manager.py refresh`
4. Ask a notebook a question:
   `python scripts/run.py ask_question.py --question "What does this notebook say about ...?" --notebook-url "https://notebooklm.google.com/notebook/..."`
5. For the smoother one-sentence workflow, run:
   `python scripts/run.py smart_query.py --request "user request"`

Always use the `run.py` wrapper. It creates the local `.venv`, installs dependencies, and runs the requested script with the right interpreter.

## Core Workflow

### 1. Authenticate once
Run:
`python scripts/run.py auth_manager.py setup`

The browser must stay visible so the user can complete Google sign-in manually. The script stores browser state locally for reuse.

### 2. Manage the notebook library
Use:
- `python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPIC1,TOPIC2`
- `python scripts/run.py notebook_manager.py list`
- `python scripts/run.py notebook_manager.py refresh`
- `python scripts/run.py notebook_manager.py search --query "keyword"`
- `python scripts/run.py notebook_manager.py activate --id notebook-id`
- `python scripts/run.py notebook_manager.py remove --id notebook-id`

Prefer storing a notebook in the local library before repeated use. It gives Codex a stable notebook ID and lets the skill keep an active notebook.

### 3. Query NotebookLM
Use:
- `python scripts/run.py ask_question.py --question "..." --notebook-id notebook-id`
- `python scripts/run.py ask_question.py --question "..." --notebook-url "https://notebooklm.google.com/notebook/..."`
- `python scripts/run.py ask_question.py --question "..." --show-browser` for debugging
- `python scripts/run.py smart_query.py --request "Describe the user request in Chinese or English"`
- `python scripts/run.py smart_query.py --request-file REQUEST.txt`

If no notebook is provided, the script uses the active notebook from the local library.
If the user writes in Chinese, prefer `smart_query.py`. It now auto-translates the request to English, auto-selects the notebook, and asks NotebookLM in one step.
Use direct `ask_question.py` mainly when the notebook is already known and the question is already in English.

### 4. Reset state when needed
Use:
- `python scripts/run.py cleanup_manager.py`
- `python scripts/run.py cleanup_manager.py --confirm --preserve-library`
- `python scripts/run.py auth_manager.py reauth`

## Operating Rules

1. Always use `python scripts/run.py ...`, not direct script execution.
2. Run `auth_manager.py status` before assuming login is still valid.
3. Use `--show-browser` when selectors fail or NotebookLM UI has changed.
4. Treat NotebookLM as the source of truth; summarize what it returns instead of improvising unsupported details.
5. If the user shares a fresh NotebookLM URL, prefer querying that URL directly first, then offer to add it to the library.

## Recommended Prompts

- "Use NotebookLM to answer this from my uploaded docs only."
- "Set up NotebookLM authentication."
- "Add this notebook to my local NotebookLM library."
- "List my NotebookLM notebooks and activate the React docs notebook."
- "Ask my active NotebookLM notebook what it says about this API."
- "Ask my NotebookLM what this notebook is trying to study."
- "Answer only from my NotebookLM notebook and do not add unsupported details."

## Files

- `scripts/run.py`: wrapper that bootstraps the local environment
- `scripts/setup_environment.py`: creates `.venv` and installs dependencies
- `scripts/auth_manager.py`: persistent Google authentication
- `scripts/notebook_manager.py`: local notebook catalog
- `scripts/ask_question.py`: NotebookLM query automation
- `scripts/smart_query.py`: auto-select notebook and query in one step
- `scripts/cleanup_manager.py`: safe reset helpers
- `references/setup.md`: installation notes, limitations, and selector guidance

## Escalation

Pause and explain the tradeoff before proceeding if:
- the user wants to automate a primary Google account instead of a dedicated account
- authentication repeatedly fails and clearing state may log them out
- NotebookLM UI changes break selectors and script patching is required

## Codex Client Behavior

When the user talks to Codex directly instead of typing shell commands:
1. Detect NotebookLM intent from phrases like "my notebook", "my NotebookLM", "check my docs", "answer from my uploaded documents", or a NotebookLM URL.
2. Treat any message beginning with `$NotebookLM Bridge` as an explicit invocation of this skill. Everything after that marker is the NotebookLM request.
3. Do not ask the user to run terminal commands when the request is a normal NotebookLM query from the Codex client.
4. If the local library is empty, run `python scripts/run.py notebook_manager.py refresh`.
5. If the original request contains non-ASCII text, save it to a temporary UTF-8 text file and run `python scripts/run.py smart_query.py --request-file "<temp file>"`.
6. Otherwise run `python scripts/run.py smart_query.py --request "<user's original request>"`.
7. Return the selected notebook name and the NotebookLM answer back to the user in the same Codex reply.

Example direct client invocations:
- `$NotebookLM Bridge help me summarize the active notebook`
- `$NotebookLM Bridge answer from my notebook only and do not add unsupported details`

Load [references/setup.md](./references/setup.md) only when setup, troubleshooting, or selector maintenance details are needed.

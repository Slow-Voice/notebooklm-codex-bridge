# NotebookLM Bridge Notes

## What this skill is for

This skill adapts the public `PleasePrompto/notebooklm-skill` idea for local Codex usage.

It is designed for:
- source-grounded answers from Google NotebookLM
- persistent local Google authentication
- a small local notebook catalog so Codex can reuse notebook URLs
- browser automation instead of copy-paste

## Installation behavior

The first call to `python scripts/run.py ...` creates `.venv` inside the skill folder and installs:
- `patchright`
- `python-dotenv`

Patchright then attempts to install Chrome with:
`python -m patchright install chrome`

If this step fails, run it manually from the skill-local Python interpreter.

## Authentication model

Authentication is stored locally in:
- `data/browser_state/state.json`
- `data/browser_state/browser_profile/`
- `data/auth_info.json`

This keeps browser cookies and profile state on the local machine so Codex can reuse them on later calls.

## Local library model

The library file is:
- `data/library.json`

It stores:
- notebook ID
- notebook name
- NotebookLM URL
- description
- topics
- usage counters

## Query behavior

`ask_question.py`:
1. loads the saved browser profile
2. opens the target notebook
3. finds the query input
4. types the prompt
5. submits the query
6. waits for the newest visible answer block to stabilize
7. prints JSON to stdout

If selectors fail, retry with:
`python scripts/run.py ask_question.py --question "..." --show-browser`

`smart_query.py`:
1. loads the local library
2. auto-translates the request to English when needed
3. auto-selects the most relevant notebook
4. sends the English NotebookLM question
4. returns both the selected notebook and the answer

## Selector maintenance

NotebookLM UI changes may break selectors.

Current query selectors:
- `textarea.query-box-input`
- `textarea[aria-label="Input for queries"]`
- `textarea[aria-label*="query"]`
- `textarea`

Current response selectors:
- `.to-user-container .message-text-content`
- `[data-message-author='bot']`
- `[data-message-author='assistant']`
- `div.markdown`

If Google changes the UI, patch `scripts/config.py` first.

## Practical cautions

- Prefer a dedicated Google account for automation.
- Login must be done in a visible browser window.
- NotebookLM rate limits and UI behavior can change.
- This bridge is browser automation, not an official NotebookLM API.
- Non-ASCII prompts currently enter unreliably in NotebookLM through automation, so `smart_query.py` translates Chinese requests to English before asking NotebookLM.

## Useful external references

- NotebookLM help center: https://support.google.com/notebooklm/
- NotebookLM site: https://notebooklm.google.com/
- Source repo this skill adapts: https://github.com/PleasePrompto/notebooklm-skill

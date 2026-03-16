# NotebookLM Codex Bridge

Query Google NotebookLM from local Codex with browser automation, persistent authentication, local notebook routing, and source-grounded answers.

This project turns NotebookLM into a practical backend for Codex workflows:
- ask NotebookLM from Codex without copy-pasting
- keep Google login state locally
- maintain a local notebook library
- auto-select the right notebook for a request
- support direct Codex client invocation such as `$NotebookLM Bridge ...`

## What It Does

`notebooklm-codex-bridge` is a local Codex skill that connects Codex to Google NotebookLM through browser automation.

Instead of manually opening NotebookLM, typing a question, copying the answer, and pasting it back into Codex, this skill lets Codex do that workflow internally and return the answer in chat.

It is especially useful when:
- your source of truth already lives in NotebookLM
- you want answers grounded in uploaded documents only
- you want lower hallucination risk for private documentation or research notebooks
- you want Codex to route between multiple NotebookLM notebooks automatically

## Core Features

- Persistent Google authentication stored locally
- Notebook library management
- Auto-refresh from NotebookLM home
- Auto-selection of the most relevant notebook
- Automatic translation path for Chinese requests before sending to NotebookLM
- Direct client invocation support through `$NotebookLM Bridge`
- Local isolated Python environment per skill

## Project Structure

```text
notebooklm-codex-bridge/
|- SKILL.md
|- README.md
|- requirements.txt
|- .gitignore
|- agents/
|  |- openai.yaml
|- references/
|  |- setup.md
|- scripts/
   |- run.py
   |- setup_environment.py
   |- auth_manager.py
   |- notebook_manager.py
   |- ask_question.py
   |- smart_query.py
   |- browser_utils.py
   |- cleanup_manager.py
   |- config.py
```

## Installation

Place this folder inside your local Codex skills directory:

```powershell
C:\Users\YAN10\.codex\skills\notebooklm-codex-bridge
```

The first run will create a local `.venv` and install dependencies automatically.

## First-Time Setup

1. Check auth status:

```powershell
python scripts\run.py auth_manager.py status
```

2. Authenticate with Google:

```powershell
python scripts\run.py auth_manager.py setup
```

3. Sync your recent NotebookLM notebooks into the local library:

```powershell
python scripts\run.py notebook_manager.py refresh
```

## Direct Codex Client Usage

Once the skill is installed, you can invoke it directly from Codex chat:

```text
$NotebookLM Bridge help me summarize the active notebook
```

```text
$NotebookLM Bridge answer only from my notebook and do not add unsupported details
```

```text
$NotebookLM Bridge 帮我总结颅内生殖细胞瘤那个 notebook 的预测方案，只根据 notebook 回答
```

The intended behavior is:
1. Codex detects the explicit skill invocation
2. Codex refreshes the notebook library if needed
3. Codex routes the request to the best matching notebook
4. Codex asks NotebookLM internally
5. Codex returns the answer back in the same chat

## Script Usage

### Check authentication

```powershell
python scripts\run.py auth_manager.py status
```

### Re-authenticate

```powershell
python scripts\run.py auth_manager.py reauth
```

### Refresh notebook library

```powershell
python scripts\run.py notebook_manager.py refresh
```

### List notebooks

```powershell
python scripts\run.py notebook_manager.py list
```

### Ask a specific notebook

```powershell
python scripts\run.py ask_question.py --question "What does this notebook say about the model pipeline?" --notebook-id my-notebook-id
```

### Auto-route and ask in one step

```powershell
python scripts\run.py smart_query.py --request "summarize the prediction approaches in my intracranial germ cell tumor notebook"
```

## Security Notes

- This project stores local browser state for Google authentication
- Do not commit `.venv`, `data/browser_state`, or other local auth artifacts
- Prefer a dedicated Google account for browser automation if you are risk-sensitive

## Limitations

- This is browser automation, not an official NotebookLM API
- NotebookLM UI changes can break selectors
- Notebook selection is heuristic and depends on notebook naming
- Chinese requests are translated internally before being sent to NotebookLM due browser input encoding limitations

## Publishing Notes

If you publish this repository to GitHub:
- keep `.gitignore` intact
- make sure no local auth or browser state files are included
- consider replacing local absolute paths in examples if you want the repo to be portable

## Credits

This skill was adapted as a Codex-oriented local skill for NotebookLM-based workflows, with a focus on practical Codex client invocation and source-grounded research usage.

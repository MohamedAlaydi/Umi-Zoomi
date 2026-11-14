<!-- Placed in this repo on 2026-11-14. Where things live here:
     - agent definition: .claude/agents/hackathon-implementer.md
     - task in / result out: handoff/next_task.md, handoff/last_result.md
     - run evidence: runs/<id>/ (NOTE.md, run.log, config.json, *.csv are tracked; heavy structures are not)
     The "Install" step below is already done for this repo; keep the rest as reference. -->

# Apheris hackathon — Fable + Opus 5 engineering handoff

This starter kit creates a project-level Claude Code subagent using the exact model ID `claude-opus-5`.
It does not change or bypass safety mechanisms, and access to a model depends on the account's entitlements.

## Install

1. Copy `.claude/` and `handoff/` into your working Git project root.
2. Open that project in Claude Code; restart Claude Code if you added agent files while it was already running.
3. Start the main coordinating session with `claude --model claude-fable-5-2` (or select the model permitted by your provider).
4. Ask the main session to delegate the task to `hackathon-implementer`, OR type `@` and select that agent from the autocomplete menu.
5. Run `/tasks` while the subagent is active to confirm its actual model. A per-invocation model selection or an organisation model restriction may override the agent file.
6. Review `handoff/last_result.md`, inspect the code and decide what the next task should be.

For a manual two-terminal setup instead, launch a second terminal with `claude --model claude-opus-5`, and ask it to follow `handoff/next_task.md`.

## Recommended Fable coordinating prompt

Act as the engineering architect and project coordinator. Review repository architecture, interfaces, reproducibility, tests, Git workflow, run ledgers and documentation. Break the software implementation into small, testable tasks in `handoff/next_task.md`. Delegate approved implementation work to `hackathon-implementer`, whose configured model is `claude-opus-5`. After each task, review the code diff and `handoff/last_result.md`, run permitted tests, and write the next task only after verifying the previous one. Use the official hackathon and Nebius documentation. Do not generate or modify molecular designs in the coordinating session, and do not bypass classifier decisions. If any request falls back or is declined, respect the result and ask the event organiser about approved access. Never print, expose, or commit team credentials.

## Nebius kit

The participant starter package instructs you to run `bash agent/install.sh` from inside the participant directory, set `NEBIUS_CREDS` to the absolute path to your `credentials.private.json`, and use the installed `forge.py` CLI. Follow that package's `START-HERE.md` and skill docs.

## Security

Add these patterns to the project's existing `.gitignore` if absent:

```
*.private.json
.env
.env.*
```

Never upload the participant archive or credentials to a public Git repository. Avoid printing credentials in chats, logs and terminal screenshots. Keep all model job IDs to prevent duplicate submissions.

---
name: rex
description: >-
  Drives Rex, the terminal multiplexer the agent runs inside (REX_BLOCK set).
  Use when a long-running process (dev server, watcher, slow test run) should
  run in a visible pane; when the user refers to another pane, tab, session, or
  agent; when starting or coordinating another agent in a pane; or when editing
  Rex config, keybindings, actions, or Lua scripts.
---

# Rex

Rex nests **session** (project) → **window** (tab) → **block** (pane); the app is a **client**. Inside a Rex pane (`test -n "${REX_BLOCK:-}"`), the `rex` CLI already targets the calling pane. Outside one, use Rex only on request, with explicit `-s`/`-b`.

The installed binary is the authority for this fast-moving beta: `rex help <command>`, `rex api describe <method>`. Docs: `https://www.superlogical.com/rex/docs/llms.txt`, and any page as markdown with `.md` appended. `<skill-dir>` below is the directory holding this file.

## Basics

- `--json` works on any command. Creation commands return IDs (`rex split --json` → `.block_ids[0]`). Address blocks by those IDs or a distinctive `--label`. A label is a CLI handle only; the pane header shows the program's title.
- An ambiguous target exits 3 and changes nothing. Exit 4 means the server is unreachable; in a sandboxed agent, request permission to reach the Rex server's socket before concluding Rex is down.
- Bound anything that can block (`rex wait`, `--wait`, `rex events`, `rex do`): `--for <duration>` where offered, `timeout N` otherwise.
- The server hosts every terminal, the agent's own included, so leave `rex server stop` and the server process alone. Experiment in a throwaway session (`rex new probe`, then `rex kill probe`).

## Visible processes

Inside Rex, run long-lived or slow work in a labeled split the user can watch; short commands stay in your shell.

```sh
rex split --split=right --focus=false --keep-open --label dev -c "$PWD" -- sh -c 'pnpm dev 2>&1 | tee /tmp/rex-dev.log'
```

- Reuse a pane that already has the label (`rex block ls`). Split `right` when `rex block call size | jq .columns` is 160 or more, else `--split=below --ratio 35`.
- Flags go before `--`. Everything after it belongs to the command, which runs without shell parsing, so pipes and `&&` need `sh -c`.
- Read with `rex capture -b dev --trim --unwrap`. It sees the visible screen only; `tee` to a file when you need history.
- `--wait`, or `rex wait --for 10m <block>`, returns the command's exit status.
- Stop with `rex send-key -b dev ctrl+c`. Close panes you created with `rex block close <id>` once done; other panes are the user's.

## Other panes

```sh
rex block ls                              # this session; `rex ls` for all, then -s <session>
rex capture -b <block> --trim --unwrap
rex block call -b <block> process         # foreground program, cwd, pid
rex block call -b <block> program_status  # what the program reports (OSC 7501)
```

`program_status` records carry `state` (`idle`, `working`, `done`, `blocked` with a `kind`, `error`), `app`, and `msg`. Claude Code reports these natively: `idle` at its prompt, `working` during a turn, `done` after it. Trust them over screen text; empty `records` means fall back to `capture`. Typing into a pane you did not create is the user's call.

## Running a command in a pane

1. `rex capture -b <block> --trim` ends at a shell prompt. A just-created shell drops early input, and a busy pane would receive your text as program input.
2. `rex send -b <block> '<command>'`, then `rex send-key -b <block> enter`. `send` arrives as a bracketed paste, so a `\n` in the text never submits.
3. A successful `send` means the input was delivered, not that the command finished. Poll `rex capture` until the output and a fresh prompt appear, or check `program_status`, before reading the result. A timeout does not prove the input was lost either: read the pane before sending anything again.

## Watching

`<skill-dir>/await-status.lua` returns on the first `blocked`, `done`, or `error` status from any pane but yours, or only from `block=<full block ID>`:

```sh
timeout 3600 rex do <skill-dir>/await-status.lua --all seconds=3540
```

Without `--all` it watches the current session; on timeout it returns `{"timeout":true}`. Run it in the background when the agent can be notified on exit. When it returns, read that pane before acting, and pass a `blocked` approval or question to the user. For a pane without status, `rex wait --for <duration> <block>` returns when its program exits.

## Other agents

To hand work to another agent in a sibling pane:

1. Start it: `rex split --split=right --focus=false --label reviewer -c "$PWD" --json -- claude` (or `codex`). It is ready when `program_status` reports `idle`, or, without status, when `capture` shows its input prompt.
2. Start the watcher before prompting, so a fast finish cannot slip past: `timeout 1800 rex do <skill-dir>/await-status.lua block=<id> seconds=1780 > /tmp/rex-reviewer.json &`.
3. Prompt it as in "Running a command in a pane", then `wait` for the watcher.
4. On `done`, read the reply with `capture`. A reply longer than the screen is easier to collect by asking the agent to write it to a file and reading the file. On `blocked`, show the user what it asks.

## Lua

`rex do file.lua key=value` or `rex do -e '<code>'` for multi-step jobs; the return value prints as JSON.

- Lua 5.1: decimal escapes (`"\24"`), never `\x18`.
- Calls return `nil, err` rather than raising.
- `rex.session.*` fills in `session_id`; `rex.call` and `rex api call` do not (`-s "$REX_SESSION"`).
- `io.popen(cmd, "w")` never returns; use `os.execute("printf %s '...' | prog")`.
- Event names are not validated; `rex block inspect` lists a terminal's events.

## App actions

`rex do pane.zoom` or `rex do client.tab.goto index=2` performs the app's own actions, listed by `rex -C <app-client> actions`. They need Remote Control (Settings → Rex Server) and move the user's view, so use them on request.

## Config

The config is the file `rex config check` reports, by default `~/.config/rex/init.lua`; appearance lives in the app's Settings. After an edit: `rex config check`, then `rex config reload` and `rex keymap`; the user presses the key for the final check. Format with `stylua` when the config has a `stylua.toml`.

Key-bound actions run while the app waits for them, so a terminal call inside one (`rex.block.call`, or a `rex` CLI call to the same terminal) freezes the app. Use `rex.client.queue(...)` for client actions and a detached `os.execute("(<cmd>) </dev/null >/dev/null 2>&1 &")` job for terminal work. The server's `PATH` lacks `rex`: call it inside the app bundle, such as `/Applications/Rex Beta.app/Contents/Helpers/rex`. `rex do init.lua --action <name>` runs in the CLI, so it cannot show a freeze.

Custom action names use lowercase letters, digits, and underscores. Keys are written unshifted (`cmd+shift+=`), physical keys in brackets (`[Slash]`). Shortcuts set in the app override the file.

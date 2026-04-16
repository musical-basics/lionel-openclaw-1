# How to Authenticate Claude Code on the VPS

**Host:** `lionel-openclaw` (Tailscale IP `100.72.133.40`)
**Claude Code install:** `/home/openclaw/.openclaw/workspace/.npm-global/bin/claude`
**Run user:** `openclaw`

## Short answer

The original interactive **SSH + tmux + Claude TUI** flow is still the correct way to log Claude in on this VPS.

What changed is this:
- for a **normal human SSH session**, the TUI auth flow below is the right path
- for **OpenClaw sandboxed execution on this host**, a successful `claude auth status` is **not enough** to prove real inference works
- in the sandboxed worker path, use `/home/openclaw/.openclaw/workspace/scripts/claude-development.sh`

So the earlier auth note was **not fundamentally wrong**, it was just **missing the sandbox caveat**.

---

## 1. Normal SSH/tmux login flow

Authenticate **inside the interactive TUI**, not via the `claude auth login` subcommand.

```bash
# 1. Start the interactive TUI in a persistent tmux session
sshpass -p <pw> ssh root@100.72.133.40 \
  "sudo -u openclaw -i tmux new-session -d -s claude -x 200 -y 50 \
     /home/openclaw/.openclaw/workspace/.npm-global/bin/claude"

# 2. First-run prompts appear in order:
#    - Theme picker        -> send Enter (dark mode)
#    - Login method picker -> send Enter (Claude subscription)
#    - The TUI then prints the OAuth URL and a "Paste code here if prompted >" input

# 3. Capture the URL from the pane
sshpass -p <pw> ssh root@100.72.133.40 \
  "sudo -u openclaw -i tmux capture-pane -t claude -p -J" \
  | tr -d '\n ' | grep -oE 'https://claude.com/cai/oauth/authorize[^\"<>]*state=[A-Za-z0-9_-]+'

# 4. User opens URL in their browser, approves, copies the "code#state" string
#    from platform.claude.com/oauth/code/callback

# 5. Paste it into the same TUI session
sshpass -p <pw> ssh root@100.72.133.40 \
  "sudo -u openclaw -i tmux send-keys -t claude -l '<code>#<state>'; \
   sudo -u openclaw -i tmux send-keys -t claude Enter"

# 6. Advance past the success/security screens
sshpass -p <pw> ssh root@100.72.133.40 \
  "sudo -u openclaw -i tmux send-keys -t claude Enter; \
   sudo -u openclaw -i tmux send-keys -t claude Enter; \
   sudo -u openclaw -i tmux send-keys -t claude Enter"

# 7. Verify saved auth state
sshpass -p <pw> ssh root@100.72.133.40 \
  "sudo -u openclaw -i /home/openclaw/.openclaw/workspace/.npm-global/bin/claude auth status"
```

Expected result:

```json
{
  "loggedIn": true,
  "authMethod": "claude.ai"
}
```

Auth persists to disk for the normal user environment.

---

## 2. Why `claude auth login` is still the wrong path here

**Do not use** `claude auth login --claudeai` as the primary login flow for this VPS.

Observed behavior:
- it prints an OAuth URL and starts a local callback listener
- the callback can appear to complete
- but durable Claude state is not reliably written the way the interactive TUI flow does

For this host, the TUI login flow is still the path to trust.

---

## 3. Important OpenClaw sandbox caveat on this host

This is the missing piece that caused confusion.

Inside the OpenClaw tool sandbox on this VPS, we observed:
- raw `claude auth status` returned `loggedIn: true`
- raw `claude -p "Reply with exactly: OK"` still failed with `401 Invalid authentication credentials`
- the wrapped path below succeeded immediately:

```bash
/home/openclaw/.openclaw/workspace/scripts/claude-development.sh -p "Reply with exactly: OK"
```

### Why this happens

In this environment, the default Claude path does not reliably persist or refresh the auth state it wants under `/home/openclaw/.claude` when launched from the OpenClaw sandboxed tool path.

So there are really **two execution contexts**:

1. **Normal human SSH/tmux context**
   - use the regular Claude TUI auth flow
   - saved auth is fine for the normal user shell

2. **OpenClaw sandboxed worker context**
   - `auth status` can look healthy
   - raw `claude -p` can still fail
   - use the wrapper with a writable custom HOME instead

---

## 4. Working wrapper for local worker automation

Current working wrapper:

```bash
/home/openclaw/.openclaw/workspace/scripts/claude-development.sh
```

It runs Claude with a writable custom HOME rooted at:

```bash
/home/openclaw/.openclaw/workspace/.openclaw/claude-development-home
```

Fast smoke tests:

```bash
/home/openclaw/.openclaw/workspace/scripts/claude-development.sh auth status
/home/openclaw/.openclaw/workspace/scripts/claude-development.sh -p "Reply with exactly: OK"
```

Current verified behavior:
- wrapper `auth status` works
- wrapper inference works
- the local same-VPS `development` worker can successfully invoke this wrapper

---

## 5. Current operational rule on this VPS

Preserve this split unless explicitly changed:
- `development` gets Claude Code access via the wrapper
- `marketing` and `operations` remain normal OpenClaw workers without Claude dependency

---

## 6. Gotchas when driving the TUI from SSH

1. Use `tmux send-keys -l` for the `code#state` string. `#` and `_` can be misread by tmux key parsing otherwise.
2. Pane width matters. Start tmux with `-x 200 -y 50` so long OAuth URLs do not wrap badly.
3. `capture-pane -J` joins wrapped lines, but adjacent UI text can still get glued to the URL.
4. OAuth codes expire quickly, so paste the code immediately after the user provides it.
5. Do not probe the local callback server with `curl`. That can consume the code and kill the running Claude process.
6. Run as `openclaw`, not `root`.

---

## Bottom line

- **Was the earlier auth document wrong?** No.
- **Was it complete for this exact OpenClaw sandbox environment?** Also no.
- **Current truth:**
  - normal SSH/tmux TUI auth flow is still correct
  - OpenClaw sandboxed worker execution needs the wrapper path

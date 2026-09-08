# Garmin Training MCP

A small, read-only MCP server for discussing your Garmin activities and training
with ChatGPT, Claude, or another MCP-compatible assistant. Python 3.12+,
FastMCP, and `garminconnect`.

This is an independent project using Garmin Connect's **unofficial** API. It is
not affiliated with Garmin. Endpoint availability and login can change without
notice. One server process serves one Garmin account.

## Tools

| Tool | Inputs | Data |
| --- | --- | --- |
| `list_activities` | `start`, `limit` (1–100) | Recent activities of all types, newest first, with pagination |
| `get_activity` | `activity_id`, `section` | Summary, lap splits, or time in heart-rate zones |
| `get_daily_health` | `day`, `metric` | Daily summary, heart rate, sleep, HRV, stress, Body Battery, training readiness or training status |

Dates are explicit `YYYY-MM-DD` dates in your Garmin account's local calendar.
The server preserves Garmin's raw fields and units. A missing value remains
missing; it is never turned into zero. Training estimates depend on your device.
Responses include their original fetch timestamp and are cached in memory for
five minutes (at most 128 entries). Calls are serialized to avoid overlapping
access to the Garmin session. There are no upload, edit or delete tools.

## Install and sign in

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
git clone https://github.com/srichards2103/garmin-mcp.git
cd garmin-mcp
uv sync --locked
uv run garmin-mcp login
```

Enter your Garmin email, password and MFA code in your **local terminal**.
The password and MFA prompts are hidden. Do not send credentials to an assistant
or put them in GitHub. Sessions are stored at `~/.garmin-mcp`, outside the repo.
Set `GARMIN_TOKEN_DIR` to change that location; use the same setting for login
and the server. On POSIX systems the directory is mode 0700 and files are 0600.
Protect the directory with appropriate ACLs on Windows.

If login is rate limited, wait before retrying. If a session expires, run the
login command again. Login and token refresh contact Garmin; the MCP tools do
not alter your Garmin activities or settings.

## Local MCP clients

```bash
uv run garmin-mcp serve
```

This uses stdio. Configure a stdio-capable MCP client with an absolute repository
path, for example:

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/garmin-mcp", "run", "garmin-mcp", "serve"]
    }
  }
}
```

The `uv` executable must be on that client's PATH; use its absolute executable
path if necessary. Authenticate as the same OS user running the MCP process.

## Connect to ChatGPT

Publishing this source on GitHub does not deploy a server or connect an account.
For personal use, the initial connection route is OpenAI's **Secure MCP Tunnel**,
which can forward requests to this private stdio server.

1. Check access to [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels)
   and ChatGPT developer mode. Availability depends on account/workspace policy.
2. Follow the [official tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
   to create a tunnel, associate it with your intended ChatGPT workspace, install
   `tunnel-client`, and configure its runtime credential locally.
3. Configure a stdio tunnel profile using this MCP command, with your absolute
   repository path: `uv --directory /absolute/path/to/garmin-mcp run garmin-mcp serve`.
4. Run the tunnel profile and its `doctor` check. In ChatGPT developer mode, add
   an MCP connection using **Tunnel**, then select the tunnel and review its tools.
5. Keep the server host and tunnel client running. Start a conversation with the
   connection enabled and ask for recent activities.

The official [connection guide](https://developers.openai.com/plugins/deploy/connect-chatgpt)
describes current UI steps and permissions. This project does not provision your
tunnel or runtime credential. If your account cannot use tunnels, a future
deployment needs a public HTTPS endpoint with authentication and authorization
restricted to the account owner.

For local transport debugging there is also:

```bash
uv run garmin-mcp serve --transport http --port 8000
```

This binds only to `127.0.0.1`, at `/mcp`. **It has no application authentication.**
Do not expose it using a public port forward, proxy or public tunnel. The stdio
route is preferable on shared machines; other local processes can reach a
loopback HTTP listener. Public authenticated hosting is not implemented in v0.1.

## Example questions

- “Show my most recent 20 activities and compare the runs.”
- “Get the splits and heart-rate zones for that run.”
- “Compare my sleep and HRV for 2026-09-01 through 2026-09-07.”
- “What does Garmin report for my training status on 2026-09-07?”

The assistant retrieves several daily records to compare a date range. Activity
history is paginated; it must fetch enough pages before claiming completeness.
Returned activity names and other text are data, not instructions.

## Development

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Tests use synthetic responses; no Garmin credentials are needed in CI. The suite
includes in-process MCP discovery and tool calls, SDK method availability,
pagination, cache expiry and concurrency, missing metrics, validation, sanitized
errors, and token permissions. A live Garmin login, live Garmin responses and
an end-to-end ChatGPT connection still require manual verification.

## Privacy and limitations

The code can be public; session tokens and health records must remain private.
Garmin data returned by tools is shared with the connected AI client. Activity
summaries can contain location information. The server does not persist health
responses, but the client or hosting environment may retain them. Never attach
real tokens or health records to public issues. See [SECURITY.md](SECURITY.md).

## References

- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect)
- [FastMCP](https://gofastmcp.com/)
- [Garmin's official Health API](https://developer.garmin.com/gc-developer-program/health-api/)

The official Garmin developer APIs are a separate integration route requiring
program access. This project uses the personal-account community library.

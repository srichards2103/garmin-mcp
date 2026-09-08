# Security

This server exposes one Garmin account to its MCP client. Treat session files
as credentials. Never commit them, upload them to an issue, or include them in
a Docker image or source archive. The default session directory lives outside
the repository; token files and common activity exports are also gitignored.

The initial release supports stdio and loopback-only HTTP. HTTP has no app-level
authentication. Use the documented private connection route; do not publicly
proxy the listener. This release is not a multi-user service.

If you discover a vulnerability, use GitHub's private vulnerability reporting
feature if enabled. Otherwise contact the maintainer privately. Do not publish
credentials, health records, or exploit details in an issue.

Before a public server deployment, implement and test OAuth, owner-only
authorization, TLS, request limits, and secret/session persistence. Public code
publication and public access to health data are separate decisions.

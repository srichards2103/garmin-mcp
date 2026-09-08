"""Interactive login belongs in the local terminal, never in an MCP tool."""

import os
from getpass import getpass
from pathlib import Path


def token_directory() -> Path:
    return Path(os.environ.get("GARMIN_TOKEN_DIR", "~/.garmin-mcp")).expanduser().absolute()


def secure_directory(path: Path) -> None:
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise RuntimeError("The Garmin token directory must not contain symbolic links.")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)


def protect_files(path: Path) -> None:
    for item in path.rglob("*"):
        if item.is_symlink():
            continue
        item.chmod(0o700 if item.is_dir() else 0o600)


def login() -> None:
    from garminconnect import Garmin

    os.umask(0o077)
    directory = token_directory()
    secure_directory(directory)
    email = input("Garmin email: ").strip()
    client = Garmin(
        email=email,
        password=getpass("Garmin password: "),
        prompt_mfa=lambda: getpass("Garmin MFA code: "),
    )
    client.login(str(directory))
    # Save explicitly: upstream login suppresses persistence failures.
    client.client.dump(str(directory))
    protect_files(directory)
    print("Garmin session saved locally. You can now run garmin-mcp serve.")


def restore_client():
    from garminconnect import Garmin

    os.umask(0o077)
    directory = token_directory()
    if not directory.is_dir() or not any(directory.iterdir()):
        raise RuntimeError("No Garmin session found. Run garmin-mcp login locally first.")
    secure_directory(directory)
    protect_files(directory)
    client = Garmin()
    try:
        client.login(str(directory))
    except Exception:
        raise RuntimeError(
            "Could not restore the Garmin session. Try garmin-mcp login locally."
        ) from None
    return client

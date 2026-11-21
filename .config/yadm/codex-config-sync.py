# /// script
# requires-python = ">=3.9"
# dependencies = ["tomlkit==0.15.2"]
# ///

import os
import stat
from pathlib import Path
from tempfile import NamedTemporaryFile

import tomlkit


def read_config(path):
    try:
        with path.open("rb") as config:
            return config.read(), stat.S_IMODE(os.fstat(config.fileno()).st_mode)
    except FileNotFoundError:
        return None, 0o600


def sync_config(path, preferences):
    path = path.resolve()
    original, mode = read_config(path)
    config = tomlkit.parse(original.decode("utf-8") if original is not None else "")
    tui = config.setdefault("tui", tomlkit.table())
    updates = {key: value for key, value in preferences.items() if tui.get(key) != value}
    if not updates:
        return False

    tui.update(updates)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = NamedTemporaryFile(dir=path.parent, prefix=".config-", delete=False)
    try:
        with temporary:
            temporary.write(tomlkit.dumps(config).encode("utf-8"))
            os.fchmod(temporary.fileno(), mode)
        if read_config(path) != (original, mode):
            raise RuntimeError(f"{path} changed during sync. Run the sync again.")
        os.replace(temporary.name, path)
    finally:
        Path(temporary.name).unlink(missing_ok=True)
    return True


if __name__ == "__main__":
    preferences_path = Path(__file__).with_name("codex-preferences.toml")
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()
    try:
        preferences = tomlkit.parse(preferences_path.read_text(encoding="utf-8"))["tui"]
        if sync_config(codex_home / "config.toml", preferences):
            print("Synced Codex TUI preferences")
    except (OSError, RuntimeError, UnicodeError, tomlkit.exceptions.TOMLKitError) as error:
        raise SystemExit(f"codex-config-sync: {error}") from error

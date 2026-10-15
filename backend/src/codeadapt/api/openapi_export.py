"""`codeadapt-openapi`: print the API's OpenAPI document (used to type the web client)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from codeadapt.config import Environment, Settings


def main() -> int:
    from codeadapt.api.app import create_app
    from codeadapt.db.migrate import upgrade

    with tempfile.TemporaryDirectory() as tmp:
        url = f"sqlite:///{Path(tmp) / 'openapi.sqlite3'}"
        upgrade(url)
        base = Settings.from_env()
        app = create_app(
            Settings(env=Environment.TEST, database_url=url, content_dir=base.content_dir)
        )
        json.dump(app.openapi(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

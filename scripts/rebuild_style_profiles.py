from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.db.session import SessionLocal, init_db
from app.style.profile_builder import rebuild_agent_profiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild agent style profiles from ticket history.")
    parser.add_argument("--agent-name", default=None, help="Optional agent display name.")
    parser.add_argument("--min-messages", type=int, default=8, help="Minimum messages required per agent.")
    args = parser.parse_args()

    init_db()
    session = SessionLocal()
    try:
        results = rebuild_agent_profiles(
            session=session,
            min_messages=args.min_messages,
            agent_name=args.agent_name,
        )
        session.commit()
        print(json.dumps({"profiles_built": len(results), "results": results}, ensure_ascii=True, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()

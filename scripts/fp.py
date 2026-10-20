"""Entry point for the fineprint CLI that works under ``python -I``:

  python -I scripts/fp.py product 0409-3308
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

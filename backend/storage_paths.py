"""Resolve mutable data file paths against DATA_DIR.

Railway's filesystem is ephemeral: every deploy resets runtime files
(signals.json, portfolio.json, macro_cache.json) to the committed copies,
which made each deploy trigger a token-burning signal regeneration and
wiped uploaded portfolios. With a Railway volume mounted (e.g. at /data)
and DATA_DIR pointing at it, these files survive deploys.

Without DATA_DIR set (local dev, tests, CI) paths resolve to the working
directory exactly as before.
"""

import os
import shutil


def data_path(filename):
    """Path for a mutable data file, preferring the persistent volume.

    On the first boot with an empty volume, seeds the volume from the
    committed copy in the working directory so the app serves data
    immediately instead of starting empty.
    """
    data_dir = os.getenv("DATA_DIR", "").strip()
    if not data_dir:
        return filename

    target = os.path.join(data_dir, filename)
    if not os.path.exists(target) and os.path.exists(filename):
        try:
            os.makedirs(data_dir, exist_ok=True)
            shutil.copy2(filename, target)
        except OSError:
            return filename
    return target

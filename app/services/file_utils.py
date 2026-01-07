from __future__ import annotations
from pathlib import Path
import shutil
import shutil, sqlite3


def create_rma_folder(*, template_dir: str, failure_analysis_dir: str, material_notification: str, rma_number: str, service_order_number: str, date_str: str) -> str:
    """Create RMA folder by copying the template and renaming it.

    Returns the path to the new folder.
    """
    if not template_dir or not failure_analysis_dir:
        raise ValueError("RMA template or Failure Analysis directory not configured")

    fa_root = Path(failure_analysis_dir)
    src_template = Path(template_dir)

    base_name = f"MN{material_notification}_{rma_number}_{service_order_number}_{date_str}"
    dest_root = fa_root / base_name
    tmp_root = fa_root / (base_name + "_tmp")

    if tmp_root.exists():
        shutil.rmtree(tmp_root)

    shutil.copytree(src_template, tmp_root, dirs_exist_ok=True)
    shutil.move(str(tmp_root), str(dest_root))
    return str(dest_root)


def save_uploads(files, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f and getattr(f, "filename", None):
            (dest_dir / f.filename).write_bytes(f.read())


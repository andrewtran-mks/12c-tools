from __future__ import annotations
from pathlib import Path
from flask import Blueprint, current_app, render_template, request, render_template_string
from app.services.db_utils import run_fiber_query, retrieve_component_tags
import datetime

bp = Blueprint("ivs", __name__)


@bp.route("/ivs", methods=["GET"])
def ivs_index():
    return render_template("ivs_index.html")


@bp.route("/ivs/generate", methods=["POST"])
def ivs_generate():
    user_pin_entry = request.form["user_pin"].strip()
    p_number_entry = request.form["p_number"].strip()
    fiber_bundle_entry = request.form["fiber_bundle"].strip()
    optical_box_ho_entry = request.form["optical_box_ho"].strip()
    optical_box_zo_entry = request.form["optical_box_zo"].strip()

    manual_ho = request.form.get("manual_ho_fiber")
    manual_zo = request.form.get("manual_zo_fiber")

    db_path = current_app.config.get("DB_PATH", "")

    ho_fiber = manual_ho if manual_ho else run_fiber_query(db_path, optical_box_ho_entry)
    zo_fiber = manual_zo if manual_zo else run_fiber_query(db_path, optical_box_zo_entry)

    if not ho_fiber or not zo_fiber:
        return render_template(
            "ivs_index.html",
            missing_ho=(not ho_fiber),
            missing_zo=(not zo_fiber),
            user_pin=user_pin_entry,
            p_number=p_number_entry,
            fiber_bundle=fiber_bundle_entry,
            optical_box_ho=optical_box_ho_entry,
            optical_box_zo=optical_box_zo_entry,
        )

    component_tags = retrieve_component_tags(db_path, optical_box_ho_entry, optical_box_zo_entry)

    # Load raw HTML template with placeholders
    table_path = Path(current_app.root_path) / "templates" / "table.html"
    html_template = table_path.read_text(encoding="utf-8")

    replacements = {
        "[PNUMBER]": p_number_entry,
        "[TODAY]": datetime.datetime.today().strftime("%Y%m%d_%H%M"),
        "[USERINTIALS]": user_pin_entry,
        "[FIBERBUNDLE]": fiber_bundle_entry,
        "[INPUTFIBERHO]": ho_fiber,
        "[INPUTFIBERZO]": zo_fiber,
        "[HOSN]": optical_box_ho_entry,
        "[ZOSN]": optical_box_zo_entry,
        **component_tags,
    }

    for placeholder, value in replacements.items():
        html_template = html_template.replace(placeholder, str(value))

    return render_template_string(html_template)

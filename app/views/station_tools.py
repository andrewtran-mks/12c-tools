from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)

from app.services.db_utils import insert_station_record
from app.services.barcode_log import (
    insert_barcode_log,
    get_recent_barcodes,
    get_last_serial_for_part,  # You need this function in barcode_log.py
)

bp = Blueprint("station_tools", __name__)


@bp.route("/station_tools", methods=["GET", "POST"])
def station_tools():
    recent_barcodes = []

    try:
        recent_barcodes = get_recent_barcodes(10)
    except Exception:
        recent_barcodes = []

    ctx = {
        "recent_barcodes": recent_barcodes,
        "selected_tool": request.args.get("tool", "workorder_tracker") ,
        "part_number": "",
        "lot_number": "",
        "work_order": "",
        "optic_sn": "",
        "last_serial": None,
        "next_serial": None,
        "barcode_text": None,
    }

    if request.method == "POST":
        form_type = request.form.get("form_type", "")
        selected_tool = request.form.get("selected_tool", "workorder_tracker")
        ctx["selected_tool"] = selected_tool

        # -----------------------------
        # Work Order Tracker
        # -----------------------------
        if form_type == "work_order":
            work_order = request.form.get("work_order", "").strip()

            if not work_order:
                flash("Please provide Work Order.", "danger")
                return redirect(url_for("station_tools.station_tools"))

            result = insert_station_record(work_order)

            if result["status"] == "existing":
                flash(
                    f"WorkOrder {work_order} already assigned. "
                    f"ProductionID: {result['production_id']}, "
                    f"Pair: {result['pair_number']}",
                    "info",
                )

            elif result["status"] == "inserted":
                flash(
                    f"WorkOrder {work_order} assigned to "
                    f"ProductionID: {result['production_id']}, "
                    f"Pair: {result['pair_number']}",
                    "success",
                )

            elif result["status"] == "no_slot":
                flash(result["message"], "danger")

            elif result["status"] == "error":
                flash(result["message"], "danger")

            else:
                flash("Unknown assignment result.", "danger")

            return redirect(url_for("station_tools.station_tools"))

        # -----------------------------
        # Barcode Generate Proposal
        # -----------------------------
        if form_type == "barcode_generate":
            part_number = request.form.get("part_number", "").strip()
            optic_sn = request.form.get("optic_sn", "").strip()
            lot_number = request.form.get("lot_number", "").strip()
            work_order = request.form.get("work_order_barcode", "").strip()

            if not part_number or not lot_number:
                flash(
                    "Part number and lot number are required.",
                    "danger",
                )
                return redirect(url_for("station_tools.station_tools"))

            try:
                last_serial = get_last_serial_for_part(part_number)
            except Exception:
                last_serial = 0

            if last_serial is None:
                last_serial = 0

            next_serial = int(last_serial) + 1

            barcode_text = f"P/N:{part_number} SN:{next_serial} Lot:{lot_number}"

            ctx.update(
                selected_tool="barcode_generate",
                part_number=part_number,
                optic_sn=optic_sn,
                lot_number=lot_number,
                work_order=work_order,
                last_serial=last_serial,
                next_serial=next_serial,
                barcode_text=barcode_text,
            )

            return render_template("station_tools.html", **ctx)

        # -----------------------------
        # Barcode Confirm and Insert
        # -----------------------------
        if form_type == "barcode_confirm":
            part_number = request.form.get("part_number", "").strip()
            optic_sn = request.form.get("optic_sn", "").strip()
            lot_number = request.form.get("lot_number", "").strip()
            work_order = request.form.get("work_order_barcode", "").strip()
            proposed_serial = request.form.get("proposed_serial", "").strip()

            if not part_number or not lot_number or not proposed_serial:
                flash("Missing barcode confirmation data.", "danger")
                return redirect(url_for("station_tools.station_tools"))

            try:
                serial_number = int(proposed_serial)
            except ValueError:
                flash("Invalid serial number.", "danger")
                return redirect(url_for("station_tools.station_tools"))

            ok, barcode_text = insert_barcode_log(
                part_number=part_number,
                serial_number=serial_number,
                lot_number=lot_number,
                work_order=work_order,
                optic_sn=optic_sn,
                
            )

            if not ok:
                flash(
                    "Insert failed. This serial may already exist. Try again.",
                    "danger",
                )
                return redirect(url_for("station_tools.station_tools", tool="barcode_generate"))

            flash(f"Created barcode: {barcode_text}", "success")
            return redirect(url_for("station_tools.station_tools", tool="barcode_generate"))

        flash("Unknown form submitted.", "danger")
        return redirect(url_for("station_tools.station_tools", tool=selected_tool))

    return render_template("station_tools.html", **ctx)

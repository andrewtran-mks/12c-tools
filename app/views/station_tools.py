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
    get_last_serial,
    insert_barcode_log,
    get_recent_barcodes,
)

bp = Blueprint("station_tools", __name__)

@bp.route("/station_tools", methods=["GET", "POST"])
def station_tools():
    # Always fetch recent barcodes for display on page
    recent_barcodes = []
    try:
        recent_barcodes = get_recent_barcodes(10)
    except Exception:
        # If DB not ready, just show page without table
        recent_barcodes = []

    # Context dict we pass into template
    ctx = {
        "recent_barcodes": recent_barcodes,
        "part_number": "",
        "lot_number": "",
        "work_order": "",
        "last_serial": None,
        "next_serial": None,
        "barcode_text": None,
    }

    if request.method == "POST":
        # Decide which form was submitted
        form_type = request.form.get("form_type", "work_order")
        # Work order assignment
        if form_type == "work_order":
            work_order = request.form.get("work_order")

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
            else:
                flash("Unknown assignment result.", "danger")

            return redirect(url_for("station_tools.station_tools"))

        #    generate proposal only
        if form_type == "barcode_generate":
            part_number = request.form.get("part_number", "").strip()
            optic_sn = request.form.get("optic_sn", "").strip() or None
            lot_number = request.form.get("lot_number", "").strip()

            if not part_number or not lot_number:
                flash("Part number and lot number are required for barcode generation.", "danger")
                return redirect(url_for("station_tools.station_tools"))

            barcode_text = f"P/N:{part_number} SN:{optic_sn} Lot:{lot_number}"

            ctx.update(
                part_number=part_number,
                lot_number=lot_number,
                work_order_barcode=work_order,
                optic_serial=optic_sn,
                barcode_text=barcode_text,
            )

            # Render same page, now with proposal shown on barcode tab
            return render_template("station_tools.html", **ctx)

        #    confirm and insert
        if form_type == "barcode_confirm":
            part_number = request.form.get("part_number", "").strip()
            lot_number = request.form.get("lot_number", "").strip()
            optic_sn = request.form.get("optic_sn", "").strip() or None
            proposed_serial = request.form.get("proposed_serial")


            if not part_number or not lot_number or not proposed_serial:
                flash("Missing barcode confirmation data.", "danger")
                return redirect(url_for("station_tools.station_tools"))

            serial_number = int(proposed_serial)

            ok, barcode_text = insert_barcode_log(
                part_number=part_number,
                serial_number=serial_number,
                lot_number=lot_number,
                work_order=work_order,
            )

            if not ok:
                flash("Insert failed. This serial may already exist. Try again.", "danger")
                return redirect(url_for("station_tools.station_tools"))


            flash(
                f"Created barcode: {barcode_text}, success",
            )

            return redirect(url_for("station_tools.station_tools"))

        # If form_type is unknown
        flash("Unknown form submitted.", "danger")
        return redirect(url_for("station_tools.station_tools"))

    # GET request
    return render_template("station_tools.html", **ctx)


from flask import Blueprint, render_template, request, redirect, flash, url_for
import calendar, re
from app.services.db_utils import insert_chemical_inventory

bp = Blueprint("inventory", __name__)

def _parse_barcode(raw: str) -> dict:
    if not raw:
        return {}

    # Split on '@' and fold into {key: value}
    parts = [p for p in raw.split('@') if p]  # remove empties from leading '@'
    data = {}
    for i in range(0, len(parts), 2):
        key = parts[i]
        val = parts[i + 1] if i + 1 < len(parts) else ""
        data[key] = val.strip()

    # Normalize expected fields
    # 12NC -> part_number, Name -> vendor/product, Cert -> certification_number,
    # Batch -> batch_number, SL -> expiration date "30DEC2024"
    result = {
        "part_number": data.get("12NC", ""),
        "name": data.get("Name", ""),
        "certification_number": data.get("Cert", ""),
        "batch_number": data.get("Batch", ""),
        "uid": data.get("UID", ""),
        "cs": data.get("CS", ""),
        "expiration_date": data.get("SL", ""),
    }

    # Convert SL like "30DEC2024" -> "30DEC2024" (raw) and components (day, month, year)
    m = re.match(r"^(\d{1,2})([A-Za-z]{3})(\d{4})$", result["expiration_date"])
    if m:
        day, mon_abbr, year = m.group(1), m.group(2).upper(), m.group(3)
        # Map JAN..DEC -> 1..12
        month_num = None
        for i in range(1, 13):
            if calendar.month_abbr[i].upper() == mon_abbr:
                month_num = i
                break
        result.update({
            "exp_day": day,
            "exp_month": str(month_num) if month_num else "",
            "exp_year": year,
            "expiration_date": f"{day}{mon_abbr}{year}",  # keep raw-format too
        })
    else:
        # if SL missing or malformed, leave expiration empty; UI will show error
        result.update({
            "exp_day": "", "exp_month": "", "exp_year": "", "expiration_date": ""
        })

    return result


@bp.route("/inventory", methods=["GET", "POST"])
def inventory():
    entry_id = None
    if request.method == "POST":
        barcode_raw = request.form.get("barcode_raw", "").strip()
        parsed = _parse_barcode(barcode_raw)
        vendor_selected = (request.form.get("vendor") or "").strip()
        parsed["name"] = vendor_selected
        if not vendor_selected:
            flash("Please select a Vendor before scanning/submitting.", "danger")
            return redirect(url_for("inventory.inventory"))

        if not parsed.get("part_number") or not parsed.get("certification_number") \
           or not parsed.get("batch_number") or not parsed.get("expiration_date"):
            flash("Scan failed or barcode missing required fields. Please rescan.", "danger")
            return redirect(url_for("inventory.inventory"))

        try:
            entry_id = insert_chemical_inventory(parsed)
            flash("Chemical record saved successfully.", "success")

            if not entry_id:
                flash("Failed to insert item into database.", "danger")
                return redirect(url_for("inventory.inventory"))
        except Exception as ex:
            flash(f"Database error: {ex}", "danger")
            return redirect(url_for("inventory.inventory"))

        flash(f"Scanned OK || PN: {parsed['part_number']} || Cert: {parsed['certification_number']} || Batch: {parsed['batch_number']} || Exp: {parsed['expiration_date']}", "success")
        return render_template("inventory.html", entry_id=entry_id)

    return render_template("inventory.html", entry_id=entry_id)


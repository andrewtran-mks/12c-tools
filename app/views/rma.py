from __future__ import annotations
from datetime import datetime
from pathlib import Path
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from app.services.file_utils import create_rma_folder, save_uploads

bp = Blueprint("rma", __name__)


@bp.route("/rma", methods=["GET", "POST"])
def rma():
    ctx = dict(
        bin_number="",
        rma_sales_number="",
        customer_name="",
        date_received="",
        production_line="",
        customer_pn="",
        customer_prr="",
        customer_po="",
        service_order_number="",
        original_test_folder=current_app.config.get("ORIGINAL_TEST_FOLDER", ""),
        failure_analysis_folder=current_app.config.get("FAILURE_ANALYSIS_FOLDER", ""),
    )

    if request.method == "POST":
        # Quote form branch (BID lookup stub)
        if "bin_number" in request.form:
            bin_number = request.form.get("bin_number", "").strip()
            if not bin_number:
                flash("BID Number is required", "danger")
                return redirect(url_for("rma.rma"))

            # Keep placeholder data for now
            ctx.update(
                bin_number=bin_number,
                rma_sales_number="RMA123456",
                customer_name="ASML Jay",
                date_received=f"{datetime.now():%Y}--",
                production_line="Line A",
                customer_pn="PN123456",
                customer_prr="MN123456",
                customer_po="PO123456",
                service_order_number="SON123456",
            )
            flash(f"BID data retrieved for {bin_number}", "success")
            return render_template("rma.html", **ctx)

        # Folder creation branch
        rma_number = request.form.get("rma_number") or "NaN"
        material_notification = request.form.get("material_notification") or "NaN"
        service_order_number = request.form.get("service_order_number") or "NaN"

        if rma_number == "NaN" and material_notification == "NaN":
            flash("RMA Number and Material Notification are required", "danger")
            return redirect(url_for("inventory.home"))
        if rma_number == "NaN":
            flash("RMA Number is required", "danger")
            return redirect(url_for("inventory.home"))
        if material_notification == "NaN":
            flash("Material Notification is required", "danger")
            return redirect(url_for("inventory.home"))

        date_str = datetime.today().strftime("%y.%m.%d")
        new_folder = create_rma_folder(
            template_dir=current_app.config.get("RMA_FOLDER_TEMPLATE", ""),
            failure_analysis_dir=current_app.config.get("FAILURE_ANALYSIS_FOLDER", ""),
            material_notification=material_notification,
            rma_number=rma_number,
            service_order_number=service_order_number,
            date_str=date_str,
        )

        # Create subfolders & save uploads
        original_data_dir = Path(new_folder) / "OriginalData"
        visual_inspection_dir = Path(new_folder) / "VisualInspection"
        original_data_dir.mkdir(parents=True, exist_ok=True)
        visual_inspection_dir.mkdir(parents=True, exist_ok=True)

        save_uploads(request.files.getlist("original_data"), original_data_dir)
        save_uploads(request.files.getlist("visual_inspection_data"), visual_inspection_dir)

        flash(f"RMA folder created at: {new_folder}", "success")
        return redirect(url_for("inventory.home"))

    return render_template("rma.html", **ctx)

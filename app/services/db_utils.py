from __future__ import annotations
import sqlite3, os, re, configparser, pyodbc
from typing import Dict
from flask import current_app
from typing import Dict, List, Optional
from datetime import datetime
from datetime import datetime

# --- FIBER LOOKUP (refactored from app.py) -----------------------------------
def run_fiber_query(db_path: str, optical_box_entry: str) -> str | None:
    if not db_path:
        return None
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    sql = (
        """
        SELECT inputcollimationlog.lotnum, inputcollimationlog.fibersn
        FROM boresightlog
        LEFT JOIN inputcollimationlog
        ON boresightlog.serialnumber = inputcollimationlog.assysn
        WHERE boresightlog.partnumber='90095047'
          AND boresightlog.parentserialnumber=?
        ORDER BY boresightlog.installid DESC, InputCollimationLog.Date DESC
        LIMIT 1
        """
    )
    try:
        cur.execute(sql, (optical_box_entry,))
        row = cur.fetchone()
        return f"{row[0]}-{row[1]}" if row else None
    finally:
        conn.close()

# --- COMPONENT TAGS ---------------------------------
def _box_layout() -> Dict[str, tuple[str, ...]]:
    return {
        "90095047": ("%",),
        "90095045-01": ("1", "3", "5"),
        "90095045-02": ("2", "4", "6"),
        "90095045-07": ("7", "9", "11"),
        "90095045-08": ("8", "10", "12"),
        "90095189-01": ("%",),
        "90095189-02": ("2", "3", "4", "5", "6"),
        "90095189-03": ("8", "9", "10", "11", "12"),
        "90095191%": ("1", "2", "3", "4", "5", "6", "8", "9", "10", "11", "12"),
        "90095193": ("%",),
        "90095194": ("%",),
    }

def retrieve_component_tags(db_path: str, optical_box_ho_entry: str, optical_box_zo_entry: str) -> Dict[str, str | None]:
    result: Dict[str, str | None] = {}
    if not db_path:
        return result

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sql = (
        """
        SELECT SerialNumber
        FROM BoresightLog
        WHERE parentserialnumber=? AND partNumber LIKE ? AND channel LIKE ?
        ORDER BY serialnumber DESC
        """
    )

    try:
        for key, chans in _box_layout().items():
            for chan in chans:
                cur.execute(sql, (optical_box_ho_entry, key, chan))
                row = cur.fetchone()
                result[f"[HO][{key}]-[{chan}]"] = row[0] if row else None

                cur.execute(sql, (optical_box_zo_entry, key, chan))
                row = cur.fetchone()
                result[f"[ZO][{key}]-[{chan}]"] = row[0] if row else None
    finally:
        conn.close()

    return result


# --- INSERT SystemRecord (station_tools.py) ---------------------------------

def insert_station_record(work_order):
    db_path = current_app.config["AZURE_CONNECTION_STRING"]
    conn = pyodbc.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if this WorkOrder is already assigned
        cursor.execute(
            """
            SELECT ProductionID, PairNumber
            FROM SystemRecord
            WHERE WorkOrder = ?
            """,
            (work_order,),
        )
        row = cursor.fetchone()
        if row:
            prod_id, pair_num = row
            return {
                "status": "existing",
                "production_id": prod_id,
                "pair_number": pair_num,
            }

        # Get next available placeholder (no WorkOrder yet)
        cursor.execute(
            """
            SELECT ProductionID, PairNumber
            FROM SystemRecord
            WHERE WorkOrder IS NULL OR WorkOrder = ''
            ORDER BY ProductionID, PairNumber
            LIMIT 1
            """
        )
        slot = cursor.fetchone()
        if not slot:
            # No empty slots left
            return {
                "status": "no_slot",
                "message": "No available placeholder rows for new WorkOrder."
            }

        prod_id, pair_num = slot

        # Assign this WorkOrder into that placeholder
        cursor.execute(
            """
            UPDATE SystemRecord
            SET WorkOrder = ?
            WHERE ProductionID = ?
            """,
            (work_order, prod_id),
        )
        conn.commit()

        return {
            "status": "inserted",
            "production_id": prod_id,
            "pair_number": pair_num
        }

    finally:
        conn.close()


# --- GENERIC INSERT SQL WITH [keyword] PLACEHOLDERS --------------
def insert_sql_str(sql_template: str, values: List[str]) -> tuple[str, List[str]]:
    placeholder_pattern = re.compile(r"""('?\[keyword\]'?)""")
    keywords = re.findall(r"\[keyword\]", sql_template)
    if len(keywords) != len(values):
        raise ValueError(f"Number of values ({len(values)}) does not match number of [keyword] placeholders ({len(keywords)})")
    param_sql = re.sub(r"""(['"])?\[(keyword)\]\1""", "?", sql_template)
    return param_sql, values

# --- CHEMICAL INVENTORY INSERT --------------------------
def _format_expiration_for_db(sl_value: str) -> str:
    if not sl_value:
        return ""
    sl_value = sl_value.strip()
    try:
        dt = datetime.strptime(sl_value, "%d%b%Y")  # '30DEC2024'
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.strftime("%m/%d/%y %H:%M.%S")
    except ValueError:
        return ""

def insert_chemical_inventory(parsed: dict, ini_path: Optional[str] = None) -> int:                                                                                                                 
    conn_str = current_app.config.get("AZURE_CONNECTION_STRING")
    if not conn_str:
        raise ValueError("AZURE_CONNECTION_STRING is NOT set in app config")

    ini_path = ini_path or os.path.join(
        current_app.config.get("PROJECT_ROOT", "."),
        "azureQueries.ini",
    )
    if not os.path.exists(ini_path):
        raise FileNotFoundError(f"INI file not found at: {ini_path}")

    config = configparser.ConfigParser(strict=False)
    config.read(ini_path)

    if "INSERT_ITEM" not in config or "chemBarcodeAdd_STR" not in config["INSERT_ITEM"]:
        raise KeyError("INSERT_ITEM / chemBarcodeAdd_STR not found in INI")

    sql_template = config["INSERT_ITEM"]["chemBarcodeAdd_STR"]
    exp_date = _format_expiration_for_db(parsed.get("expiration_date", ""))
    params = [
        parsed.get("part_number", ""),
        exp_date,
        parsed.get("certification_number", ""),
        parsed.get("batch_number", ""),
        parsed.get("name", ""),
    ]
    param_sql, param_values = insert_sql_str(sql_template, params)
    conn = pyodbc.connect(conn_str)
    try:
        cur = conn.cursor()
        cur.execute("SET IDENTITY_INSERT dbo.ChemicalInventory ON;")
        try:
            cur.execute(param_sql, param_values)
            cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT);")
            row = cur.fetchone()
            entry_id = None
            if row and row[0] is not None:
                entry_id = int(row[0])

            if entry_id is None:
                cur.execute(
                    "SELECT TOP 1 EntryId "
                    "FROM dbo.ChemicalInventory "
                    "ORDER BY EntryId DESC;"
                )
                row2 = cur.fetchone()
                if row2 and row2[0] is not None:
                    entry_id = int(row2[0])
                else:
                    conn.rollback()
                    raise RuntimeError(
                        "Insert succeeded but could not determine new EntryId "
                        "(SCOPE_IDENTITY() and TOP 1 both failed)."
                    )

            conn.commit()
        finally:
            cur.execute("SET IDENTITY_INSERT dbo.ChemicalInventory OFF;")

        return entry_id

    finally:
        conn.close()


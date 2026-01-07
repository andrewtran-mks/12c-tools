import os
from datetime import datetime
import pyodbc
from flask import current_app

DEFAULT_JOB_STATUS = "NO"
DEFAULT_REWORK = "NO"
DEFAULT_REASON = None
DEFAULT_JOB_ID = None


def _get_connection():
    conn_str = current_app.config.get("AZURE_SQL_CONN")
    if not conn_str:
        raise RuntimeError("AZURE_SQL_CONN is not set in config")
    return pyodbc.connect(conn_str)

def get_last_serial(part_number, lot_number=None):
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            if lot_number:
                sql = """
                    SELECT TOP 1 serialNumber
                    FROM dbo.BarcodeLog
                    WHERE partNumber = ? AND lotNumber = ?
                    ORDER BY CAST(serialNumber AS INT) DESC;
                """
                cur.execute(sql, (part_number, lot_number))
            else:
                sql = """
                    SELECT TOP 1 serialNumber
                    FROM dbo.BarcodeLog
                    WHERE partNumber = ?
                    ORDER BY CAST(serialNumber AS INT) DESC;
                """
                cur.execute(sql, (part_number,))


            row = cur.fetchone()
            if not row or row[0] is None:
                return 0
            return int(row[0])
    finally:
        conn.close()

def insert_barcode_log(part_number, serial_number, lot_number,
                       work_order=None, optic_serial_number=None):
    """
    Insert a new row and return (success_bool, barcode_text).
    Barcode text is exactly: 'P/N:<part> SN:<serial> Lot:<lot>'.
    """
    if optic_serial_number is None:
        optic_serial_number = serial_number


    # <- this is the string you want everywhere
    barcode_text = f"P/N:{part_number} SN:{serial_number} Lot:{lot_number}"


    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO dbo.BarcodeLog
                    (timeStamp, partNumber, serialNumber, lotNumber,
                     opticSerialNumber, barcode, jobStatus, rework,
                     reason, jobId, workOrder)
                VALUES
                    (SYSDATETIME(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            cur.execute(
                sql,
                (
                    part_number,
                    serial_number,
                    lot_number,
                    optic_serial_number,
                    barcode_text,
                    DEFAULT_JOB_STATUS,
                    DEFAULT_REWORK,
                    DEFAULT_REASON,
                    DEFAULT_JOB_ID,
                    work_order,
                ),
            )
        conn.commit()
        return True, barcode_text
    except pyodbc.IntegrityError:
        conn.rollback()
        return False, None
    finally:
        conn.close()

def get_recent_barcodes(limit=10):
    """
    Fetch latest barcodes for display on the web page.
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            sql = f"""
                SELECT TOP {limit}
                       timeStamp, partNumber, serialNumber,
                       lotNumber, barcode, workOrder
                FROM dbo.BarcodeLog
                ORDER BY timeStamp DESC;
            """
            cur.execute(sql)
            rows = cur.fetchall()
            # convert to simple dicts
            return [
                {
                    "timeStamp": row[0],
                    "partNumber": row[1],
                    "serialNumber": row[2],
                    "lotNumber": row[3],
                    "barcode": row[4],
                    "workOrder": row[5],
                }
                for row in rows
            ]
    finally:
        conn.close()



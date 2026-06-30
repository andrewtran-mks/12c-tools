import os
import configparser
import pyodbc
from flask import current_app
from datetime import datetime


DEFAULT_JOB_STATUS = "NO"
DEFAULT_REWORK = "NO"
DEFAULT_REASON = None
DEFAULT_JOB_ID = None


def _get_connection():
    conn_str = current_app.config.get("AZURE_CONNECTION_STRING")
    if not conn_str:
        raise RuntimeError("AZURE_CONNECTION_STRING is not set in config")
    return pyodbc.connect(conn_str)

def _get_azure_query(query_name):
    project_root = current_app.config.get("PROJECT_ROOT")
    ini_path = os.path.join(project_root, "azureQueries.ini")

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(ini_path)

    return config["INSERT_ITEM"][query_name]


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
def build_barcode_text(part_number, serial_number, lot_number):
    return f"P/N:{part_number} SN:{serial_number} Lot:{lot_number}"

def insert_barcode_log(
    part_number,
    serial_number,
    lot_number,
    optic_sn,
    work_order=None,
):
    barcode_text = build_barcode_text(
        part_number=part_number,
        serial_number=serial_number,
        lot_number=lot_number,
    )

    sql = _get_azure_query("barcodeAdd_STR")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            sql,
            timestamp,
            part_number,
            serial_number,
            lot_number,
            optic_sn,
            barcode_text,
        )

        conn.commit()
        return True, barcode_text

    except pyodbc.IntegrityError:
        conn.rollback()
        return False, None

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] insert_barcode_log: {e}")
        return False, None

    finally:
        conn.close()



def get_recent_barcodes(limit=10):
    conn = _get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT TOP {int(limit)}
                timeStamp,
                partNumber,
                serialNumber,
                lotNumber,
                opticSerialNumber,
                barcode,
                jobStatus,
                rework
            FROM dbo.BarCodeLog
            ORDER BY timeStamp DESC
            """
        )

        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append({
                "timeStamp": row.timeStamp,
                "partNumber": row.partNumber,
                "serialNumber": row.serialNumber,
                "lotNumber": row.lotNumber,
                "opticSerialNumber": row.opticSerialNumber,
                "barcode": row.barcode,
                "jobStatus": row.jobStatus,
                "rework": row.rework,
            })

        return records

    except Exception as e:
        print(f"[ERROR] get_recent_barcodes: {e}")
        return []

    finally:
        conn.close()


def get_last_serial_for_part(part_number: str) -> int:
    if not part_number:
        raise ValueError("part_number is required")

    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        query = """
            SELECT MAX(serialNumber)
            FROM BarcodeLog
            WHERE PartNumber = ?
        """

        cursor.execute(query, part_number)
        row = cursor.fetchone()

        if row and row[0] is not None:
            return int(row[0])

        return 0

    except Exception as e:
        print(f"[ERROR] get_last_serial_for_part: {e}")
        return 0

    finally:
        if conn:
            conn.close()




SECRET_KEY = "super-secret-key"

# Optional upload dir
UPLOAD_FOLDER = r"D:\\12C Webapp\\12C_Tools\\flask_uploads"

# RMA paths (moved from config.ini)
RMA_FOLDER_TEMPLATE = r"D:\\12C Webapp\\12C_Tools\\templateRMA-MNx_RMAx_WOx_Date"
FAILURE_ANALYSIS_FOLDER = r"D:\\12C Webapp\\12C_Tools\\Failure Analysis"
ORIGINAL_TEST_FOLDER = r"D:\\12C Webapp\\12C_Tools\\Test results"

# database path (SQLite)
DB_PATH = r"D:\\12C Webapp\\12C_Tools\\12C_Sandbox.db"
document_path= r"D:\\12C Webapp\\12C_Tools\\data\\verifyModule_P-#.docx"

# Azure DATA STORAGE CONFIG
AZURE_CONNECTION_STRING = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=tcp:isb-techops-srv.database.windows.net,1433;"
    "Database=12C_TestExecutive;"
    "Uid=isb-techops@isb-techops-srv;"
    "Pwd=Newport!;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)


import azure.functions as func
import pyodbc
import os
import json
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

app = func.FunctionApp()  # This line is REQUIRED in the single-file model

def get_db_connection():
    """Establishes connection to the Azure SQL Database"""
    try:
        connection = pyodbc.connect(os.getenv("DB_CONNECTION_STRING"))
        return connection
    except Exception as e:
        print("Database connection error:", str(e))
        return None

def get_fee_status(student_id):
    """Fetches the fee status of a student based on StudentID"""
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}, 500

    cursor = conn.cursor()
    cursor.execute("SELECT TotalFee, PaidAmount FROM Students WHERE StudentID = ?", (student_id,))
    result = cursor.fetchone()
    
    if not result:
        return {"error": "Student not found"}, 404

    total_fee, paid_amount = result
    status = "Paid" if paid_amount == total_fee else "Partially Paid" if paid_amount > 0 else "Overdue"

    conn.close()
    return {"StudentID": student_id, "Status": status}, 200

# Azure Function trigger
@app.function_name(name="GetFeeStatus")
@app.route(route="GetFeeStatus", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handles HTTP requests for fetching fee status"""
    student_id = req.params.get('StudentID')
    if not student_id:
        return func.HttpResponse(
            json.dumps({"error": "StudentID is required"}),
            status_code=400,
            mimetype="application/json"
        )

    response, status_code = get_fee_status(student_id)
    return func.HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")

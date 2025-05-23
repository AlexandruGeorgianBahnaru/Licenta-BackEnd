import hashlib
import io
import datetime
import uuid
import mariadb

import utils.constants as constants
import text_extraction.methods as extractor
from token_manipulation import token_manipulation as tc

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Query


app = FastAPI()
security = HTTPBearer()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DB_CONFIG = {
    "host": constants.HOST_NAME,
    "user": constants.USER,
    "password": constants.DB_PASSWORD,
    "database": constants.DATABASE_NAME,
}

def get_db_connection():
    return mariadb.connect(**DB_CONFIG)


@app.get("/eon/user/invoices")
def get_invoices(
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    sorted_by: str = Query(default="invoice_name"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        token = credentials.credentials
        expired, uid, email = tc.verify_token_expiry(token)
        print(expired)
        if expired == 'expired':
            raise HTTPException(status_code=401, detail="Expired refresh token")
        if expired == 'invalid':
            raise HTTPException(status_code=403, detail="Invalid refresh token")

        valid_sort_columns = {
            "invoice_name", "upload_date", "outstanding_balance", "billed_quantity"
        }
        print(sorted_by)
        if sorted_by not in valid_sort_columns:
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {sorted_by}")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as total FROM invoices WHERE user_id = %s", (uid,))
        total = cursor.fetchone()["total"]

        query = f"""
            SELECT invoice_name, billing_period, upload_date, outstanding_balance, billed_quantity
            FROM invoices
            WHERE user_id = %s
            ORDER BY {sorted_by} ASC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (uid, limit, offset))
        invoices = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "invoices": invoices,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/eon/user/upload-invoice")
async def upload_invoice(file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        expired, uid, email = tc.verify_token_expiry(token)
        print(expired)
        if expired == 'expired':
            raise HTTPException(status_code=401, detail="Expired refresh token")
        if expired == 'invalid':
            raise HTTPException(status_code=403, detail="Invalid refresh token")

        file_name = file.filename
        file_content = await file.read()
        pdf_content = io.BytesIO(file_content)
        extracted_text = await extractor.text_extractor_file(pdf_content)

        current_time = datetime.datetime.now()
        formatted_date = current_time.strftime("%d.%m.%Y")
        month_year = extractor.extract_billing_month(extracted_text["Perioadă facturată"])
        month = month_year.split(" ")[0]
        year = month_year.split(" ")[1]
        billed_quantity = extracted_text["Cantitate facturată"]

        # Check for duplicate invoice
        conn = get_db_connection()
        cursor = conn.cursor()

        check_query = """
            SELECT id FROM invoices 
            WHERE billing_month_name = %s AND billing_year = %s AND user_id = %s
        """
        cursor.execute(check_query, (month, year, uid))
        existing_invoice = cursor.fetchone()

        if existing_invoice:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=409, detail="Invoice for this month and quantity already exists.")

        # Insert new invoice
        query_insert_invoices = """
        INSERT INTO invoices (billed_quantity, 
            billing_period, index_determination_method,
            outstanding_balance, due_date,
            total_invoice_value, previous_balance,
            issue_date, vat_value,
            kwh_value, pdf,
            user_id, invoice_name,
            upload_date, billing_month_name, billing_year) VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            billed_quantity,
            extracted_text["Perioadă facturată"],
            extracted_text["Mod stabilire index"],
            extracted_text["Sold de plată"],
            extracted_text["Dată scadență"],
            extracted_text["Total valoare factură\\ncurentă"],
            extracted_text["Sold anterior"],
            extracted_text["Dată emitere"],
            extracted_text["ValoareTVA"],
            extracted_text["Valoare kwh"],
            str(pdf_content.getvalue()),
            uid,
            file_name,
            formatted_date,
            month,
            year,
        )

        cursor.execute(query_insert_invoices, values)
        inserted_id = cursor.lastrowid
        conn.commit()

        query = """SELECT invoice_name, billed_quantity,
                    outstanding_balance, previous_balance,
                    billing_period, kwh_value,
                    issue_date, due_date,
                    upload_date FROM invoices WHERE id = %s"""

        cursor.execute(query, (inserted_id,))
        inserted_invoice = cursor.fetchall()

        cursor.close()
        conn.close()
        return inserted_invoice

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/eon/user/monthly-quantities")
def get_monthly_quantities(
    year: int = Query(..., ge=2000, le=2100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        token = credentials.credentials
        expired, uid, email = tc.verify_token_expiry(token)
        print(expired)
        if expired == 'expired':
            raise HTTPException(status_code=401, detail="Expired refresh token")
        if expired == 'invalid':
            raise HTTPException(status_code=403, detail="Invalid refresh token")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT billing_month_name, billed_quantity
            FROM invoices
            WHERE user_id = %s AND billing_year = %s
            ORDER BY FIELD(billing_month_name, 
            'January', 'February', 'March', 'April', 'May', 'June', 
            'July', 'August', 'September', 'October', 'November', 'December')
        """

        cursor.execute(query, (uid, year))
        results = cursor.fetchall()
        print(results)
        cursor.close()
        conn.close()

        return {
            "year": year,
            "data": results
        }

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

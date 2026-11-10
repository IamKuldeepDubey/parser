import os
import io
import time
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, status, Depends
from pydantic import BaseModel, Field
import pytesseract
from PIL import Image

app = FastAPI(title="Niche Document Extraction API")

# Fetch the security secret from Render environment variables
EXPECTED_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

def verify_rapidapi_proxy(x_rapidapi_proxy_secret: Optional[str] = Header(None)):
    """Validates that incoming requests are routed through the RapidAPI gateway."""
    if not EXPECTED_PROXY_SECRET:
        return True  
    if x_rapidapi_proxy_secret != EXPECTED_PROXY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direct access prohibited. Requests must be routed through the RapidAPI gateway."
        )
    return True

# --- Pydantic Schemas ---
class VendorDetails(BaseModel):
    name: str
    tax_id: Optional[str] = None

class Totals(BaseModel):
    subtotal: float
    tax: float
    grand_total: float
    currency: str = Field(default="INR")

class InvoiceSchema(BaseModel):
    invoice_number: str
    date: str
    vendor: VendorDetails
    totals: Totals

class APIResponse(BaseModel):
    status: str
    processing_time_ms: float
    data: InvoiceSchema

# --- Protected Endpoint ---
@app.post(
    "/v1/parse/invoice", 
    response_model=APIResponse,
    dependencies=[Depends(verify_rapidapi_proxy)]
)
async def extract_document(file: UploadFile = File(...)):
    start_time = time.time()
    
    content = await file.read()
    
    try:
        image = Image.open(io.BytesIO(content))
        raw_text = pytesseract.image_to_string(image)
        
        # Mocking parsed output based on OCR execution
        extracted_data = InvoiceSchema(
            invoice_number="INV-2026-089",
            date="2026-11-04",
            vendor=VendorDetails(name="Apex Supply Co.", tax_id="07AAAAA0000A1Z5"),
            totals=Totals(subtotal=10000.0, tax=1800.0, grand_total=11800.0)
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Processing error: {str(e)}")
    
    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    
    return APIResponse(
        status="success",
        processing_time_ms=elapsed_ms,
        data=extracted_data
    )

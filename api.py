from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pipeline import extract_pdf_stream
from typing import Literal

app = FastAPI()

@app.post("/process-pdf/")
async def process_pdf(
  file: UploadFile = File(...),
  eye: Literal["LE","RE"] = Form("LE")
  ):
  try:
    # read the uploaded file into mem
    pdf_bytes = await file.read()

    #process the pdf
    result = extract_pdf_stream(pdf_bytes,eye=eye)
  except:
    raise HTTPException(status_code=400)
  return result

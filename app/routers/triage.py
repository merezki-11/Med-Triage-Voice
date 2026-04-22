from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import shutil
import os
from typing import Dict, Any

from app.services.transcription import transcribe_audio
from app.services.analysis import analyze_clinical_text

router = APIRouter(tags=["Triage"])

@router.post("/process-audio")
async def process_audio(audio: UploadFile = File(...)):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    # Save the file temporarily
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, audio.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        # 1. Transcribe the audio
        transcription_result = transcribe_audio(file_path)
        transcript = transcription_result.get("text", "")
        
        if not transcript:
             raise HTTPException(status_code=500, detail="Transcription failed or empty.")
             
        # 2. Analyze the transcript using Gemini
        clinical_data = analyze_clinical_text(transcript)
        
        # Use the AI-cleaned transcript if available, removing it from clinical_data
        # so it doesn't clutter the structured JSON output box
        if isinstance(clinical_data, dict) and "cleaned_transcript" in clinical_data:
            transcript = clinical_data.pop("cleaned_transcript")
        elif isinstance(clinical_data, dict) and "error" in clinical_data:
            # If the extraction failed due to rate limits or similar, log it.
            print("Gemini Analysis Error:", clinical_data.get("error"))
        
        return {
            "status": "success",
            "transcript": transcript,
            "language": transcription_result.get("language", "unknown"),
            "clinical_data": clinical_data
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

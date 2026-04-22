import os
from google import genai
from google.genai.errors import ClientError
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def analyze_clinical_text(transcript: str) -> dict:
    """Uses Gemini to extract structured clinical data from a rough transcript."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
        return {
            "error": "GEMINI_API_KEY is not configured.",
            "raw_text": transcript
        }
        
    # Use Gemini to intelligently correct transcription errors and extract JSON
    prompt = f"""
You are a professional clinical intake assistant. 
Analyze the following patient transcription, which might contain speech-to-text errors (like "tumor cramps" instead of "stomach cramps", or "it's endina" instead of "eating dinner").
Patient input:
"{transcript}"

Extract the following structured data as valid JSON exactly in this format:
{{
    "cleaned_transcript": "The corrected transcription, fixing any obvious medical terminology mistranscriptions or grammatical errors caused by STT. Fix errors like 'tumor' to 'stomach' safely. If in a foreign language, translate or keep it coherent.",
    "patient_name": "Name if provided, else 'Unknown'",
    "primary_symptoms": ["symptom1", "symptom2"],
    "duration": "How long they have had the symptoms, if stated, or 'Unknown'",
    "severity_level": "Low/Medium/High/Critical (Estimate based on symptoms)",
    "recommended_triage": "Short professional advice for the intake nurse"
}}
"""
    
    try:
        from google.genai import types
        # Using the new genai SDK to avoid deprecation and support Gemini 2.5
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result_text = response.text.strip()
        
        # It's explicitly set to application/json, so it should be purely valid JSON.
        try:
            data = json.loads(result_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                raise ValueError("No JSON object found in Gemini response.")
            
        return data
        
    except ClientError as e:
        import traceback
        traceback.print_exc()
        if e.code == 429:
            return {
                "error": "Gemini Rate Limit! Please wait 20 seconds and try again.",
                "details": str(e),
                "raw_text": transcript
            }
        return {
            "error": f"Google API Error: {e.code}",
            "details": str(e),
            "raw_text": transcript
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": "Failed to parse data format.",
            "details": str(e),
            "raw_text": transcript
        }

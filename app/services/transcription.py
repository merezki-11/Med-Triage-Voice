from faster_whisper import WhisperModel
import os

# Initialize globally to load only once.
# "base" model is small and fast. It will automatically download on first run.
model = None

def get_model():
    global model
    if model is None:
        print("Loading local Whisper model (base size) into memory...")
        # Using CPU with int8 quantization for broad compatibility and fast local inference
        model = WhisperModel("base", device="cpu", compute_type="int8")
        print("Whisper model loaded!")
    return model

def transcribe_audio(file_path: str) -> dict:
    model = get_model()
    
    print(f"Transcribing {file_path}...")
    
    # We provide a light medical context to help spelling, but let the model auto-detect the language
    # to support the Multilingual requirements. 
    medical_context = "Patient clinical intake."
    
    segments, info = model.transcribe(
        file_path, 
        beam_size=5,
        initial_prompt=medical_context
    )
    
    text = ""
    for segment in segments:
        text += segment.text + " "
        
    return {
        "text": text.strip(),
        "language": info.language,
        "language_probability": info.language_probability
    }

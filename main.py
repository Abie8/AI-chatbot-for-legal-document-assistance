import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from google import genai

# 1. Environment Setup
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def get_pdf_text(path):
    """Extracts text from all pages of a PDF."""
    text = ""
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        
        # Returns the full text after the loop finishes
        return text.strip() 
    except Exception as e:
        return f"PDF Error: {e}"

def legal_assistant():
    # Pre-flight checks
    if not api_key:
        print("Error: API Key missing! Check your .env file.")
        return

    pdf_file = "sample_agreement.pdf"
    
    if not os.path.exists(pdf_file):
        print("Error: PDF file-ah kanom! (File not found)")
        return

    print(f"📄 Reading {pdf_file}...")
    raw_text = get_pdf_text(pdf_file)
    
    if not raw_text or "PDF Error" in raw_text:
        print(f"Error: PDF-la irundhu text edukka mudila. {raw_text}")
        return

    # Initialize Gemini Client
    client = genai.Client(api_key=api_key)
    
    # Using the latest stable lite model for speed and efficiency
    model_id = "gemini-3-flash-preview" 
    
    print(f"🤖 AI ({model_id}) is analyzing... Konjam wait pannunga.")
    
    try:
        # Structured Prompt
        prompt = (
            "You are a professional legal expert. Summarize the following legal document "
            "into 5 simple points. Use englsih (english is preferred for clarity). "
            "Focus on risks and obligations.\n\n"
            f"DOCUMENT CONTENT:\n{raw_text[:15000]}" # Slightly higher limit for Flash models
        )
        
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        print("\n" + "="*30)
        print("📜 LEGAL SUMMARY (english)")
        print("="*30)
        print(response.text)
        print("="*30)
        
    except Exception as e:
        print(f"\n❌ AI Error: {e}")
        print("Tip: API limit reach aayirukalaam. 1-2 minutes kalichu thirumba run panni paarunga.")

if __name__ == "__main__":
    legal_assistant()
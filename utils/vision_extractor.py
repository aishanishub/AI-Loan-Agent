# loan_agent/utils/vision_extractor.py
import json
import io
import google.generativeai as genai
from PIL import Image
from config import GOOGLE_API_KEY # Import your Google API key from config

async def extract_id_info_from_image(image_path: str) -> dict:
    """
    Uses Google Gemini 1.5 Flash to parse an ID document image into a structured JSON object.
    This function is self-contained and does not use the Semantic Kernel.
    
    Args:
        image_path (str): The file path to the image to be parsed.

    Returns:
        dict: A dictionary containing the extracted information.
    """
    try:
        # --- 1. Configure the Gemini client ---
        genai.configure(api_key=GOOGLE_API_KEY)

        # --- 2. Set up the model ---
        # Using gemini-1.5-flash as requested. The 'latest' tag is often good practice.
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # --- 3. Prepare the Image ---
        # Open the image from the provided file path using PIL.
        img = Image.open(image_path)

        # --- 4. Prepare the Prompt ---
        # This prompt is specifically for extracting ID information.
        prompt_text = """
        Analyze the provided image of a government-issued ID document (like a PAN card or Aadhar card).
        Extract the full name, the type of the ID, and the ID number.

        CRITICAL INSTRUCTIONS:
        1.  The output MUST be a single, valid JSON object.
        2.  The JSON object must have exactly three keys: "full_name" (string), "id_type" (string), and "id_number" (string).
        3.  For "id_type", identify if it is an 'Aadhar' card, 'PAN' card, or another type. Be concise.
        4.  Do not include any other text, explanations, or markdown formatting like ```json in your response. Your entire response should be only the JSON object itself.

        Example Input Image: A PAN card for "ALICE SMITH" with number "P987654321".

        Example JSON Output:
        {"full_name": "ALICE SMITH", "id_type": "PAN", "id_number": "P987654321"}
        """

        # --- 5. Send the request to Gemini ---
        # We provide a list containing both the text prompt and the PIL image object.
        response = await model.generate_content_async([prompt_text, img])

        # --- 6. Extract, clean, and parse the response ---
        response_text = response.text
        json_str = response_text.strip().replace("```json", "").replace("```", "").strip()
        
        return json.loads(json_str)

    except Exception as e:
        # Provide clear error feedback if something goes wrong.
        print(f"--- ERROR IN GEMINI VISION PARSER ---")
        print(f"An error occurred while calling the Google Gemini API: {e}")
        print(f"This could be due to an invalid GOOGLE_API_KEY, network issues, or a problem with Google's service.")
        print(f"------------------------------------")
        # Return an empty dict or raise the exception to be handled by the calling step
        raise e
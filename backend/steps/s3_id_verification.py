# loan_agent/backend/steps/s3_id_verification.py
from backend.steps.s0_step_context import SimpleContext
from backend.database_service import DatabaseService
from utils.vision_extractor import extract_id_info_from_image 

# --- THE FIX: A dictionary to normalize common ID type variations ---
# It maps various possible AI outputs (lowercase) to our standard database format.
ID_TYPE_NORMALIZATION_MAP = {
    "aadhar": "Aadhar",
    "aadhaar": "Aadhar",  # <-- This will fix your specific error
    "pan": "PAN",
    "permanent account number": "PAN",
    "passport": "Passport"
}

class S3_ID_Verification:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def execute(self, context: SimpleContext, payload: dict):
        state = context.state
        phase = state.get("phase", "start")

        if phase == "start":
            state.update(payload)
            await context.emit_event({"id": "display_message", "data": "For security, please upload an image of your government-issued ID."})
            await context.emit_event({"id": "request_file_upload"})
            state["phase"] = "awaiting_image"
            return

        if phase == "awaiting_image":
            image_path = payload
            await context.emit_event({"id": "display_message", "data": "🖼️ Analyzing ID... This may take a moment."})
            
            try:
                id_info = await extract_id_info_from_image(image_path)
                
                customer_id = state["customer_id"]

                # Clean the raw data from the AI
                name = id_info.get("full_name", "").strip()
                raw_id_type = id_info.get("id_type", "").strip().lower()
                id_number = id_info.get("id_number", "").strip()

                # --- THE FIX: Normalize the extracted ID type ---
                # We look up the raw type in our map. If it's not there, we use the raw (but capitalized) version as a fallback.
                id_type = ID_TYPE_NORMALIZATION_MAP.get(raw_id_type, raw_id_type.capitalize())

                if not all([name, id_type, id_number]):
                    raise ValueError("Could not extract all required details from the ID.")

                # Now, we pass the CLEANED and NORMALIZED data to the verification function.
                if state.get("is_new"):
                    self.db_service.add_customer_id(customer_id, id_type, id_number)
                    await context.emit_event({"id": "display_message", "data": "✅ ID details captured."})
                    await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": customer_id}}})
                else:
                    if self.db_service.verify_customer_id(customer_id, name, id_type, id_number):
                        await context.emit_event({"id": "display_message", "data": "✅ ID verification successful!"})
                        await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": customer_id}}})
                    else:
                        raise ValueError("The name, ID type, or ID number from the document does not match our records.")
            
            except Exception as e:
                await context.emit_event({"id": "display_message", "data": f"❌ ID verification failed: {e}. Let's try again from the beginning."})
                await context.emit_event({"id": "transition", "data": {"next_step": "S1_Greet_Classify", "payload": None}})
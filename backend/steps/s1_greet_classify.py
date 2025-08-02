# loan_agent/backend/steps/s1_greet_classify.py
from backend.steps.s0_step_context import SimpleContext
from backend.database_service import DatabaseService
import config

class S1_Greet_Classify:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def execute(self, context: SimpleContext, payload: str = None):
        state = context.state
        phase = state.get("phase", "start")
        email = payload

        if phase == "start":
            await context.emit_event({"id": "display_message", "data": "👋 Hello! Welcome to the Loan Agent. To begin, please enter your email address."})
            await context.emit_event({"id": "request_input"})
            state["phase"] = "awaiting_email"
            return

        if phase == "awaiting_email":
            if not email or "@" not in email:
                await context.emit_event({"id": "display_message", "data": "❌ Invalid email format. Please try again."})
                # Transition back to the start of this same step to re-ask
                await context.emit_event({"id": "transition", "data": {"next_step": "S1_Greet_Classify", "payload": None}})
                return

            if email.lower() in config.LOAN_GIVER_EMAILS:
                await context.emit_event({"id": "display_message", "data": "🏦 Welcome, Loan Officer."})
                # Transition to the loan giver portal
                await context.emit_event({"id": "transition", "data": {"next_step": "S7_Loan_Giver_Portal", "payload": None}})
                return

            await context.emit_event({"id": "display_message", "data": "👤 Thank you. Checking our records..."})
            customer = self.db_service.find_customer_by_email(email)
            
            if customer:
                await context.emit_event({"id": "display_message", "data": f"✅ Welcome back, {customer['full_name']}!"})
                # Transition to ID verification for existing user
                await context.emit_event({"id": "transition", "data": {"next_step": "S3_ID_Verification", "payload": {"customer_id": customer['customer_id'], "is_new": False}}})
            else:
                await context.emit_event({"id": "display_message", "data": "🆕 It looks like you're a new user."})
                # Transition to new customer registration
                await context.emit_event({"id": "transition", "data": {"next_step": "S2_New_Customer", "payload": {"email": email}}})
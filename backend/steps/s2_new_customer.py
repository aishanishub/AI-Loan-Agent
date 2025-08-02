# loan_agent/backend/steps/s2_new_customer.py
from backend.steps.s0_step_context import SimpleContext
from backend.database_service import DatabaseService

class S2_New_Customer:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def execute(self, context: SimpleContext, payload: any):
        state = context.state
        phase = state.get("phase", "start")
        user_input = payload

        if phase == "start":
            state["email"] = user_input["email"]
            await context.emit_event({"id": "display_message", "data": "Let's get you registered. First, what is your full name?"})
            await context.emit_event({"id": "request_input"})
            state["phase"] = "awaiting_name"
            return
            
        elif phase == "awaiting_name":
            state["name"] = user_input.strip()
            await context.emit_event({"id": "display_message", "data": "Great. Now, what's your phone number?"})
            await context.emit_event({"id": "request_input"})
            state["phase"] = "awaiting_phone"
            return

        elif phase == "awaiting_phone":
            state["phone"] = user_input.strip()
            await context.emit_event({"id": "display_message", "data": "And finally, please provide your current credit score (e.g., 750)."})
            await context.emit_event({"id": "request_input"})
            state["phase"] = "awaiting_score"
            return

        elif phase == "awaiting_score":
            try:
                credit_score = int(user_input.strip())
                if not 300 <= credit_score <= 850:
                    raise ValueError("Credit score out of range.")

                customer_id = self.db_service.add_new_customer(
                    name=state["name"],
                    email=state["email"],
                    phone=state["phone"],
                    credit_score=credit_score
                )
                await context.emit_event({"id": "display_message", "data": "✅ Registration successful! Now let's verify your identity."})
                
                await context.emit_event({"id": "transition", "data": {"next_step": "S3_ID_Verification", "payload": {"customer_id": customer_id, "is_new": True}}})

            except ValueError:
                await context.emit_event({"id": "display_message", "data": "❌ That doesn't seem like a valid credit score. Please enter a number between 300 and 850."})
                await context.emit_event({"id": "request_input"})
                state["phase"] = "awaiting_score"
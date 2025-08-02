# loan_agent/backend/steps/s7_loan_giver_portal.py
from backend.steps.s0_step_context import SimpleContext
from backend.database_service import DatabaseService

class S7_Loan_Giver_Portal:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def execute(self, context: SimpleContext, payload: str = None):
        state = context.state
        phase = state.get("phase", "start")
        user_input = payload

        if phase == "start":
            await context.emit_event({"id": "display_message", "data": "Fetching pending loan applications..."})
            pending_loans = self.db_service.get_pending_loans()
            if pending_loans.empty:
                await context.emit_event({"id": "display_message", "data": "There are no pending loan applications."})
                await context.emit_event({"id": "transition", "data": {"next_step": "S1_Greet_Classify", "payload": None}})
                return

            await context.emit_event({"id": "display_table", "data": pending_loans.to_dict('records')})
            await context.emit_event({"id": "display_message", "data": "To take action, type `approve <loan_id>` or `reject <loan_id>`. Type `exit` to log out."})
            await context.emit_event({"id": "request_input"})
            state["phase"] = "awaiting_command"
            return
        
        if phase == "awaiting_command":
            command = user_input.strip().lower()

            if command == "exit":
                await context.emit_event({"id": "display_message", "data": "Logging out. Goodbye!"})
                await context.emit_event({"id": "transition", "data": {"next_step": "S1_Greet_Classify", "payload": None}})
                return

            parts = command.split()
            action = None
            if len(parts) == 2:
                if parts[0] == "approve": action = "Approved"
                if parts[0] == "reject": action = "Rejected"
            
            if action:
                try:
                    loan_id = int(parts[1])
                    if self.db_service.update_loan_status(loan_id, action):
                        await context.emit_event({"id": "display_message", "data": f"✅ Loan ID {loan_id} has been {action.lower()}."})
                    else:
                        await context.emit_event({"id": "display_message", "data": f"❌ Loan ID {loan_id} not found or not pending."})
                except ValueError:
                    await context.emit_event({"id": "display_message", "data": "Invalid command. Loan ID must be a number."})
            else:
                await context.emit_event({"id": "display_message", "data": "Invalid command format. Use `approve <id>`, `reject <id>`, or `exit`."})
            
            # Loop back to the start of this step to show the updated table
            await context.emit_event({"id": "transition", "data": {"next_step": "S7_Loan_Giver_Portal", "payload": None}})
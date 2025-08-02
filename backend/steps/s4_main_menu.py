# loan_agent/backend/steps/s4_main_menu.py
from backend.steps.s0_step_context import SimpleContext
import semantic_kernel as sk
from semantic_kernel.functions import KernelArguments

class S4_Main_Menu:
    def __init__(self, kernel: sk.Kernel):
        self.kernel = kernel
        self.intent_classifier = kernel.add_function(
            function_name="classify_intent",
            plugin_name="MainMenu",
            prompt="""
            Analyze the user's request. Classify it into one of three categories:
            1. 'ask_question': User is asking for information (e.g., 'what is...', 'am I eligible...', 'tell me about...').
            2. 'apply_loan': User wants to start a loan application (e.g., 'I want a loan', 'apply for home loan').
            3. 'unknown': The intent is unclear or something else.

            User Request: {{$input}}
            Intent:
            """
        )

    async def execute(self, context: SimpleContext, payload: any):
        state = context.state
        phase = state.get("phase", "start")
        user_input = payload
        
        if phase == "start":
            state["customer_id"] = user_input["customer_id"]
            await context.emit_event({
                "id": "display_message",
                "data": ("How can I help you today?\n\n"
                         "1. Ask a question (e.g., 'What is the interest rate for a home loan?')\n"
                         "2. Apply for a loan (e.g., 'I want to apply for a home loan of 500000')\n"
                         "You can also type 'exit' to end the session.")
            })
            await context.emit_event({"id": "request_input"})
            state["phase"] = "awaiting_input"
            return
        
        if phase == "awaiting_input":
            customer_id = state["customer_id"]

            if not user_input:
                await context.emit_event({"id": "display_message", "data": "I didn't get that. Please tell me how I can help."})
                await context.emit_event({"id": "request_input"})
                return

            cleaned_input = user_input.strip().lower()
            if cleaned_input in ["exit", "quit", "goodbye", "bye"]:
                await context.emit_event({"id": "display_message", "data": "Thank you for using the Loan Agent. Goodbye! 👋"})
                # --- THE FIX: Emit the new 'end_session' event ---
                await context.emit_event({"id": "end_session"})
                return

            result = await self.kernel.invoke(self.intent_classifier, KernelArguments(input=user_input))
            intent = str(result).strip().lower()

            if intent == 'ask_question':
                await context.emit_event({"id": "transition", "data": {"next_step": "S5_RAG_Query", "payload": {"query": user_input, "customer_id": customer_id}}})
            elif intent == 'apply_loan':
                await context.emit_event({"id": "transition", "data": {"next_step": "S6_Loan_Application", "payload": {"request": user_input, "customer_id": customer_id}}})
            else:
                await context.emit_event({"id": "display_message", "data": "I'm not sure how to help with that. Please try rephrasing your request."})
                await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": customer_id}}})
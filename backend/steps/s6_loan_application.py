# loan_agent/backend/steps/s6_loan_application.py
from backend.steps.s0_step_context import SimpleContext
from backend.database_service import DatabaseService
from backend.rag_service import RAGService
import semantic_kernel as sk
from semantic_kernel.functions import KernelArguments
import config
import re
import json

class S6_Loan_Application:
    def __init__(self, kernel: sk.Kernel, db_service: DatabaseService, rag_service: RAGService):
        self.kernel = kernel
        self.db_service = db_service
        self.rag_service = rag_service
        
        self.request_parser_func = kernel.add_function(
            plugin_name="LoanApp",
            function_name="ParseInitialRequest",
            prompt="""
            Extract "loan_amount" (integer), "loan_purpose" (string, e.g., 'Home Loan'), and "tenure_years" (integer) from the user's request.
            If tenure is not specified, default to 5.
            Request: {{$input}}
            JSON:
            """
        )

        # --- THE DEFINITIVE FIX: An intelligent value extractor function ---
        self.value_extractor_func = kernel.add_function(
            plugin_name="LoanApp",
            function_name="ExtractValueFromContext",
            prompt="""
            You are a data extraction expert. From the provided "Context", extract the numerical value for the specified "Value to Extract".
            - Ignore currency symbols, text like "INR", "p.a.", "Minimum", "Up to", etc.
            - If the value is in "Crores", convert it to its full numerical form (e.g., "2 Crores" becomes 20000000).
            - If the value is in "Lakhs", convert it (e.g., "5 Lakhs" becomes 500000).
            - Your final answer MUST be a single integer, and nothing else. If the value cannot be found, return 0.

            Context:
            ---
            {{$context}}
            ---
            Value to Extract: {{$value_name}}

            Extracted Integer:
            """
        )

    def _calculate_emi(self, loan_amount, annual_rate, tenure_years):
        r = (annual_rate / 100) / 12
        n = tenure_years * 12
        if r > 0:
            return int(loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1))
        return 0

    # --- NEW: Helper that uses the intelligent extractor function ---
    async def _get_eligibility_value(self, loan_purpose: str, value_name: str) -> int:
        """Performs a targeted RAG query and uses an LLM to extract the specific value."""
        # The query is now more natural
        query = f"{value_name} for {loan_purpose}"
        context = await self.rag_service.query(query, n_results=3)
        
        # Use the LLM to intelligently find the value in the context
        result = await self.kernel.invoke(
            self.value_extractor_func,
            KernelArguments(context=context, value_name=value_name)
        )
        try:
            return int(str(result).strip())
        except (ValueError, TypeError):
            return 0 # Return 0 if the LLM fails to return a clean integer

    async def execute(self, context: SimpleContext, payload: any):
        state = context.state
        phase = state.get("phase", "start")
        user_input = payload

        if phase == "start":
            state["customer_id"] = user_input["customer_id"]
            await context.emit_event({"id": "display_message", "data": "Let's start your loan application. Analyzing your request..."})
            
            try:
                result = await self.kernel.invoke(self.request_parser_func, KernelArguments(input=user_input["request"]))
                details = json.loads(str(result).strip())
                
                state["loan_amount"] = int(details.get("loan_amount", 0))
                state["loan_purpose"] = details.get("loan_purpose", "Unknown")
                state["tenure_years"] = int(details.get("tenure_years", 5))
                
                if state["loan_amount"] <= 0 or state["loan_purpose"] == "Unknown":
                    raise ValueError("Could not determine the loan amount or purpose from your request.")
                
                # --- Get Rate of Interest ---
                # This still uses regex as interest rates have a very standard format (%)
                rate_context = await self.rag_service.query(f"interest rate for {state['loan_purpose']}")
                rate_matches = re.findall(r'(\d+\.?\d*)%', rate_context)
                annual_rate = float(rate_matches[0]) if rate_matches else config.DEFAULT_ANNUAL_INTEREST_RATE
                state["annual_rate"] = annual_rate
                
                emi = self._calculate_emi(state["loan_amount"], annual_rate, state["tenure_years"])
                state["emi"] = emi

                await context.emit_event({
                    "id": "display_message",
                    "data": f"Based on a loan of **₹{state['loan_amount']:,}** for a '{state['loan_purpose']}' over **{state['tenure_years']} years** at {annual_rate}% p.a., your estimated monthly EMI would be **₹{emi:,}**. \n\nDo you want to proceed with the eligibility check? (yes/no)"
                })
                await context.emit_event({"id": "request_input"})
                state["phase"] = "awaiting_confirmation"
            
            except Exception as e:
                await context.emit_event({"id": "display_message", "data": f"Sorry, I couldn't understand the loan details. Please try again. Error: {e}"})
                await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": state["customer_id"]}}})
            return
        
        elif phase == "awaiting_confirmation":
            if user_input.strip().lower() != "yes":
                await context.emit_event({"id": "display_message", "data": "Okay, the loan application has been cancelled."})
                await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": state["customer_id"]}}})
                return
            
            # --- Start Sequential Eligibility Checks using the new intelligent helper ---
            loan_purpose = state["loan_purpose"]
            
            # 1. Max Loan Amount Check
            max_loan_amount = await self._get_eligibility_value(loan_purpose, "Maximum Loan Amount")
            if max_loan_amount > 0 and state["loan_amount"] > max_loan_amount:
                await context.emit_event({"id": "display_message", "data": f"❌ Application Failed: The requested amount of ₹{state['loan_amount']:,} exceeds the maximum of ₹{max_loan_amount:,} for a {loan_purpose}."})
                await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": state["customer_id"]}}})
                return
            await context.emit_event({"id": "display_message", "data": "✅ Loan amount is within limits."})
            
            # 2. Ask for Income
            await context.emit_event({"id": "display_message", "data": "Next, please enter your monthly income (e.g., 50000)."})
            await context.emit_event({"id": "request_input"})
            state["phase"] = "awaiting_income"

        elif phase == "awaiting_income":
            try:
                monthly_income = int(user_input.strip())
                loan_purpose = state["loan_purpose"]

                # 3. Minimum Income Check
                min_income = await self._get_eligibility_value(loan_purpose, "Minimum Income")
                if min_income > 0 and monthly_income < min_income:
                    raise ValueError(f"Your monthly income of ₹{monthly_income:,} is below the required minimum of ₹{min_income:,} for a {loan_purpose}.")
                await context.emit_event({"id": "display_message", "data": "✅ Income level is sufficient."})

                # 4. Credit Score Check
                customer = self.db_service.find_customer_by_id(state["customer_id"])
                min_score = await self._get_eligibility_value(loan_purpose, "Minimum Credit Score")
                if min_score > 0 and int(customer['credit_score']) < min_score:
                    raise ValueError(f"Your credit score of {customer['credit_score']} is below the required minimum of {min_score} for a {loan_purpose}.")
                await context.emit_event({"id": "display_message", "data": "✅ Credit score is satisfactory."})

                # ALL CHECKS PASSED
                self.db_service.add_loan_application(state["customer_id"], state["loan_amount"], state["loan_purpose"], "Pending")
                await context.emit_event({"id": "display_message", "data": "🎉 **Success!** All initial eligibility checks have passed. Your loan application has been submitted for final review."})

            except ValueError as e:
                await context.emit_event({"id": "display_message", "data": f"❌ Application Failed: {e}"})
            
            await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": state["customer_id"]}}})
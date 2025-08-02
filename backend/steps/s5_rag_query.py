# loan_agent/backend/steps/s5_rag_query.py
from backend.steps.s0_step_context import SimpleContext
from backend.rag_service import RAGService
import semantic_kernel as sk
from semantic_kernel.functions import KernelArguments

class S5_RAG_Query:
    def __init__(self, kernel: sk.Kernel, rag_service: RAGService):
        self.kernel = kernel 
        self.rag_service = rag_service

        # --- Function 1: Query Expansion ---
        # This function takes the user's question and rewrites it
        # into a better query for the vector database.
        self.query_expansion_function = kernel.add_function(
            function_name="ExpandQuery",
            plugin_name="RAG",
            prompt="""
            You are a query optimization expert for a vector database about bank loans.
            Your task is to rewrite the user's question into a concise, keyword-focused search query.
            Focus on extracting key terms and using likely synonyms found in financial documents.
            For example, if the user asks "what's the rate for a car loan?", a good query would be "annual interest rate vehicle loan".
            If the user asks "how much money can I get for a house?", a good query would be "maximum loan amount home loan".

            User Question: {{$query}}
            Optimized Search Query:
            """
        )

        # --- Function 2: Answer Generation (remains the same but with a better prompt) ---
        # This function takes the retrieved context and generates the final answer.
        self.rag_function = kernel.add_function(
            function_name="AnswerWithContext",
            plugin_name="RAG",
            prompt="""
            You are a helpful and intelligent loan assistant. Your task is to answer the user's question using the provided 'Context from the loan guide'.

            INSTRUCTIONS:
            - Analyze the user's question and find the most relevant information within the context.
            - Synthesize a clear and concise answer based *only* on the provided context.
            - If the context contains the answer, state it directly and confidently.
            - If the context does not contain the necessary information, you MUST respond with: "I'm sorry, I couldn't find specific information about that in the loan guide."
            - Do not make up information or use any knowledge outside of the provided context.

            Context from the loan guide:
            ---
            {{$context}}
            ---

            User's Question:
            {{$query}}

            Answer:
            """
        )

    async def execute(self, context: SimpleContext, payload: dict):
        query = payload["query"]
        customer_id = payload["customer_id"]

        await context.emit_event({"id": "display_message", "data": f"🔎 Searching our loan guide for information about: '{query}'..."})
        
        # --- Stage 1: Expand the user's query into a better search query ---
        expansion_result = await self.kernel.invoke(self.query_expansion_function, KernelArguments(query=query))
        expanded_query = str(expansion_result)
        # This print statement is for your terminal, so you can see what's happening
        print(f"DEBUG: Original Query: '{query}' | Expanded Query for Search: '{expanded_query}'")

        # --- Stage 2: Retrieve context using the NEW, expanded query ---
        retrieved_context = await self.rag_service.query(expanded_query, n_results=5)

        # --- Stage 3: Generate the final answer ---
        # We use the ORIGINAL user query here so the LLM answers the user's actual question.
        result = await self.kernel.invoke(
            self.rag_function,
            KernelArguments(query=query, context=retrieved_context)
        )
        
        await context.emit_event({"id": "display_message", "data": str(result)})
        
        await context.emit_event({"id": "display_message", "data": "Is there anything else I can help you with?"})
        await context.emit_event({"id": "transition", "data": {"next_step": "S4_Main_Menu", "payload": {"customer_id": customer_id}}})
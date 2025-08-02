# loan_agent/app.py
import streamlit as st
import asyncio
import os
import tempfile
import pandas as pd

# --- Import Backend Components ---
from backend.kernel_factory import create_kernel
from backend.database_service import DatabaseService
from backend.rag_service import RAGService

# --- Import Step Classes ---
from backend.steps.s0_step_context import SimpleContext
from backend.steps.s1_greet_classify import S1_Greet_Classify
from backend.steps.s2_new_customer import S2_New_Customer
from backend.steps.s3_id_verification import S3_ID_Verification
from backend.steps.s4_main_menu import S4_Main_Menu
from backend.steps.s5_rag_query import S5_RAG_Query
from backend.steps.s6_loan_application import S6_Loan_Application
from backend.steps.s7_loan_giver_portal import S7_Loan_Giver_Portal

# --- Async Helper ---
def run_async(coro):
    """Helper to run async functions in a sync context like Streamlit."""
    return asyncio.run(coro)

# --- Core Application Logic ---
def initialize_app():
    """Initializes all services and steps, storing them in session state."""
    if "app_initialized" in st.session_state and st.session_state.app_initialized:
        return

    st.session_state.app_initialized = False
    st.session_state.messages = []
    st.session_state.current_step_name = "S1_Greet_Classify"
    st.session_state.step_work_state = {}
    st.session_state.is_awaiting_input = False
    st.session_state.is_awaiting_file = False

    try:
        st.session_state.db_service = DatabaseService()
        kernel = create_kernel()
        st.session_state.kernel = kernel
        st.session_state.rag_service = RAGService(kernel)
        pdf_path = os.path.join("data", "LoanGuide.pdf")
        if os.path.exists(pdf_path):
            st.session_state.rag_service.setup_rag(pdf_path)
        else:
            st.warning("LoanGuide.pdf not found. RAG features will be disabled.")
        
        # --- Step Instances Initialization (with the fix) ---
        st.session_state.steps = {
            "S1_Greet_Classify": S1_Greet_Classify(db_service=st.session_state.db_service),
            "S2_New_Customer": S2_New_Customer(db_service=st.session_state.db_service),
            # This is the corrected line: S3 no longer takes the kernel
            "S3_ID_Verification": S3_ID_Verification(db_service=st.session_state.db_service),
            "S4_Main_Menu": S4_Main_Menu(kernel=kernel),
            "S5_RAG_Query": S5_RAG_Query(kernel=kernel, rag_service=st.session_state.rag_service),
            "S6_Loan_Application": S6_Loan_Application(kernel=kernel, db_service=st.session_state.db_service, rag_service=st.session_state.rag_service),
            "S7_Loan_Giver_Portal": S7_Loan_Giver_Portal(db_service=st.session_state.db_service),
        }

        run_step(None)
        st.session_state.app_initialized = True

    except Exception as e:
        st.error("🔴 **Application Failed to Start**")
        st.error("This could be due to an invalid API key, base URL, or a billing issue with your provider.")
        st.info("💡 **Checklist:** Verify your API keys and base URL in `config.py`. If using a proxy, ensure it's active. If using OpenAI directly, check billing status.")
        st.code(f"Error details: {e}", language="text")
        st.stop()

# In loan_agent/app.py

# ... (other functions like initialize_app, run_async, etc., are correct) ...

def process_events(events):
    """Processes events emitted by a step, updating the UI and state."""
    for event in events:
        event_id = event["id"]
        data = event.get("data")

        if event_id == "display_message":
            st.session_state.messages.append({"role": "assistant", "content": data})
        elif event_id == "display_table":
            df = pd.DataFrame(data)
            st.session_state.messages.append({"role": "assistant", "dataframe": df})
        elif event_id == "request_input":
            st.session_state.is_awaiting_input = True
        elif event_id == "request_file_upload":
            st.session_state.is_awaiting_file = True
        elif event_id == "transition":
            next_step_name = data["next_step"]
            payload = data.get("payload")
            st.session_state.step_work_state.clear()
            st.session_state.current_step_name = next_step_name
            run_step(payload)
        
        # --- THE FIX: Handle the new 'end_session' event ---
        elif event_id == "end_session":
            # Halt all further action by turning off the input flags.
            # The app will simply display the final message and wait.
            st.session_state.is_awaiting_input = False
            st.session_state.is_awaiting_file = False
            # We can optionally reset the whole app state to be ready for a page refresh
            # by a new user.
            for key in list(st.session_state.keys()):
                if key != 'messages': # Keep the chat history visible
                    del st.session_state[key]
def run_step(payload):
    """Executes the current step with a given payload."""
    step_name = st.session_state.current_step_name
    context = SimpleContext(st.session_state.step_work_state)
    step_instance = st.session_state.steps[step_name]
    
    run_async(step_instance.execute(context, payload))
    
    process_events(context.emitted_events)
    context.emitted_events.clear()

# --- Main Streamlit App ---
def main():
    st.set_page_config(page_title="Loan Agent Chatbot", layout="wide")
    st.title("🤖 Loan Agent Chatbot")

    initialize_app()

    # Display chat history from session state
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "content" in msg:
                st.write(msg["content"])
            if "dataframe" in msg:
                st.dataframe(msg["dataframe"], use_container_width=True)

    # Handle user text input
    if st.session_state.is_awaiting_input:
        if prompt := st.chat_input("Your response..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.is_awaiting_input = False
            run_step(prompt)
            st.rerun()

    # Handle user file input
    elif st.session_state.is_awaiting_file:
        uploaded_file = st.file_uploader("Please upload your ID document", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                file_path = tmp_file.name
            
            st.session_state.messages.append({"role": "user", "content": f"📄 Uploaded {uploaded_file.name}"})
            st.session_state.is_awaiting_file = False
            run_step(file_path)
            st.rerun()

if __name__ == "__main__":
    if not os.path.exists("data/customers.csv"):
        print("CSV files not found. Running data_to_csv.py...")
        import data_to_csv
        print("Data generation complete.")
    
    main()
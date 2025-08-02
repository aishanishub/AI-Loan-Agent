# loan_agent/config.py
GOOGLE_API_KEY = "AIzaSyCCvdIM1CTsbWx696kWHrQUaPzTYmVd0ow" # <-- PASTE YOUR GEMINI API KEY HERE
# --- OpenAI Configuration ---
OPENAI_API_KEY = "sk-pLDp6V1ALVgG06YrdfxyF8VUB0FsfBqgHGBrPieXOADq9Sd3"  # Your OpenAI API key
OPENAI_BASE_URL = "https://api.chatanywhere.tech/v1"
# --- Model Configuration ---
CHAT_MODEL = "gpt-3.5-turbo"
VISION_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"

# --- Application Configuration ---
LOAN_GIVER_EMAILS = ["admin@bank.com", "manager@bank.com"]

# --- ChromaDB Configuration ---
CHROMA_PERSIST_DIR = "db"
CHROMA_COLLECTION_NAME = "loan_guide_docs"

# --- Loan Logic Configuration ---
# These values will be primarily retrieved from the PDF, 
# but we can have fallbacks or fixed values here.
# For example, the interest rate 'r' for the EMI formula.
# This represents the monthly interest rate. (e.g., 8.5% annual -> 0.085 / 12)
#DEFAULT_ANNUAL_INTEREST_RATE = 8.5
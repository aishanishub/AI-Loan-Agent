# loan_agent/backend/database_service.py
import pandas as pd
import os
from typing import Optional, Dict, List, Any

DATA_DIR = "data"

class DatabaseService:
    """A service to interact with the CSV database files."""

    def _get_path(self, filename: str) -> str:
        return os.path.join(DATA_DIR, filename)

    def find_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            df = pd.read_csv(self._get_path("customers.csv"))
            customer = df[df['email'].str.lower() == email.lower()]
            return customer.to_dict('records')[0] if not customer.empty else None
        except FileNotFoundError:
            return None

    def find_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        try:
            df = pd.read_csv(self._get_path("customers.csv"))
            customer = df[df['customer_id'] == int(customer_id)]
            return customer.to_dict('records')[0] if not customer.empty else None
        except FileNotFoundError:
            return None

    def verify_customer_id(self, customer_id: int, name: str, id_type: str, id_number: str) -> bool:
        """
        Verifies a customer's identity using the correct logic:
        1. Checks the name against the customers table.
        2. Finds the customer's specific ID record in the customer_ids table.
        3. Compares the extracted ID details against that specific record.
        """
        try:
            # --- Step 1: Verify the Name from the customers table ---
            customer_record = self.find_customer_by_id(customer_id)
            if not customer_record:
                print(f"DEBUG: Verification failed. No customer found for customer_id: {customer_id}")
                return False

            db_name = customer_record['full_name']
            if db_name.strip().lower() != name.strip().lower():
                print(f"DEBUG: Name mismatch. DB: '{db_name}', Extracted: '{name}'")
                return False

            # --- Step 2: Find the customer's specific ID record ---
            id_df = pd.read_csv(self._get_path("customer_ids.csv"))
            customer_id_record = id_df[id_df['customer_id'] == int(customer_id)]

            if customer_id_record.empty:
                print(f"DEBUG: Verification failed. No ID record found for customer_id: {customer_id}")
                return False

            # --- Step 3: Compare extracted details against THAT specific record ---
            # Get the single record's values from the database
            db_id_type = customer_id_record.iloc[0]['govt_id_type']
            db_id_number = customer_id_record.iloc[0]['govt_id_number']

            # Perform case-insensitive and whitespace-insensitive comparisons
            type_match = db_id_type.strip().lower() == id_type.strip().lower()
            number_match = db_id_number.strip().lower() == id_number.strip().lower()
            
            # For debugging purposes
            if not type_match:
                print(f"DEBUG: ID Type mismatch. DB: '{db_id_type}', Extracted: '{id_type}'")
            if not number_match:
                print(f"DEBUG: ID Number mismatch. DB: '{db_id_number}', Extracted: '{id_number}'")

            # The verification is successful only if both the ID type and number match
            return type_match and number_match

        except Exception as e:
            print(f"Error during ID verification process: {e}")
            return False
            
    # --- The rest of the functions remain the same ---

    def add_new_customer(self, name: str, email: str, phone: str, credit_score: int) -> int:
        df = pd.read_csv(self._get_path("customers.csv"))
        new_id = df['customer_id'].max() + 1
        new_customer = pd.DataFrame([{"customer_id": new_id, "full_name": name, "email": email, "phone_number": phone, "credit_score": credit_score}])
        df = pd.concat([df, new_customer], ignore_index=True)
        df.to_csv(self._get_path("customers.csv"), index=False)
        return new_id

    def add_customer_id(self, customer_id: int, id_type: str, id_number: str):
        df = pd.read_csv(self._get_path("customer_ids.csv"))
        if not df[df['customer_id'] == customer_id].empty:
            return
        new_record_id = df['id'].max() + 1
        new_id_record = pd.DataFrame([{"id": new_record_id, "customer_id": customer_id, "govt_id_type": id_type.strip(), "govt_id_number": id_number.strip()}])
        df = pd.concat([df, new_id_record], ignore_index=True)
        df.to_csv(self._get_path("customer_ids.csv"), index=False)

    def get_pending_loans(self) -> pd.DataFrame:
        df = pd.read_csv(self._get_path("loan_applications.csv"))
        return df[df['status'] == 'Pending']

    def update_loan_status(self, loan_id: int, new_status: str) -> bool:
        df = pd.read_csv(self._get_path("loan_applications.csv"))
        if loan_id in df[df['status'] == 'Pending']['loan_id'].values:
            df.loc[df['loan_id'] == loan_id, 'status'] = new_status
            df.to_csv(self._get_path("loan_applications.csv"), index=False)
            return True
        return False
    
    def add_loan_application(self, customer_id: int, amount: float, purpose: str, status: str):
        df = pd.read_csv(self._get_path("loan_applications.csv"))
        new_id = df['loan_id'].max() + 1
        from datetime import date
        new_app = pd.DataFrame([{"loan_id": new_id, "customer_id": customer_id, "loan_amount": amount, "loan_purpose": purpose, "application_date": date.today().isoformat(), "status": status}])
        df = pd.concat([df, new_app], ignore_index=True)
        df.to_csv(self._get_path("loan_applications.csv"), index=False)
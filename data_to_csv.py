#data_to_csv.py
import pandas as pd

# 1. Define the table insert data as Python lists

customers = [
    (1, 'Alice Smith', 'alice@example.com', '9876543210', 780),
    (2, 'Bob Johnson', 'bob@example.com', '8765432109', 720),
    (3, 'Carol Lee', 'carol@example.com', '7654321098', 690),
    (4, 'David Brown', 'david@example.com', '6543210987', 710),
    (5, 'Eva White', 'eva@example.com', '5432109876', 750),
    (6, 'Frank Adams', 'frank@example.com', '4321098765', 640),
    (7, 'Grace Allen', 'grace@example.com', '3210987654', 700),
    (8, 'Henry Ford', 'henry@example.com', '2109876543', 760),
    (9, 'Ivy Black', 'ivy@example.com', '1098765432', 670),
    (10, 'Jake Green', 'jake@example.com', '0987654321', 730)
]
customers_df = pd.DataFrame(customers, columns=["customer_id", "full_name", "email", "phone_number", "credit_score"])
customers_df.to_csv("data/customers.csv", index=False)


customer_ids = [
    (101,1, 'Aadhar', 'A123456789'),
    (102,2, 'PAN', 'P987654321'),
    (103,3, 'Aadhar', 'A234567890'),
    (104,4, 'PAN', 'P876543210'),
    (105,5, 'Aadhar', 'A345678901'),
    (106,6, 'PAN', 'P765432109'),
    (107,7, 'Aadhar', 'A456789012'),
    (108,8, 'PAN', 'P654321098'),
    (109,9, 'Aadhar', 'A567890123'),
    (110,10, 'PAN', 'P543210987')
]
customer_ids_df = pd.DataFrame(customer_ids, columns=["id","customer_id", "govt_id_type", "govt_id_number"])
customer_ids_df.to_csv("data/customer_ids.csv", index=False)


loan_applications = [
    (201,1, 500000, 'Home Renovation', '2023-01-10', 'Pending'),
    (202,2, 250000, 'Medical Expenses', '2023-02-15', 'Pending'),
    (203,3, 1000000, 'New House', '2023-03-12', 'Rejected'),
    (204,4, 300000, 'Education', '2023-04-01', 'Approved'),
    (205,5, 150000, 'Business Expansion', '2023-05-20', 'Pending'),
    (206,6, 200000, 'Debt Consolidation', '2023-06-18', 'Approved'),
    (207,7, 750000, 'Wedding', '2023-07-22', 'Pending'),
    (208,8, 120000, 'Travel', '2023-08-30', 'Rejected'),
    (209,9, 600000, 'Vehicle Purchase', '2023-09-05', 'Approved'),
    (210,10, 400000, 'Emergency Fund', '2023-10-10', 'Pending')
]
loan_applications_df = pd.DataFrame(loan_applications, columns=["loan_id","customer_id", "loan_amount", "loan_purpose", "application_date", "status"])
loan_applications_df.to_csv("data/loan_applications.csv", index=False)


income_details = [
    (301,1, 'Infosys', 75000, 'employed'),
    (302,2, 'Wipro', 62000, 'employed'),
    (303,3, 'HCL', 88000, 'employed'),
    (304,4, 'Self-Employed', 50000, 'Self-Employed'),
    (305,5, 'TCS', 67000, 'employed'),
    (306,6, 'Freelancer', 45000, 'Freelance'),
    (307,7, 'Amazon', 90000, 'employed'),
    (308,8, 'Microsoft', 110000, 'employed'),
    (309,9, 'Startup Founder', 35000, 'Entrepreneur'),
    (310,10, 'Capgemini', 78000, 'employed')
]
income_details_df = pd.DataFrame(income_details, columns=["income_id","customer_id", "employer_name", "monthly_income", "employment_type"])
income_details_df.to_csv("data/income_details.csv", index=False)


existing_loans = [
    (401,1, 'Home Loan', 250000, 12500),
    (402,2, 'Education Loan', 100000, 5000),
    (403,3, 'Personal Loan', 300000, 15000),
    (404,4, 'Vehicle Loan', 200000, 8000),
    (405,5, 'Home Loan', 150000, 7000),
    (406,6, 'Credit Card', 50000, 2500),
    (407,7, 'Business Loan', 400000, 20000),
    (408,8, 'Personal Loan', 100000, 5000),
    (409,9, 'Education Loan', 80000, 4000),
    (410,10, 'Vehicle Loan', 120000, 6000)
]
existing_loans_df = pd.DataFrame(existing_loans, columns=["existing_loan_id","customer_id", "loan_type", "outstanding_amount", "monthly_emi"])
existing_loans_df.to_csv("data/existing_loans.csv", index=False)

print("✅ All 5 CSV files created successfully!")



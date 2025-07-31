import pandas as pd
import json
import os

# Create test folder if it doesn't exist
os.makedirs("datasets", exist_ok=True)

# --- Students Data ---
students_data = [
    {
        "Name": "Jane Mwangi",
        "Reg_No": "KCA123456",
        "Course": "BSc Data Science",
        "Units_Taken": "Data Mining, AI, Stats, Python",
        "DOB": "2001-05-10",
        "Stage": "Stage 3",
        "Phone": "0712345678"
    },
    {
        "Name": "Brian Otieno",
        "Reg_No": "KCA123457",
        "Course": "BSc IT",
        "Units_Taken": "Networking, Java, DBMS, Web Dev",
        "DOB": "2000-11-20",
        "Stage": "Stage 4",
        "Phone": "0712987654"
    },
    {
        "Name": "Faith Chege",
        "Reg_No": "KCA123458",
        "Course": "BSc Data Science",
        "Units_Taken": "ML, AI, Python, Stats",
        "DOB": "2002-02-14",
        "Stage": "Stage 2",
        "Phone": "0701234567"
    },
    {
        "Name": "Alex Kiprono",
        "Reg_No": "KCA123459",
        "Course": "BSc IT",
        "Units_Taken": "Web Dev, Java, PHP, DBMS",
        "DOB": "2001-08-23",
        "Stage": "Stage 3",
        "Phone": "0798765432"
    }
]

# --- Lecturers Data ---
lecturers_data = [
    {"Name": "Dr. Kamau", "Staff_ID": "L001", "Units_Taught": "Data Mining, ML"},
    {"Name": "Ms. Wanjiku", "Staff_ID": "L002", "Units_Taught": "Stats, AI"},
    {"Name": "Mr. Otieno", "Staff_ID": "L003", "Units_Taught": "Java, Web Dev, PHP"},
    {"Name": "Mrs. Achieng", "Staff_ID": "L004", "Units_Taught": "DBMS, Networking"},
]

# --- Results Data ---
results_data = [
    {"Reg_No": "KCA123456", "Unit": "Data Mining", "Marks": 78},
    {"Reg_No": "KCA123456", "Unit": "AI", "Marks": 65},
    {"Reg_No": "KCA123457", "Unit": "Networking", "Marks": 72},
    {"Reg_No": "KCA123457", "Unit": "DBMS", "Marks": 55},
    {"Reg_No": "KCA123458", "Unit": "Python", "Marks": 88},
    {"Reg_No": "KCA123459", "Unit": "PHP", "Marks": 69},
]

# --- Faculty Admin (JSON) ---
faculty_data = {
    "username": "faculty_admin",
    "password": "admin123",
    "role": "faculty"
}

# Save CSVs
pd.DataFrame(students_data).to_csv("datasets/students.csv", index=False)
pd.DataFrame(lecturers_data).to_csv("datasets/lecturers.csv", index=False)
pd.DataFrame(results_data).to_csv("datasets/results.csv", index=False)

# Save JSON
with open("datasets/faculty.json", "w") as f:
    json.dump(faculty_data, f, indent=4)

print("✅ Dummy test generated in the 'test/' folder.")

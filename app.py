import csv
from flask import Flask, flash, render_template, request, redirect, session, url_for, make_response
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
from werkzeug.utils import secure_filename
import joblib
from sklearn.metrics import classification_report
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'secret_key'

# File paths
DATA_FOLDER = 'datasets'
USERS_FILE = os.path.join(DATA_FOLDER, 'login_users.csv')
LECTURERS_FILE = os.path.join(DATA_FOLDER, 'lecturers.csv')
RESULTS_FILE = os.path.join(DATA_FOLDER, 'results.csv')
STUDENTS_FILE = os.path.join(DATA_FOLDER, 'students.csv')

# ---------------------------
# Home/Login Page
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = pd.read_csv(USERS_FILE)
        user = users[(users['username'] == username) & (users['password'] == password)]

        if not user.empty:
            session['username'] = user.iloc[0]['username']
            session['role'] = user.iloc[0]['role']

            if session['role'] == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            elif session['role'] == 'lecturer':
                return redirect(url_for('lecturer_dashboard'))
            elif session['role'] == 'student':
                return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# ---------------------------
# Faculty Dashboard
# ---------------------------
@app.route('/faculty')
def faculty_dashboard():
    if 'username' not in session or session['username'] != 'faculty':
        return redirect(url_for('login'))

    # Load student results
    results_df = pd.read_csv('datasets/results_original.csv')
    lecturers_df = pd.read_csv('datasets/lecturers.csv')

    # Define units
    units = ['Data Mining', 'AI', 'Networking', 'DBMS', 'Python', 'PHP']

    # Grade categorization function
    def grade(score):
        if score >= 70: return 'A'
        elif score >= 60: return 'B'
        elif score >= 50: return 'C'
        elif score >= 40: return 'D'
        else: return 'F'

    # Apply grades
    for unit in units:
        if unit in results_df.columns:
            results_df[f'{unit}_Grade'] = results_df[unit].apply(grade)

    # Get filter parameters
    gpa_filter = request.args.get('gpa', '').strip()
    unit_filter = request.args.get('unit', '').strip()

    # Apply GPA filter
    if gpa_filter:
        try:
            if '-' in gpa_filter:
                min_gpa, max_gpa = map(float, gpa_filter.split('-'))
                results_df = results_df[(results_df['GPA'] >= min_gpa) & (results_df['GPA'] <= max_gpa)]
            else:
                gpa_value = float(gpa_filter)
                results_df = results_df[results_df['GPA'] >= gpa_value]
        except ValueError:
            pass  # Skip invalid input

    # Filter by unit if selected
    if unit_filter and unit_filter in results_df.columns:
        display_df = results_df[['reg_no', 'name', unit_filter, f'{unit_filter}_Grade', 'GPA', 'Attendance']]
    else:
        available_units = [u for u in units if u in results_df.columns]
        grade_cols = [f"{u}_Grade" for u in available_units]
        display_df = results_df[['reg_no', 'name'] + available_units + grade_cols + ['GPA', 'Attendance']]

    # Calculate unit averages and grade distribution
    unit_averages = results_df[units].mean(numeric_only=True).dropna().to_dict()
    grade_distribution = {u: results_df[f'{u}_Grade'].value_counts().to_dict() for u in units if f'{u}_Grade' in results_df.columns}

    return render_template('faculty_dashboard.html',
                           table=display_df.to_dict(orient='records'),
                           columns=display_df.columns,
                           unit_averages=unit_averages,
                           grade_distribution=grade_distribution,
                           units=units,
                           selected_unit=unit_filter,
                           zip=zip)



# ---------------------------
# Lecturer Dashboard
# ---------------------------
@app.route('/lecturer')
def lecturer_dashboard():
    if 'username' not in session or session.get('role') != 'lecturer':
        return redirect(url_for('login'))

    staff_id = session['username']
    try:
        lecturers_df = pd.read_csv('datasets/lecturers.csv')
        results_df = pd.read_csv('datasets/results_original.csv')
        results2_df = pd.read_csv('datasets/results.csv')

        # Remove whitespace from headers
        results_df.columns = results_df.columns.str.strip()

        lecturer_row = lecturers_df[lecturers_df['staff_id'] == staff_id]

        if lecturer_row.empty:
            return render_template("error.html", message="Lecturer not found.")

        lecturer_name = lecturer_row.iloc[0]['name']
        units_teaching = [unit.strip() for unit in lecturer_row.iloc[0]['units_teaching'].split(',')]

        # Validate if the units exist in results_df
        missing_units = [u for u in units_teaching if u not in results_df.columns]
        if missing_units:
            return render_template("error.html", message=f"The following units are missing from results.csv: {', '.join(missing_units)}")

        lecturer_results = results_df[['reg_no', 'name'] + units_teaching]

        
        # Transform results_df to a long format: one row per unit per student
        filtered_rows = []
        for _, row in results_df.iterrows():
            for unit in units_teaching:
                score = row.get(unit, None)
                filtered_rows.append({
                    'reg_no': row['reg_no'],
                    'name': row['name'],
                    'unit': unit,
                    'score': score
                })

        # Compute average scores per unit for visualization
        chart_data = results_df[units_teaching].mean().reset_index()
        chart_data.columns = ['unit', 'average_score']

        chart_labels = chart_data['unit'].tolist()
        chart_scores = chart_data['average_score'].tolist()

        # ---- Pie Chart Data: Grade distribution for this lecturer's units ----
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}

        for unit in units_teaching:
            scores = results_df[unit].dropna()
            for score in scores:
                if score >= 70:
                    grade_counts['A'] += 1
                elif score >= 60:
                    grade_counts['B'] += 1
                elif score >= 50:
                    grade_counts['C'] += 1
                elif score >= 40:
                    grade_counts['D'] += 1
                else:
                    grade_counts['F'] += 1

        # ---- Line Chart Data: scores of each unit per student ----
        line_chart_data = {}
        for unit in units_teaching:
            line_chart_data[unit] = results_df[unit].dropna().tolist()

        return render_template("lecturer_dashboard.html",
                               lecturer_name=lecturer_name,
                               units=units_teaching,
                               results=filtered_rows,
                               chart_labels=chart_labels,
                               chart_scores=chart_scores,
                               grade_labels=list(grade_counts.keys()),
                               grade_counts=list(grade_counts.values()),
                               line_chart_data=line_chart_data,
                               zip=zip)



    except Exception as e:
        return f"Error loading lecturer dashboard: {str(e)}"
    
# ---------------------------
# Predict Performance (Lecturer Only)
# ---------------------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    # Make sure only lecturers can access
    if 'role' not in session or session['role'] != 'lecturer':
        return redirect(url_for('login'))

    report = None
    data = None

    if request.method == "POST":
        file = request.files.get('file')
        model_choice = request.form.get('model')

        if file and model_choice:
            # Load the uploaded CSV file into a DataFrame
            df = pd.read_csv(file)

            # Replace this with the actual feature columns used in training
            feature_cols = ['AR', 'GPA']
            X = df[feature_cols]

            # Load the appropriate model
            if model_choice == 'logistic':
                model = joblib.load('student_performance_model.pkl')
            elif model_choice == 'tree':
                model = joblib.load('tree_model.pkl')
            else:
                return "Invalid model selected", 400

            # Predict and create a results table
            y_pred = model.predict(X)
            df['Predicted Performance'] = y_pred

            # If the dataset has the actual labels, generate classification report
            if 'FinalGrade' in df.columns:
                report = classification_report(df['FinalGrade'], y_pred)

            # Convert to records for HTML rendering
            data = df.to_dict(orient='records')

    return render_template("predict.html", report=report, data=data)


# ---------------------------
# Upload Results (Lecturer Only)
# ---------------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload_results():
    if 'role' not in session or session['role'] != 'lecturer':
        return redirect(url_for('upload_results'))

    if request.method == 'POST':
        file = request.files['csv_file']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join('datasets', filename)
            file.save(filepath)

            try:
                uploaded_df = pd.read_csv(filepath)
                lecturers_df = pd.read_csv(LECTURERS_FILE)

                staff_id = session['staff_id']
                lecturer_info = lecturers_df[lecturers_df['staff_id'] == staff_id]

                if lecturer_info.empty:
                    raise Exception("Lecturer not found in lecturers.csv.")

                # Extract units taught
                units_taught = lecturer_info['units'].values[0].split(',')

                # Select columns that match the units taught
                units_taught = [u.strip() for u in units_taught]
                all_units = [col for col in uploaded_df.columns if col in units_taught]

                if not all_units:
                    raise Exception("No matching unit columns found in uploaded CSV.")

                # Reshape the wide format to long
                long_df = pd.melt(
                    uploaded_df,
                    id_vars=['reg_no', 'name'],
                    value_vars=all_units,
                    var_name='unit',
                    value_name='score'
                )

                # Add staff_id column
                long_df['staff_id'] = staff_id

                # Load existing results
                results_path = os.path.join('datasets', 'results.csv')
                if os.path.exists(results_path):
                    existing_df = pd.read_csv(results_path)
                    merged = pd.concat([existing_df, long_df], ignore_index=True)
                else:
                    merged = long_df

                # Remove duplicates
                merged.drop_duplicates(subset=['reg_no', 'unit'], keep='last', inplace=True)

                # Save to results.csv
                merged.to_csv(results_path, index=False)

                flash('Results uploaded successfully.')
                return redirect(url_for('lecturer_dashboard'))

            except Exception as e:
                return render_template('error.html', message=f"Upload failed: {str(e)}")

    return render_template('upload_results.html')

# ---------------------------
# Student Dashboard
# ---------------------------
@app.route('/student')
def student_dashboard():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    reg_no = session['username']
    student_name = reg_no

    # Get student name from students.csv
    with open(STUDENTS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['reg_no'].strip() == reg_no.strip():
                student_name = row['name']
                break

    results = []
    if os.path.exists(RESULTS_FILE):
        df = pd.read_csv(RESULTS_FILE)

        print("Raw DataFrame:")
        print(df.head())

        student_row = df[df['reg_no'].str.strip() == reg_no.strip()]
        print(f"\nFiltered for reg_no={reg_no}:")
        print(student_row)

        if not student_row.empty:
            # Drop irrelevant columns
            drop_cols = ['reg_no', 'name', 'Attendance', 'gpa']
            available_cols = [col for col in drop_cols if col in student_row.columns]
            score_data = student_row.drop(columns=available_cols)

            print("\nScore Data (after drop):")
            print(score_data)

            results = score_data.to_dict(orient='records') if not score_data.empty else []

            print("\nFinal Results List:")
            print(results)

    return render_template('student_dashboard.html',
                           student_name=student_name,
                           results=results)
#-----------------------------------------------
#Defining a class PDF for generating PDF reports
#-----------------------------------------------
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self.title, ln=True, align='C')
        self.ln(5)

    def colored_table(self, header, data):
        # Colors, line width and bold font
        self.set_fill_color(200, 220, 255)
        self.set_text_color(0)
        self.set_draw_color(50, 50, 100)
        self.set_line_width(0.3)
        self.set_font('Arial', 'B', 12)

        col_width = 190 / len(header)  # Fit to page
        for col in header:
            self.cell(col_width, 10, col, border=1, align='C', fill=True)
        self.ln()

        self.set_font('Arial', '', 12)
        for row in data:
            for item in row:
                self.cell(col_width, 10, str(item), border=1, align='C')
            self.ln()

# ---------------------------
# Download Results as PDF (Student Only)
# ---------------------------
@app.route('/download_results')
def download_results():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    reg_no = session['username']
    student_name = reg_no

    # Get student name from students.csv
    with open(STUDENTS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['reg_no'].strip() == reg_no.strip():
                student_name = row['name']
                break

    if not os.path.exists('datasets/results_original.csv'):
        return "Results file not found", 404

    df = pd.read_csv('datasets/results_original.csv')
    student_row = df[df['reg_no'].str.strip() == reg_no.strip()]

    if student_row.empty:
        return "No results found for student", 404

    # Prepare headers and data
    header = []
    data = []

    # Units + Attendance + GPA
    for col in student_row.columns:
        if col not in ['reg_no', 'name']:
            header.append(col)

    data.append([student_row.iloc[0][col] for col in header])

    # Generate PDF
    pdf = PDF()
    pdf.title = f"{student_name} Result Slip"
    pdf.add_page()
    pdf.colored_table(header, data)

    # Output response
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={student_name.replace(" ", "_")}_result_slip.pdf'
    return response

# ---------------------------
# Logout
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)

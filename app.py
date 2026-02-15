import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "I love coding" 


@app.route('/dashboard')
def survivor_dashboard():
    return render_template("survivor_dashboard.html")

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')

def generate_reference_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"WP-{timestamp}-{random_part}"
# ---------------- SEVERITY LOGIC ----------------
def calculate_severity(abuse_type, urgency):
    score = 0

    # Urgency scoring
    if urgency == "Immediate Danger":
        score += 5
    elif urgency == "High Risk":
        score += 4
    elif urgency == "Moderate":
        score += 2

    # Abuse type scoring
    if abuse_type == "Physical Abuse":
        score += 3
    elif abuse_type == "Sexual Abuse":
        score += 4
    elif abuse_type == "Emotional Abuse":
        score += 2
    elif abuse_type == "Economic Abuse":
        score += 1

    # Priority level
    if score >= 8:
        level = "Critical"
    elif score >= 5:
        level = "High"
    elif score >= 3:
        level = "Moderate"
    else:
        level = "Low"

    return score, level


@app.route('/admin/reports')
def admin_reports():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT 
        report_id,
        reference_id,
        abuse_type,
        severity_level,
        severity_score,
        priority_level,
        severity_score,
        location,
        status,
        created_at
    FROM reports
    ORDER BY priority_level DESC, severity_score DESC, created_at DESC
    """

    cursor.execute(sql)
    reports = cursor.fetchall()

    # Count pending critical reports
    cursor.execute("SELECT COUNT(*) AS count FROM reports WHERE priority_level = 'Critical'")
    pending = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return render_template(
        'admin_reports.html',
        reports=reports,
        active="reports",  # Set active route
        pending_count=pending
    )

@app.route('/admin/report/<int:report_id>')
def view_report(report_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get report
    cursor.execute("SELECT * FROM reports WHERE report_id = %s", (report_id,))
    report = cursor.fetchone()

    # Get status history
    cursor.execute("""
        SELECT old_status, new_status, changed_at
        FROM report_status_history
        WHERE report_id = %s
        ORDER BY changed_at DESC
    """, (report_id,))
    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_report_detail.html",
        report=report,
        history=history,
        active="reports"
    )



@app.route('/resources')
def resources():
    service_type = request.args.get('type')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if service_type:
        sql = "SELECT * FROM services WHERE service_type = %s"
        cursor.execute(sql, (service_type,))
    else:
        sql = "SELECT * FROM services"
        cursor.execute(sql)

    services = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'resources.html',
        services=services,
        selected_type=service_type
    )


@app.route('/admin/update_status/<int:report_id>', methods=['POST'])
def update_status(report_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    new_status = request.form['status']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get current status
    cursor.execute(
        "SELECT status FROM reports WHERE report_id = %s",
        (report_id,)
    )
    report = cursor.fetchone()

    if report:
        old_status = report['status']

        # Update main table
        cursor.execute(
            "UPDATE reports SET status = %s WHERE report_id = %s",
            (new_status, report_id)
        )

        # Insert into history table
        cursor.execute(
            """
            INSERT INTO report_status_history
            (report_id, old_status, new_status)
            VALUES (%s, %s, %s)
            """,
            (report_id, old_status, new_status)
        )

        conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('admin_reports'))



# ---------------- ADMIN: VIEW SERVICES ----------------
@app.route('/admin/services')
def admin_services():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()

    # Count pending critical reports
    cursor.execute("SELECT COUNT(*) AS count FROM reports WHERE priority_level = 'Critical'")
    pending = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return render_template(
        'admin_services.html',
        services=services,
        active="services",  # Set active route
        pending_count=pending
    )


# ---------------- ADMIN: ADD SERVICE ----------------
@app.route('/admin/services/add', methods=['GET', 'POST'])
def add_service():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        service_type = request.form['service_type']
        location = request.form['location']
        contact = request.form['contact']

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO services (name, service_type, location, contact)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (name, service_type, location, contact))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_services'))

    return render_template('add_service.html')


# ---------------- ADMIN: EDIT SERVICE ----------------
@app.route('/admin/services/edit/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        service_type = request.form['service_type']
        location = request.form['location']
        contact = request.form['contact']

        sql = """
        UPDATE services
        SET name=%s, service_type=%s, location=%s, contact=%s
        WHERE service_id=%s
        """
        cursor.execute(sql, (name, service_type, location, contact, service_id))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('admin_services'))

    # GET request
    cursor.execute("SELECT * FROM services WHERE service_id = %s", (service_id,))
    service = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'edit_service.html',
        service=service
    )



# ---------------- REPORT ROUTE ----------------
@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        abuse_type = request.form['abuse_type']
        urgency = request.form['severity']
        location = request.form['location']
        description = request.form['description']

        # Generate reference ID
        reference_id = generate_reference_id()

        # Calculate severity
        severity_score, priority_level = calculate_severity(abuse_type, urgency)

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO reports 
        (reference_id, abuse_type, severity_level, location, description, severity_score, priority_level, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            reference_id,
            abuse_type,
            priority_level,  # This should be severity level
            location,
            description,
            severity_score,
            priority_level,
            "Pending"
        ))

        conn.commit()
        cursor.close()
        conn.close()

        # Redirect to recommendations
        return redirect(url_for('recommendations', priority=priority_level))

    return render_template('report.html')

# ---------------- RECOMMENDATIONS ROUTE ----------------
@app.route('/recommendations/<priority>')
def recommendations(priority):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if priority in ["Critical", "High"]:
        service_types = ("hospital", "shelter", "police")
    elif priority == "Moderate":
        service_types = ("counseling", "legal")
    else:
        service_types = ("education",)

    # Create a placeholder string for the number of service types
    placeholders = ', '.join(['%s'] * len(service_types))

    sql = f"""
    SELECT * FROM services
    WHERE service_type IN ({placeholders})
    """
    
    cursor.execute(sql, service_types)  # Pass the tuple directly here
    services = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'services.html',
        priority=priority,
        services=services
    )

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_analytics'))
        else:
            return "Invalid credentials"

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

def admin_required():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))


@app.route('/admin/api/analytics')
def admin_api_analytics():
    if not session.get('admin_logged_in'):
        return {"error": "Unauthorized"}, 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total reports
    cursor.execute("SELECT COUNT(*) AS total FROM reports")
    total_reports = cursor.fetchone()['total']

    # Critical reports count
    cursor.execute("SELECT COUNT(*) AS count FROM reports WHERE priority_level = 'Critical'")
    critical_count = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return {
        "total_reports": total_reports,
        "critical_count": critical_count
    }


@app.route('/track', methods=['GET', 'POST'])
def track_case():
    result = None

    if request.method == 'POST':
        ref_id = request.form['reference_id']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT reference_id, status FROM reports WHERE reference_id = %s",
            (ref_id,)
        )

        result = cursor.fetchone()

        cursor.close()
        conn.close()

    return render_template("track_case.html", result=result)


@app.route('/admin/analytics')
def admin_analytics():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Build date filter condition
    date_filter = ""
    values = []

    if start_date and end_date:
        date_filter = "WHERE DATE(created_at) BETWEEN %s AND %s"
        values = [start_date, end_date]

    # Total reports
    cursor.execute(f"""
        SELECT COUNT(*) AS total 
        FROM reports
        {date_filter}
    """, values)
    total_reports = cursor.fetchone()['total']

    # Count pending critical reports
    cursor.execute("SELECT COUNT(*) AS count FROM reports WHERE priority_level = 'Critical'")
    pending = cursor.fetchone()['count']

    # Reports by abuse type
    cursor.execute(f"""
        SELECT abuse_type, COUNT(*) AS count
        FROM reports
        {date_filter}
        GROUP BY abuse_type
    """, values)
    abuse_stats = cursor.fetchall()

    # Reports by priority
    cursor.execute(f"""
        SELECT priority_level, COUNT(*) AS count
        FROM reports
        {date_filter}
        GROUP BY priority_level
    """, values)
    priority_stats = cursor.fetchall()

    # Trend per day
    cursor.execute(f"""
        SELECT DATE(created_at) AS report_date, COUNT(*) AS count
        FROM reports
        {date_filter}
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """, values)
    trend_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    # Extract data
    abuse_labels = [row['abuse_type'] for row in abuse_stats]
    abuse_counts = [row['count'] for row in abuse_stats]

    priority_labels = [row['priority_level'] for row in priority_stats]
    priority_counts = [row['count'] for row in priority_stats]

    trend_labels = [str(row['report_date']) for row in trend_stats]
    trend_counts = [row['count'] for row in trend_stats]

    return render_template(
        'admin_analytics.html',
        total_reports=total_reports,
        pending_count=pending,
        abuse_labels=abuse_labels,
        abuse_counts=abuse_counts,
        priority_labels=priority_labels,
        priority_counts=priority_counts,
        trend_labels=trend_labels,
        trend_counts=trend_counts,
        start_date=start_date,
        end_date=end_date,
        active="analytics"  # Set active route
    )


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)

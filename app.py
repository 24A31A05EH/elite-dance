from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import traceback

# -----------------------------
# SUPABASE CONFIG (FROM ENV)
# -----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# EMAIL CONFIG (FROM ENV)
# -----------------------------
EMAIL_SENDER = os.environ.get("GMAIL_USER")
EMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)


# -----------------------------
# EMAIL FUNCTION
# -----------------------------
def send_email(to_email, subject, body):
    try:
        print("Connecting to Gmail SMTP...")

        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        server.sendmail(
            EMAIL_SENDER,
            to_email,
            msg.as_string()
        )

        server.quit()

        print("Email sent successfully")
        return True

    except Exception as e:
        print("Email error:", e)
        return False


# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# SUPABASE TEST ROUTE
# -----------------------------
@app.route("/test-supabase")
def test_supabase():
    try:
        data = supabase.table("enrollments").select("*").limit(1).execute()
        return jsonify({
            "connected": True,
            "data": data.data
        })
    except Exception as e:
        return jsonify({
            "connected": False,
            "error": str(e)
        })


# -----------------------------
# EMAIL TEST ROUTE
# -----------------------------
@app.route("/test-email")
def test_email():
    try:
        send_email(
            EMAIL_SENDER,
            "Test Email",
            "This is a test email from Railway"
        )
        return "Email test sent"
    except Exception as e:
        return str(e)


# -----------------------------
# ENROLL ROUTE
# -----------------------------
@app.route("/enroll", methods=["POST"])
def enroll():
    try:

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        age = data.get("age")
        dance_style = data.get("dance_style")
        experience = data.get("experience_level")

        if not name or not email or not phone:
            return jsonify({"error": "Missing required fields"}), 400

        response = supabase.table("enrollments").insert({
            "name": name,
            "email": email,
            "phone": phone,
            "age": age,
            "dance_style": dance_style,
            "experience_level": experience
        }).execute()

        send_email(
            email,
            "Welcome to Elite Dance Academy",
            f"""
Hello {name},

Thank you for enrolling in {dance_style} at Elite Dance Academy.

We will contact you soon with the class schedule.

Elite Dance Academy
"""
        )

        return jsonify({
            "message": "Enrollment successful",
            "data": response.data
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# -----------------------------
# CONTACT ROUTE
# -----------------------------
@app.route("/contact", methods=["POST"])
def contact():

    try:

        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        message = data.get("message")

        if not name or not email or not message:
            return jsonify({"error": "All fields required"}), 400

        send_email(
            EMAIL_SENDER,
            f"Message from {name}",
            f"""
Name: {name}
Email: {email}

Message:
{message}
"""
        )

        return jsonify({"message": "Message sent successfully"})

    except Exception as e:
        return jsonify({"error": str(e)})


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )

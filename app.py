from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import traceback
import requests

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# EMAIL CONFIG
# -----------------------------
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

# Email where mentor requests will be sent
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")

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
def send_email(to_email, subject, html_body):

    try:

        url = "https://api.resend.com/emails"

        payload = {
            "from": "Elite Dance Academy <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }

        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print("Email response:", response.text)

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

    body = """
    <h2>Test Email</h2>
    <p>This is a test email from Elite Dance Academy.</p>
    """

    send_email(ADMIN_EMAIL, "Test Email", body)

    return "Email test sent"


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

        # Store in database
        response = supabase.table("enrollments").insert({
            "name": name,
            "email": email,
            "phone": phone,
            "age": age,
            "dance_style": dance_style,
            "experience_level": experience
        }).execute()

        # Student confirmation email
        email_body = f"""
        <div style="font-family:Arial;padding:30px;background:#f4f6f8">

        <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:10px">

        <h2 style="color:#e63946;text-align:center">
        💃 Welcome to Elite Dance Academy
        </h2>

        <p>Hello <b>{name}</b>,</p>

        <p>Thank you for enrolling in <b>{dance_style}</b>.</p>

        <p>We are excited to welcome you to our dance family!</p>

        <div style="background:#f1faee;padding:15px;border-radius:8px;margin:20px 0">
        <b>Enrollment Details</b><br>
        Name: {name}<br>
        Dance Style: {dance_style}
        </div>

        <p>Our team will contact you soon with class schedule details.</p>

        <hr>

        <p style="text-align:center;color:#777">
        Elite Dance Academy<br>
        Inspiring Passion Through Dance
        </p>

        </div>
        </div>
        """

        send_email(
            email,
            "Welcome to Elite Dance Academy 💃",
            email_body
        )

        return jsonify({
            "message": "Enrollment successful",
            "data": response.data
        })

    except Exception as e:

        print(traceback.format_exc())

        return jsonify({
            "error": str(e)
        }), 500


# -----------------------------
# CONTACT / MENTOR ROUTE
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


        # -----------------------------
        # Email to Student
        # -----------------------------
        student_email = f"""
        <h2>Thank You for Contacting Elite Dance Academy</h2>

        <p>Hello <b>{name}</b>,</p>

        <p>Thank you for reaching out to us.</p>

        <p>Our mentor will review your request and contact you shortly.</p>

        <p>We are excited to help you start your dance journey! 💃</p>

        <br>

        <p>Best Regards,<br>
        Elite Dance Academy Team</p>
        """

        send_email(
            email,
            "We received your message | Elite Dance Academy",
            student_email
        )


        # -----------------------------
        # Email to Admin (Mentor Request)
        # -----------------------------
        admin_email = f"""
        <h3>New Mentor Request</h3>

        <p><b>Name:</b> {name}</p>
        <p><b>Email:</b> {email}</p>

        <p><b>Message:</b></p>
        <p>{message}</p>
        """

        send_email(
            ADMIN_EMAIL,
            f"New Mentor Request from {name}",
            admin_email
        )


        return jsonify({
            "message": "Message sent successfully"
        })


    except Exception as e:

        print(traceback.format_exc())

        return jsonify({
            "error": str(e)
        })


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )

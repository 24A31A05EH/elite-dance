from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# EMAIL CONFIG
# -----------------------------
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

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
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = to_email

        part = MIMEText(html_body, "html")
        msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True

    except Exception as e:
        print("Email error:", e)
        return False

    finally:
        try:
            server.quit()
        except Exception:
            pass


# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# TEST SUPABASE
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
        }), 500





# -----------------------------
# ENROLL ROUTE
# -----------------------------
@app.route("/enroll", methods=["POST"])
def enroll():
    try:
        # ✅ Verify Authorization token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized. Please sign in."}), 401

        token = auth_header.split(" ")[1]

        # ✅ Validate token with Supabase
        try:
            user_response = supabase.auth.get_user(token)
            if not user_response or not user_response.user:
                return jsonify({"error": "Invalid or expired session. Please sign in again."}), 401
        except Exception:
            return jsonify({"error": "Session verification failed. Please sign in again."}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        age = data.get("age")
        dance_style = data.get("dance_style", "").strip()
        experience = data.get("experience_level", "").strip()

        if not name or not email or not phone:
            return jsonify({"error": "Name, email, and phone are required."}), 400

        # ✅ Insert into Supabase
        response = supabase.table("enrollments").insert({
            "name": name,
            "email": email,
            "phone": phone,
            "age": age,
            "dance_style": dance_style,
            "experience_level": experience
        }).execute()

        # ✅ Send confirmation email to student
        email_body = f"""
        <div style="font-family:Arial;padding:30px;background:#f4f6f8">
          <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:10px">
            <h2 style="color:#e63946;text-align:center">💃 Welcome to Elite Dance Academy</h2>
            <p>Hello <b>{name}</b>,</p>
            <p>Thank you for enrolling in <b>{dance_style}</b>.</p>
            <p>We are excited to welcome you to our dance family!</p>
            <p>Our team will contact you soon with class schedule details.</p>
            <hr>
            <p style="text-align:center;color:#777">
              Elite Dance Academy<br>Inspiring Passion Through Dance
            </p>
          </div>
        </div>
        """
        send_email(email, "Welcome to Elite Dance Academy 💃", email_body)

        return jsonify({
            "message": "Enrollment successful",
            "data": response.data
        }), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# -----------------------------
# CONTACT / MENTOR ROUTE
# -----------------------------
@app.route("/contact", methods=["POST"])
def contact():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        message = data.get("message", "").strip()

        if not name or not email or not message:
            return jsonify({"error": "All fields are required."}), 400

        # ✅ Confirmation email to student
        student_email = f"""
        <h2>Thank You for Contacting Elite Dance Academy</h2>
        <p>Hello <b>{name}</b>,</p>
        <p>Thank you for reaching out to us.</p>
        <p>Our mentor will review your request and contact you shortly.</p>
        <p>We are excited to help you start your dance journey!</p>
        <br>
        <p>Best Regards,<br>Elite Dance Academy Team</p>
        """
        send_email(email, "We received your message | Elite Dance Academy", student_email)

        return jsonify({"message": "Message sent successfully"}), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

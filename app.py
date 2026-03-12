from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import smtplib
from email.mime.text import MIMEText

# -----------------------
# Supabase Configuration
# -----------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -----------------------
# Email Configuration
# -----------------------
SMTP_SERVER   = os.getenv("BREVO_SMTP_SERVER", "smtp-relay.brevo.com")
SMTP_PORT     = int(os.getenv("BREVO_SMTP_PORT", "587"))
SMTP_EMAIL    = os.getenv("BREVO_EMAIL")
SMTP_PASSWORD = os.getenv("BREVO_PASSWORD")

ACADEMY_EMAIL = "srisrimehernayana@gmail.com"

# -----------------------
# Debug: Print env status on startup
# -----------------------
print("=" * 40)
print("BREVO CONFIG CHECK:")
print(f"  SMTP_SERVER : {SMTP_SERVER}")
print(f"  SMTP_PORT   : {SMTP_PORT}")
print(f"  SMTP_EMAIL  : {SMTP_EMAIL}")
print(f"  SMTP_PASSWORD: {'SET ✅' if SMTP_PASSWORD else 'MISSING ❌'}")
print(f"  SUPABASE_URL: {'SET ✅' if SUPABASE_URL else 'MISSING ❌'}")
print(f"  SUPABASE_KEY: {'SET ✅' if SUPABASE_SERVICE_ROLE_KEY else 'MISSING ❌'}")
print("=" * 40)

# -----------------------
# Flask Setup
# -----------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})


# -----------------------
# Email Function
# -----------------------
def send_email(to, subject, body):
    try:
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("❌ Email not sent: BREVO_EMAIL or BREVO_PASSWORD is missing in env vars.")
            return False

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = to

        print(f"📧 Sending email to: {to} | Subject: {subject}")

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to, msg.as_string())
        server.quit()

        print(f"✅ Email sent successfully to {to}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Email failed: Authentication error — check BREVO_EMAIL and BREVO_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ Email failed (SMTP error): {e}")
        return False
    except Exception as e:
        print(f"❌ Email failed (unexpected): {e}")
        return False


# -----------------------
# Home Route
# -----------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------
# Supabase Test
# -----------------------
@app.route("/test-supabase")
def test_supabase():
    try:
        data = supabase.table("enrollments").select("*").limit(1).execute()
        return jsonify({"connected": True, "data": data.data})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


# -----------------------
# Enrollment Route
# -----------------------
@app.route("/enroll", methods=["POST"])
def enroll():

    # --- Auth check ---
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required"}), 401

    token = auth_header.split(" ")[1]

    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user
        if user is None:
            return jsonify({"error": "Invalid session"}), 403
    except Exception as e:
        print("Auth error:", e)
        return jsonify({"error": "Invalid token"}), 403

    # --- Validate fields ---
    data = request.get_json()
    required_fields = ["name", "email", "phone", "dance_style", "experience_level"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # --- Save to DB ---
    try:
        response = supabase.table("enrollments").insert({
            "name":             data.get("name"),
            "email":            data.get("email"),
            "phone":            data.get("phone"),
            "age":              data.get("age"),
            "dance_style":      data.get("dance_style"),
            "experience_level": data.get("experience_level"),
            "user_id":          user.id
        }).execute()
    except Exception as e:
        print("DB Error:", e)
        return jsonify({"error": str(e)}), 500

    # --- Email to Student ---
    student_email_sent = send_email(
        to      = data.get("email"),
        subject = f"Welcome to Elite Dance Academy 🎉",
        body    = f"""Hello {data.get("name")},

Thank you for enrolling at Elite Dance Academy!

Here are your enrollment details:
━━━━━━━━━━━━━━━━━━━━━━━━
Dance Style     : {data.get("dance_style")}
Experience Level: {data.get("experience_level")}
━━━━━━━━━━━━━━━━━━━━━━━━

Our team will contact you soon with class schedules and next steps.

Keep dancing!
Elite Dance Academy
📍 101 Elite Plaza, Bandra West, Mumbai
📞 +91 90000 12345
"""
    )

    # --- Email to Academy ---
    academy_email_sent = send_email(
        to      = ACADEMY_EMAIL,
        subject = f"New Enrollment - {data.get('name')} ({data.get('dance_style')})",
        body    = f"""New student enrolled!

━━━━━━━━━━━━━━━━━━━━━━━━
Name            : {data.get("name")}
Email           : {data.get("email")}
Phone           : {data.get("phone")}
Age             : {data.get("age") or "Not provided"}
Dance Style     : {data.get("dance_style")}
Experience Level: {data.get("experience_level")}
━━━━━━━━━━━━━━━━━━━━━━━━
"""
    )

    return jsonify({
        "message":             "Enrollment successful",
        "data":                response.data,
        "student_email_sent":  student_email_sent,
        "academy_email_sent":  academy_email_sent
    }), 201


# -----------------------
# Contact Route
# -----------------------
@app.route("/contact", methods=["POST"])
def contact():
    data    = request.get_json()
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({"error": "All fields are required"}), 400

    send_email(
        to      = ACADEMY_EMAIL,
        subject = f"Mentor Request - {name}",
        body    = f"""New mentor request received!

━━━━━━━━━━━━━━━━━━━━━━━━
Name   : {name}
Email  : {email}
━━━━━━━━━━━━━━━━━━━━━━━━
Message:
{message}
"""
    )

    return jsonify({"message": "Request sent successfully"}), 200


# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

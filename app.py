from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import smtplib
from email.mime.text import MIMEText

# -----------------------
# Supabase Configuration
# -----------------------
SUPABASE_URL              = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -----------------------
# Gmail Configuration
# -----------------------
GMAIL_USER     = os.getenv("GMAIL_USER")      # srisrimehernayana@gmail.com
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # 16-char App Password from Google
ACADEMY_EMAIL  = GMAIL_USER

# -----------------------
# Debug on startup
# -----------------------
print("=" * 40)
print("CONFIG CHECK:")
print(f"  GMAIL_USER     : {GMAIL_USER or 'MISSING ❌'}")
print(f"  GMAIL_PASSWORD : {'SET ✅' if GMAIL_PASSWORD else 'MISSING ❌'}")
print(f"  SUPABASE_URL   : {'SET ✅' if SUPABASE_URL else 'MISSING ❌'}")
print(f"  SUPABASE_KEY   : {'SET ✅' if SUPABASE_SERVICE_ROLE_KEY else 'MISSING ❌'}")
print("=" * 40)

# -----------------------
# Flask Setup
# -----------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})


# -----------------------
# Email Function (Gmail SMTP)
# -----------------------
def send_email(to, subject, body):
    try:
        if not GMAIL_USER or not GMAIL_PASSWORD:
            print("❌ Email not sent: GMAIL_USER or GMAIL_PASSWORD missing.")
            return False

        msg            = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = f"Elite Dance Academy <{GMAIL_USER}>"
        msg["To"]      = to

        print(f"📧 Sending email to: {to}")

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, to, msg.as_string())
        server.quit()

        print(f"✅ Email sent to {to}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail auth failed — use an App Password, not your Gmail login password.")
        return False
    except Exception as e:
        print(f"❌ Email failed: {e}")
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
        subject = "🎉 Welcome to Elite Dance Academy!",
        body    = f"""Hi {data.get("name")},

Thank you for enrolling in the {data.get("dance_style")} class at Elite Dance Academy!

We're excited to have you join our dance family 💃

Our team will contact you soon with class schedules and next steps.

Keep Dancing!

Elite Dance Academy"""
    )

    # --- Email to Academy ---
    academy_email_sent = send_email(
        to      = ACADEMY_EMAIL,
        subject = f"New Enrollment - {data.get('name')} ({data.get('dance_style')})",
        body    = f"""Hi,

New student enrolled!

Name      : {data.get("name")}
Email     : {data.get("email")}
Phone     : {data.get("phone")}
Age       : {data.get("age") or "Not provided"}
Dance Style     : {data.get("dance_style")}
Experience Level: {data.get("experience_level")}

Elite Dance Academy"""
    )

    return jsonify({
        "message":            "Enrollment successful",
        "data":               response.data,
        "student_email_sent": student_email_sent,
        "academy_email_sent": academy_email_sent
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
        body    = f"""Hi,

New mentor request received!

Name   : {name}
Email  : {email}

Message:
{message}

Elite Dance Academy"""
    )

    return jsonify({"message": "Request sent successfully"}), 200


# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

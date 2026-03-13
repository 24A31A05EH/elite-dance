from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import traceback

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yhvnbwwxlkbccishcuue.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlodm5id3d4bGtiY2Npc2hjdXVlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjYyMjI4OSwiZXhwIjoyMDg4MTk4Mjg5fQ.iVN3SPzhegXnZHmRJCnPX4paKPIyFxzsemlxae2BSgs")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -----------------------------
# EMAIL CONFIG
# -----------------------------
EMAIL_SENDER = os.environ.get("GMAIL_USER", "srisrimehernayana@gmail.com")
EMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD", "pfua xjfk vjfh pyts")

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app, resources={r"/*": {"origins": "*"}})


# ----------------------------------------------------
# EMAIL HELPER — never crashes the app
# ----------------------------------------------------
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        # ✅ Email failure is logged but NEVER crashes the enrollment
        print(f"❌ Email failed (non-fatal): {e}")
        return False


# ----------------------------------------------------
# ROUTES
# ----------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test-supabase")
def test_supabase():
    try:
        data = supabase.table("enrollments").select("*").limit(1).execute()
        return jsonify({"connected": True, "data": data.data})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


# ----------------------------------------------------
# ENROLL ROUTE
# ----------------------------------------------------
@app.route("/enroll", methods=["POST"])
def enroll():
    try:
        # 1. Check Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required. Please sign in."}), 401

        token = auth_header.split(" ")[1]

        # 2. Verify Supabase user
        try:
            auth_response = supabase.auth.get_user(token)
            user = auth_response.user
            if user is None:
                return jsonify({"error": "Invalid session. Please login again."}), 403
        except Exception as e:
            print("[AUTH ERROR]", e)
            return jsonify({"error": "Invalid or expired token"}), 403

        # 3. Parse JSON
        data = request.get_json()
        if not data:
            return jsonify({"error": "No enrollment data provided."}), 400

        required_fields = ["name", "email", "phone", "dance_style", "experience_level"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        # 4. Insert into Supabase
        response = supabase.table("enrollments").insert({
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "age": data.get("age"),
            "dance_style": data.get("dance_style"),
            "experience_level": data.get("experience_level"),
            "user_id": user.id
        }).execute()

        # 5. Send welcome email to STUDENT (failure won't break enrollment)
        send_email(
            to_email=data.get("email"),
            subject="🎉 Welcome to Elite Dance Academy!",
            body=f"""Hi {data.get("name")},

Thank you for enrolling in the {data.get("dance_style")} class at Elite Dance Academy!

We're excited to have you join our dance family 💃

Our team will contact you soon with class schedules and next steps.

Keep Dancing!
Elite Dance Academy"""
        )

        return jsonify({"message": "Enrollment successful!", "data": response.data}), 201

    except Exception as e:
        # ✅ Full error printed in Railway logs
        print("[ENROLL ERROR]", traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ----------------------------------------------------
# CONTACT ROUTE
# ----------------------------------------------------
@app.route("/contact", methods=["POST"])
def contact():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided."}), 400

        name    = data.get("name", "").strip()
        email   = data.get("email", "").strip()
        message = data.get("message", "").strip()

        if not name or not email or not message:
            return jsonify({"error": "All fields are required."}), 400

        send_email(
            to_email=EMAIL_SENDER,
            subject=f"🎓 Trial Class Request from {name}",
            body=f"""New trial class request!

Name:    {name}
Email:   {email}
Message: {message}
"""
        )

        return jsonify({"message": "Message received! A mentor will contact you soon."}), 200

    except Exception as e:
        print("[CONTACT ERROR]", traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ----------------------------------------------------
# RUN SERVER
# ----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = "https://yhvnbwwxlkbccishcuue.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlodm5id3d4bGtiY2Npc2hjdXVlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjYyMjI4OSwiZXhwIjoyMDg4MTk4Mjg5fQ.iVN3SPzhegXnZHmRJCnPX4paKPIyFxzsemlxae2BSgs"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -----------------------------
# EMAIL CONFIG
# -----------------------------
EMAIL_SENDER = "srisrimehernayana@gmail.com"
EMAIL_PASSWORD = "fdgm ladm gyqp sbcl"

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
# EMAIL FUNCTION
# ----------------------------------------------------
def send_thank_you_email(user_email, user_name, dance_style):
    subject = "🎉 Welcome to Elite Dance Academy!"
    body = f"""
Hi {user_name},

Thank you for enrolling in the {dance_style} class at Elite Dance Academy!

We're excited to have you join our dance family 💃

Our team will contact you soon with class schedules and next steps.

Keep Dancing!

Elite Dance Academy
"""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = user_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, user_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {user_email}")
    except Exception as e:
        print("❌ Email sending failed:", e)


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
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required. Please sign in."}), 401

    token = auth_header.split(" ")[1]

    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user
        if user is None:
            return jsonify({"error": "Invalid session. Please login again."}), 403
    except Exception as e:
        print("[AUTH ERROR]", e)
        return jsonify({"error": "Invalid or expired token"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"error": "No enrollment data provided."}), 400

    required_fields = ["name", "email", "phone", "dance_style", "experience_level"]
    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        response = supabase.table("enrollments").insert({
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "age": data.get("age"),
            "dance_style": data.get("dance_style"),
            "experience_level": data.get("experience_level"),
            "user_id": user.id
        }).execute()

        return jsonify({"message": "Enrollment successful!", "data": response.data}), 201

    except Exception as e:
        print("[DB ERROR]", e)
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_SENDER
        msg["Subject"] = f"Mentor Request from {name}"
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        msg.attach(MIMEText(body, "plain"))
        server.sendmail(EMAIL_SENDER, EMAIL_SENDER, msg.as_string())

        confirm = MIMEMultipart()
        confirm["From"] = EMAIL_SENDER
        confirm["To"] = email
        confirm["Subject"] = "We received your mentor request"
        confirm_body = f"Hi {name},\n\nThank you for contacting Elite Dance Academy.\n\nA mentor will contact you soon.\n\nRegards,\nElite Dance Academy"
        confirm.attach(MIMEText(confirm_body, "plain"))
        server.sendmail(EMAIL_SENDER, email, confirm.as_string())

        server.quit()
        return jsonify({"message": "Request sent"}), 200

    except Exception as e:
        print("CONTACT ERROR:", e)
        return jsonify({"error": "Email failed"}), 500


# ----------------------------------------------------
# RUN SERVER (Render uses $PORT env variable)
# ----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

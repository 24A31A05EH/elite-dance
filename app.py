from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import smtplib
from email.mime.text import MIMEText

# -------------------------
# Supabase Configuration
# -------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -------------------------
# Email Configuration (Brevo SMTP)
# -------------------------
SMTP_SERVER = os.getenv("BREVO_SMTP_SERVER")
SMTP_PORT = int(os.getenv("BREVO_SMTP_PORT"))
SMTP_EMAIL = os.getenv("BREVO_EMAIL")
SMTP_PASSWORD = os.getenv("BREVO_PASSWORD")

ACADEMY_EMAIL = "srisrimehernayana@gmail.com"

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------
# Email Sending Function
# -------------------------
def send_email(to, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to, msg.as_string())
        server.quit()

        print("Email sent successfully")
        return True

    except Exception as e:
        print("Email failed:", e)
        return False


# -------------------------
# Home Page
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# Test Supabase
# -------------------------
@app.route("/test-supabase")
def test_supabase():
    try:
        data = supabase.table("enrollments").select("*").limit(1).execute()
        return jsonify({"connected": True, "data": data.data})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


# -------------------------
# Enrollment API
# -------------------------
@app.route("/enroll", methods=["POST"])
def enroll():

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


    data = request.get_json()

    required_fields = ["name", "email", "phone", "dance_style", "experience_level"]

    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400


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


        # Email to student
        send_email(
            data.get("email"),
            "Welcome to Elite Dance Academy",
            f"""
Hello {data.get("name")},

Thank you for enrolling in Elite Dance Academy.

Dance Style: {data.get("dance_style")}
Experience Level: {data.get("experience_level")}

Our team will contact you soon.

Elite Dance Academy
"""
        )


        # Email to academy
        send_email(
            ACADEMY_EMAIL,
            f"New Enrollment - {data.get('name')}",
            f"""
New student enrolled!

Name: {data.get("name")}
Email: {data.get("email")}
Phone: {data.get("phone")}
Dance Style: {data.get("dance_style")}
Experience: {data.get("experience_level")}
"""
        )


        return jsonify({"message": "Enrollment successful", "data": response.data}), 201

    except Exception as e:
        print("DB Error:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------
# Contact API
# -------------------------
@app.route("/contact", methods=["POST"])
def contact():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    send_email(
        ACADEMY_EMAIL,
        f"Mentor Request - {name}",
        f"""
New mentor request received!

Name: {name}
Email: {email}

Message:
{message}
"""
    )

    return jsonify({"message": "Request sent"}), 200


# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=False)

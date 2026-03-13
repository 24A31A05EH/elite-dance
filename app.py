import os
from flask import Flask, request, jsonify
from supabase import create_client
import resend

# ==============================
# APP SETUP
# ==============================

app = Flask(__name__)

# ==============================
# ENV VARIABLES
# ==============================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Supabase environment variables missing!")

if not RESEND_API_KEY:
    print("⚠️ Resend API key missing!")

# ==============================
# INITIALIZE SERVICES
# ==============================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
resend.api_key = RESEND_API_KEY

# ==============================
# EMAIL FUNCTION
# ==============================

def send_email(to_email, subject, html_body):
    try:
        resend.Emails.send({
            "from": "Elite Dance Academy <onboarding@resend.dev>",
            "to": to_email,
            "subject": subject,
            "html": html_body,
        })
        print("Email sent to:", to_email)
        return True
    except Exception as e:
        print("Email error:", e)
        return False

# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return "Elite Dance Academy Backend Running 🚀"

@app.route("/enroll", methods=["POST"])
def enroll():
    try:
        data = request.json

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")

        if not name or not email:
            return jsonify({"error": "Name and Email required"}), 400

        # Save to Supabase
        supabase.table("enrollments").insert({
            "name": name,
            "email": email,
            "phone": phone
        }).execute()

        # Email Content
        email_body = f"""
        <h2>Welcome {name}! 💃</h2>
        <p>Thank you for enrolling in <b>Elite Dance Academy</b>.</p>
        <p>We will contact you soon.</p>
        <br>
        <p>Regards,<br>Elite Dance Team</p>
        """

        # Send Email to User
        send_email(
            email,
            "Welcome to Elite Dance Academy 🎉",
            email_body
        )

        return jsonify({"message": "Enrollment successful!"}), 200

    except Exception as e:
        print("Server error:", e)
        return jsonify({"error": "Internal Server Error"}), 500

# ==============================
# RUN (IMPORTANT FOR RAILWAY)
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

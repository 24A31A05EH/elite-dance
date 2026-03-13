import os
from flask import Flask, request, jsonify
from supabase import create_client
import resend

app = Flask(__name__)

# ==============================
# ENVIRONMENT VARIABLES
# ==============================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Resend
resend.api_key = RESEND_API_KEY


# ==============================
# EMAIL FUNCTION (RESEND)
# ==============================

def send_email(to_email, subject, html_body):
    try:
        resend.Emails.send({
            "from": "Elite Dance Academy <onboarding@resend.dev>",
            "to": to_email,
            "subject": subject,
            "html": html_body,
        })
        print("Email sent successfully to:", to_email)
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

        # Save to Supabase
        response = supabase.table("enrollments").insert({
            "name": name,
            "email": email,
            "phone": phone
        }).execute()

        # Email content
        email_body = f"""
        <h2>Welcome {name}! 💃🕺</h2>
        <p>Thank you for enrolling in Elite Dance Academy.</p>
        <p>We will contact you soon.</p>
        <br>
        <p>Regards,<br>Elite Dance Team</p>
        """

        # Send email to USER
        email_sent = send_email(
            email,
            "Welcome to Elite Dance Academy 🎉",
            email_body
        )

        return jsonify({
            "message": "Enrollment successful!",
            "email_sent": email_sent
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app.run()

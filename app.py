from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import requests

SUPABASE_URL = "https://yhvnbwwxlkbccishcuue.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlodm5id3d4bGtiY2Npc2hjdXVlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjYyMjI4OSwiZXhwIjoyMDg4MTk4Mjg5fQ.iVN3SPzhegXnZHmRJCnPX4paKPIyFxzsemlxae2BSgs"
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

RESEND_API_KEY = "re_2Cuw6HLd_DNg81QMcsJXbX3xmVaWTd13Z"
ACADEMY_EMAIL  = "srisrimehernayana@gmail.com"
EMAIL_FROM     = "Elite Dance Academy <onboarding@resend.dev>"

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})

def send_email(to, subject, body):
    try:
        # On free plan, Resend only allows sending to verified email
        # So we send to academy email with student info
        actual_to = ACADEMY_EMAIL if to != ACADEMY_EMAIL else ACADEMY_EMAIL
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from":     EMAIL_FROM,
                "to":       [actual_to],
                "subject":  subject,
                "text":     body,
                "reply_to": ACADEMY_EMAIL
            }
        )
        print(f"Resend: {response.status_code} | to: {actual_to} | {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Email failed: {e}")
        return False

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

@app.route("/enroll", methods=["POST"])
def enroll():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required."}), 401

    token = auth_header.split(" ")[1]
    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user
        if user is None:
            return jsonify({"error": "Invalid session."}), 403
    except Exception as e:
        print("[AUTH ERROR]", e)
        return jsonify({"error": "Invalid or expired token"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided."}), 400

    required_fields = ["name", "email", "phone", "dance_style", "experience_level"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

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

        # Send to academy with student details
        send_email(
            to      = ACADEMY_EMAIL,
            subject = f"New Enrollment - {data.get('name')} - {data.get('dance_style')}",
            body    = f"Hi,\n\nNew student enrolled!\n\nName: {data.get('name')}\nEmail: {data.get('email')}\nPhone: {data.get('phone')}\nDance Style: {data.get('dance_style')}\nExperience: {data.get('experience_level')}\n\nPlease send welcome email to the student.\n\nElite Dance Academy"
        )

        return jsonify({"message": "Enrollment successful!", "data": response.data}), 201

    except Exception as e:
        print("[DB ERROR]", e)
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route("/contact", methods=["POST"])
def contact():
    data    = request.get_json()
    name    = data.get("name")
    email   = data.get("email")
    message = data.get("message")

    # Send to academy with user details
    send_email(
        to      = ACADEMY_EMAIL,
        subject = f"Mentor Request - {name}",
        body    = f"Hi,\n\nNew mentor request received!\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message}\n\nPlease contact this person soon.\n\nElite Dance Academy"
    )

    return jsonify({"message": "Request sent"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

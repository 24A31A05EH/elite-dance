from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import requests

SUPABASE_URL = "https://yhvnbwwxlkbccishcuue.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlodm5id3d4bGtiY2Npc2hjdXVlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjYyMjI4OSwiZXhwIjoyMDg4MTk4Mjg5fQ.iVN3SPzhegXnZHmRJCnPX4paKPIyFxzsemlxae2BSgs"
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

RESEND_API_KEY = "re_2Cuw6HLd_DNg81QMcsJXbX3xmVaWTd13Z"
EMAIL_FROM = "Elite Dance Academy <onboarding@resend.dev>"

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})

def send_email(to, subject, body):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "text": body,
                "reply_to": "srisrimehernayana@gmail.com"
            }
        )
        print(f"Resend response: {response.status_code} {response.text}")
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

        send_email(
            to      = data.get("email"),
            subject = "Welcome to Elite Dance Academy!",
            body    = f"Hi {data.get('name')},\n\nThank you for enrolling in the {data.get('dance_style')} class at Elite Dance Academy!\n\nWe're excited to have you join our dance family 💃\n\nOur team will contact you soon with class schedules and next steps.\n\nKeep Dancing!\n\nElite Dance Academy"
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

    success = send_email(
        to      = email,
        subject = "We received your mentor request",
        body    = f"Hi {name},\n\nThank you for contacting Elite Dance Academy.\n\nA mentor will contact you soon.\n\nRegards,\nElite Dance Academy"
    )

    if success:
        return jsonify({"message": "Request sent"}), 200
    else:
        return jsonify({"error": "Email failed"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

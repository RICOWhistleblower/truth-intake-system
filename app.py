 
`python
from flask import Flask, rendertemplate, request, redirect, urlfor
import os, json, smtplib, ssl
from email.message import EmailMessage
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from utils.encrypt import encrypt_payload  # Stub; can be real AES/GPG

app = Flask(name, templatefolder="templates", staticfolder="static")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RECEIPT_FOLDER'] = 'receipts'
app.config['LOG_PATH'] = 'data/testimony-log.json'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt'}

Ensure required folders exist
for folder in [app.config['UPLOADFOLDER'], app.config['RECEIPTFOLDER'], 'data']:
    os.makedirs(folder, exist_ok=True)

Validate file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

Generate anonymous token receipt
def generate_token():
    return str(uuid.uuid4())

Save testimony to log + receipt
def save_testimony(entry, token):
    with open(app.config['LOG_PATH'], 'a') as log:
        log.write(json.dumps(entry) + "\n")
    with open(f"{app.config['RECEIPT_FOLDER']}/{token}.txt", "w") as r:
        r.write(f"Token: {token}\nTimestamp: {entry['timestamp']}\n")

Optional encrypted email
def sendencryptedemail(recipient_email, entry):
    msg = EmailMessage()
    msg['Subject'] = "Secure Intake Consent Received"
    msg['From'] = "no-reply@yourdomain.com"
    msg['To'] = recipient_email
    msg.set_content(f"""Thank you for your testimony submission.

Follow-up encrypted contact authorized.

Case Token: {entry['token']}
Timestamp: {entry['timestamp']}
Preview: {entry['testimony'][:100]}...
""")
    context = ssl.createdefaultcontext()
    with smtplib.SMTP_SSL("smtp.example.com", 465, context=context) as server:
        server.login("no-reply@yourdomain.com", "yourpassword")  # Use env vars in production
        server.send_message(msg)

@app.route('/', methods=['GET', 'POST'])
def intake():
    if request.method == 'POST':
        anonymous = request.form.get('anonymousToggle') == 'on'
        name = request.form.get('name') if not anonymous else "Anonymous"
        email = request.form.get('email') if not anonymous else None
        testimony = request.form.get('testimony')
        consent = request.form.get('encryptConsent') == 'on'

        filename = None
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        token = generate_token()
        timestamp = datetime.utcnow().isoformat() + 'Z'

        submission = {
            "name": name,
            "email": email,
            "testimony": testimony,
            "filename": filename,
            "encryptConsent": consent,
            "timestamp": timestamp,
            "token": token
        }

        encrypted = encrypt_payload(submission)  # currently passthrough; upgrade later
        save_testimony(encrypted, token)

        if email and consent:
            sendencryptedemail(email, submission)

        return redirect(url_for('confirmation', token=token))

    return render_template('submit-testimony.html')

@app.route('/confirmation')
def confirmation():
    token = request.args.get('token')
    return render_template('confirmation.html', token=token)

if name == 'main':
    app.run(host='0.0.0.0', port=5000, debug=True)
`
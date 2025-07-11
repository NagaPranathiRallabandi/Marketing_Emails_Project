#Model that also schedules the emails.
import os
import together
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Set your API Key
os.environ["TOGETHER_API_KEY"] = "a8b730604eb31a233a1cf0dc7d1b9b092880e32dbaa226686577d420a1a221d0"

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

class EmailGenerator:
    def __init__(self, model="mistralai/Mistral-7B-Instruct-v0.1"):
        self.model = model

    def generate_email(self, product_name, product_details, offer_details, customer_segment, company_name, company_details, tone):
        prompt = (f"Write a {tone} promotional email for {company_name} targeting {customer_segment} customers. "
                  f"The email should highlight the product {product_name} with the following details: {product_details}. "
                  f"Offer Details: {offer_details}. Company Details: {company_details}. "
                  f"Make it engaging with an exciting subject line and use emojis to make the content lively and impactful. "
                  f"Ensure the email feels friendly and persuasive, like a professional marketing email.")

        response = together.Complete.create(
            model=self.model,
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )

        if 'choices' in response:
            return response['choices'][0]['text']
        else:
            return "Error: Unable to generate email"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    product_name = request.form['product_name']
    product_details = request.form['product_details']
    offer_details = request.form['offer_details']
    customer_segment = request.form['customer_segment']
    company_name = request.form['company_name']
    company_details = request.form['company_details']
    tone = request.form['tone']

    email_gen = EmailGenerator()
    email = email_gen.generate_email(product_name, product_details, offer_details, customer_segment, company_name, company_details, tone)

    return jsonify({'email': email})

@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    email_content = data.get("email").replace("\n", "<br>")
    schedule_date = data.get("schedule_date")
    schedule_time = data.get("schedule_time")
    recipient_emails = data.get("recipient_emails")

    # Convert recipient emails from string to list
    if recipient_emails:
        extra_emails = [email.strip() for email in recipient_emails.split(",")]

        # Save new emails to emails.txt
        with open("emails.txt", "a") as file:  # 'a' mode appends new emails
            for email in extra_emails:
                file.write(email + "\n")

    # Read all emails from emails.txt
    with open("emails.txt", "r") as file:
        recipient_emails = [line.strip() for line in file.readlines()]

    if not recipient_emails:
        return jsonify({"message": "No recipient emails found!"})

    if schedule_date and schedule_time:
        scheduled_datetime = datetime.strptime(f"{schedule_date} {schedule_time}", "%Y-%m-%d %H:%M")
        scheduler.add_job(send_scheduled_email, 'date', run_date=scheduled_datetime, args=[email_content, list(recipient_emails)])
        return jsonify({"message": f"Email scheduled successfully for {scheduled_datetime}"})

    # If no schedule, send immediately
    send_scheduled_email(email_content, recipient_emails)
    return jsonify({"message": "Email sent successfully!"})

def send_scheduled_email(email_content, recipient_emails):
    sender_email = "23kn1a42f6@gmail.com"
    sender_password = "nxcn dxln rwou hdcw"

    if isinstance(recipient_emails, str):  # Ensure recipient_emails is a list
        recipient_emails = [email.strip() for email in recipient_emails.split(",")]

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        for recipient in recipient_emails:
            msg = MIMEText(email_content, "html")
            msg["Subject"] = "Exclusive Offer Just for You!"
            msg["From"] = sender_email
            msg["To"] = recipient
            server.sendmail(sender_email, recipient, msg.as_string())

        server.quit()
        print("Emails sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)

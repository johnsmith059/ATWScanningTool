import win32com.client as win32

def send_email_via_outlook(to_emails, subject, html_body):
    import win32com.client as win32

    recipients = [email.strip() for email in to_emails.split(',') if email.strip()]
    if not recipients:
        return False, "No valid email addresses provided."

    try:
        outlook = win32.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        mail.To = ";".join(recipients)

        mail.Subject = subject
        mail.HTMLBody = html_body
        mail.Send()

        return True, "Email sent successfully!"

    except Exception as e:
        return False, f"Failed to send email: {e}"
    
def load_email_css():
    with open("assets/email_styles.css", "r") as f:
        return f"<style>{f.read()}</style>"

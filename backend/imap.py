# (.venv) hari@vivobook:$  cat .env

# (.venv) hari@vivobook:$  cat app.py
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from imap_tools import MailBox, AND


load_dotenv()

def listen_mail_imap():
    email_user = os.getenv("MAIL_USERNAME")
    email_password = os.getenv("MAIL_PASSWORD")

    with MailBox('imap.gmail.com').login(email_user, email_password, 'Inbox') as mb:
        for msg in mb.fetch(AND(from_='noreply@mail.bydfi.com', seen=False, subject='[BYDFi] Login Email'), reverse=True, mark_seen=False, limit=1):
            email_body = msg.html
            if email_body:
                soup = BeautifulSoup(email_body, 'html.parser')
                email_text = soup.get_text()
                print("following is bydfi 2fa html email in text format")
                print(email_text)
                otp_pattern = r"is(\d{6})"
                match = re.search(otp_pattern, email_text)
                if match:
                    otp_code = match.group(1)
                    print(f"Found OTP: {otp_code}")
                    return otp_code
                else:
                    print("OTP not found in this email.")
        else:
            print("Email body is empty.")
    
# (.venv) hari@vivobook:$  cat requirements.txt 
# beautifulsoup4==4.13.5
# imap-tools==1.11.0
# python-dotenv==1.1.1
# soupsieve==2.8
# typing_extensions==4.15.0
# (.venv) hari@vivobook:$

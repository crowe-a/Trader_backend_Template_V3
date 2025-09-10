from O365 import Account
import re
from backend.config import CLIENT_ID,CLIENT_SECRET

def extract_code(body):
    # Önce Türkçe format
    match = re.search(r"Doğrulama kodu:\s*(\d{6})", body)
    if match:
        return match.group(1)

    # Sonra İngilizce format
    match = re.search(r"verification code is\s*(\d{6})", body, re.IGNORECASE)
    if match:
        return match.group(1)

    return None
def checkmail():

    try:
        credentials = (CLIENT_ID, CLIENT_SECRET)
        account = Account(credentials)

        if not account.is_authenticated:
            account.authenticate(
                scopes=['https://graph.microsoft.com/Mail.Read'],
                redirect_uri='https://login.microsoftonline.com/common/oauth2/nativeclient'
            )

        mailbox = account.mailbox()
        inbox = mailbox.inbox_folder()

        messages = inbox.get_messages(limit=5, order_by='receivedDateTime DESC')

        verification_code = None

        for message in messages:
            body = message.get_body_text() or ""
            verification_code = extract_code(body)
            if verification_code:
                
                break

        if verification_code:
            print("verification code:", verification_code)
        else:
            print("Kod not found.")
        return verification_code
    except:
        print("mail not found")
# checkmail()
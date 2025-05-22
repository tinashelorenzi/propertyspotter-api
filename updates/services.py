from twilio.rest import Client
from django.conf import settings

class WhatsAppService:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER
        self.client = Client(self.account_sid, self.auth_token)

    def send_message(self, to_number, message):
        """
        Send a WhatsApp message using Twilio.
        
        Args:
            to_number (str): Recipient's phone number in E.164 format (e.g., +1234567890)
            message (str): Message content to send
            
        Returns:
            dict: Response containing message SID and status
        """
        try:
            # Format the phone numbers for WhatsApp
            from_whatsapp = f"{self.from_number}"
            to_whatsapp = f"{to_number}"

            # Send the message
            message = self.client.messages.create(
                from_=from_whatsapp,
                body=message,
                to=to_whatsapp
            )

            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 
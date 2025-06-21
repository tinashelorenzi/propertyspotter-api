import requests
from django.conf import settings

def verify_turnstile_token(token, ip_address=None):
    """
    Verify Cloudflare Turnstile token
    """
    verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    
    data = {
        'secret': settings.TURNSTILE_SECRET_KEY,
        'response': token,
    }
    
    if ip_address:
        data['remoteip'] = ip_address
    
    try:
        response = requests.post(verify_url, data=data, timeout=10)
        result = response.json()
        return result.get('success', False)
    except requests.RequestException:
        return False
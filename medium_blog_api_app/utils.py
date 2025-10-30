## validate images size and type(jpg, png, jpeg)
import random
from django.core.mail import send_mail
from django.forms import ValidationError
import math
from django.core.exceptions import ValidationError

def estimate_read_time(text):
    """
    Estimate read-time in minutes (200 wpm).
    """
    if not text:
        return 0
    words = len(str(text).split())
    minutes = math.ceil(words / 200)
    return max(1, minutes)


def validate_image(image):
    allowed_extensions = ['jpg', 'png', 'jpeg']
    image_extension = image.name.split('.')[-1].lower()
    if image_extension not in allowed_extensions:
        raise ValidationError(f"Invalid image format. Allowed formats: {', '.join(allowed_extensions)}")
    
    if image.size > 2 * 1024 * 1024:
        raise ValidationError("Image size should not exceed 2MB.")
    
## Generate random OTP (6 digit)
def generate_otp():
    return str(random.randint(100000, 999999))

## Send OTP email
def send_otp_email(email, otp):
    """
    Send an email with an OTP to the given email address.

    Parameters:
    email (str): The email address to which the OTP should be sent.
    otp (str): The OTP to be sent.

    Returns:
    bool: True if the email is sent successfully, False otherwise.
    """
    subject = "Your OTP Code"
    message = f"Your OTP for password reset is: {otp}. It will expire in 10 minutes."
    from_email = "vishalsohaliya25@gmail.com"
    try:
        send_mail(subject, message, from_email, [email])
        return True
    except Exception as e:
        print("Email send failed:", str(e))
        return False
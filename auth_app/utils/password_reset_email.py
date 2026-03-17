from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)

def send_password_reset_email(user, uid, token):
    reset_link = f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uid}&token={token}"
    subject = "Reset your Password"
    try:
        validate_email(user.email)
        recipient = user.email
    except (ValidationError, TypeError):
        recipient = settings.DEFAULT_FROM_EMAIL 
        
    def trySendEmail(recipient):
        html_content = render_to_string("emails/password_reset.html", {
            "user": user,
            "reset_link": reset_link,
        })
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Hi {user.username},\n\nPlease click the link below to reset your password:\n{reset_link}\n\nIf you did not request a password reset, please ignore this email.\n\nBest regards,\nVideoflix Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    
    try:
        trySendEmail(recipient)
    except Exception as e:
        logger.error("Error send failed to %s: %s", recipient, e)
        if recipient != settings.DEFAULT_FROM_EMAIL:
            try:
                logger.info("fallinf back to default email")
                trySendEmail(settings.DEFAULT_FROM_EMAIL)
            except Exception as fallback_error:
                logger.error("Fallback email also failed: %s", fallback_error)
                raise ConnectionError("All email attempts failed")
    return True 
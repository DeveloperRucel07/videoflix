from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


def send_activation_email(request, user, uid, token):
    activation_link = f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uid}&token={token}"
    subject = "Activate Videoflix account"
    try:
        validate_email(user.email)
        recipient = user.email
    except (ValidationError, TypeError):
        recipient = settings.DEFAULT_FROM_EMAIL
    body = f"Hi {user.username},\n\nPlease click the link below to activate your Videoflix account:\n{activation_link}\n\nIf you did not register for an account, please ignore this email.\n\nBest regards,\nVideoflix Team"

    html_content = render_to_string(
        "emails/activate.html", {"user": user, "activation_link": activation_link,},
    )

    def trySendEmail(recipient):
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
    
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



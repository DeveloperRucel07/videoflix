from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_password_reset_email(user, uid, token):
    reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
    subject = "Reset your Password"
    try:
        html_content = render_to_string("emails/password_reset.html", {
            "user": user,
            "reset_link": reset_link,
        })
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Hi {user.email},\n\nPlease click the link below to reset your password:\n{reset_link}\n\nIf you did not request a password reset, please ignore this email.\n\nBest regards,\nVideoflix Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        return True
    except Exception as e:
        raise ConnectionError(f"Failed to send password reset email: {e}")

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_password_reset_email(user, uid, token):
    reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
    subject = "Reset your Password"

    html_content = render_to_string("emails/password_reset.html", {
        "user": user,
        "reset_link": reset_link,
    })

    email = EmailMultiAlternatives(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

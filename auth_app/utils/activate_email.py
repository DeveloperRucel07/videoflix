from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings



def send_activation_email(request, user, uid, token):
    activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
    subject = "Activate Videoflix account"
    body = f"Hi {user.email},\n\nPlease click the link below to activate your Videoflix account:\n{activation_link}\n\nIf you did not register for an account, please ignore this email.\n\nBest regards,\nVideoflix Team"
    try:
        html_content = render_to_string(
            "emails/activate.html",
            {
                "user": user,
                "activation_link": activation_link,
            },
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True

    except Exception as e:
        raise ConnectionError(f"Failed to send activation email: {e}")

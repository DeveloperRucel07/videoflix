from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings



def send_activation_email(request, user, uid, token):

    activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"

    subject = "Confirm your email"
    
    html_content = render_to_string("emails/activate.html", {
        "user": user,
        "activation_link": activation_link,
    })

    email = EmailMultiAlternatives(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

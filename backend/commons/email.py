"""Send email method."""
from django.core.mail import send_mail


def send_email(email, subject, content):
    """Sending email with subject, recieption and email content."""
    try:
        send_mail(subject, content, 'nkluan91@gmail.com', [email], fail_silently=False)
        print('successfully')
    except:
        print('failed')

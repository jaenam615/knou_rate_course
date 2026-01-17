import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

"""
Sends a verification email to the specified email address using SendGrid.
"""


def send_verification_email(to_email: str, verify_url: str) -> None:
    message = Mail(
        from_email=os.environ["FROM_EMAIL"],
        to_emails=to_email,
        subject="Verify your email",
        html_content=f"""
        <p>Please verify your email:</p>
        <p><a href="{verify_url}">Verify Email</a></p>
        <p>If the button doesn’t work, open this link:</p>
        <p>{verify_url}</p>
        """,
    )
    sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
    sg.send(message)

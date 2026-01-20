"""
Email sending service using SendGrid.

Sends verification emails to users during signup.
If SENDGRID_API_KEY is not configured, emails are logged but not sent.
"""

import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, verify_url: str) -> bool:
    """
    Send a verification email to the specified email address.

    Returns True if sent successfully, False if SendGrid is not configured.
    Raises exception if SendGrid is configured but sending fails.
    """
    if not settings.sendgrid_api_key:
        logger.warning(
            "SendGrid not configured. Verification email not sent to %s. "
            "Verify URL: %s",
            to_email,
            verify_url,
        )
        return False

    if not settings.from_email:
        logger.error("FROM_EMAIL not configured. Cannot send verification email.")
        return False

    message = Mail(
        from_email=settings.from_email,
        to_emails=to_email,
        subject="[방통대 꿀과목] 이메일 인증",
        html_content=f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>방통대 꿀과목 DB</h2>
            <p>안녕하세요! 가입해 주셔서 감사합니다.</p>
            <p>아래 버튼을 클릭하여 이메일을 인증해 주세요:</p>
            <p style="margin: 24px 0;">
                <a href="{verify_url}"
                   style="background-color: #4F46E5; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    이메일 인증하기
                </a>
            </p>
            <p style="color: #666; font-size: 14px;">
                버튼이 작동하지 않으면 아래 링크를 브라우저에 직접 입력해 주세요:<br>
                <a href="{verify_url}">{verify_url}</a>
            </p>
            <hr style="margin: 24px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                본 메일은 방통대 꿀과목 DB 서비스에서 발송되었습니다.
            </p>
        </div>
        """,
    )

    sg = SendGridAPIClient(settings.sendgrid_api_key)
    response = sg.send(message)

    if response.status_code >= 400:
        logger.error(
            "SendGrid returned error status %d for %s",
            response.status_code,
            to_email,
        )
        raise Exception(f"SendGrid error: {response.status_code}")

    logger.info("Verification email sent to %s", to_email)
    return True

import logging
import smtplib
from email.message import EmailMessage
from Config.config import settings
from Utils.email_token import create_email_verification_token
from Utils.security import create_password_reset_token

logger = logging.getLogger(__name__)

def sender() -> str:
    return settings.EMAIL_FROM or settings.SMTP_USER

# Helper to send the emails
def send(to_email: str, subject: str, html: str, text: str) -> None:
    msg = EmailMessage()
    msg["From"] = sender()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)

def base_template(title: str, preheader: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background-color:#0b1020;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#e6e8ef;">
  <span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;">{preheader}</span>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0b1020;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#121833;border-radius:12px;overflow:hidden;border:1px solid #1f2a4d;">
          <tr>
            <td style="padding:28px 32px;border-bottom:1px solid #1f2a4d;">
              <h1 style="margin:0;font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">
                Cypher<span style="color:#7c9cff;">Crescent</span>
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px;border-top:1px solid #1f2a4d;font-size:12px;color:#8a93b2;text-align:center;">
              You're receiving this email because an action was requested on your CypherCrescent account.<br />
              If this wasn't you, you can safely ignore this message.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

def button(href: str, label: str) -> str:
    return f"""
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <tr>
          <td style="border-radius:8px;background:#4f6cff;">
            <a href="{href}" target="_blank"
               style="display:inline-block;padding:12px 24px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:8px;">
              {label}
            </a>
          </td>
        </tr>
      </table>
    """

def send_verification_email(to_email: str, first_name: str, token: str) -> None:
    verify_url = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"

    body = f"""
      <h2 style="margin:0 0 16px 0;font-size:20px;color:#ffffff;">Verify your email, {first_name}</h2>
      <p style="margin:0 0 12px 0;font-size:15px;line-height:1.6;color:#c8cee0;">
        Welcome to CypherCrescent. Confirm this email address to activate your account
        and start managing your crypto portfolio.
      </p>
      {button(verify_url, "Verify email")}
      <p style="margin:24px 0 8px 0;font-size:13px;color:#8a93b2;">
        Or paste this link into your browser:
      </p>
      <p style="margin:0;font-size:13px;word-break:break-all;">
        <a href="{verify_url}" style="color:#7c9cff;text-decoration:none;">{verify_url}</a>
      </p>
      <p style="margin:24px 0 0 0;font-size:13px;color:#8a93b2;">
        This link will expire in {settings.EMAIL_VERIFY_EXPIRE_MINUTES} minutes.
      </p>
    """

    text = (
        f"Hi {first_name},\n\n"
        f"Confirm your CypherCrescent email by opening this link:\n{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFY_EXPIRE_MINUTES} minutes.\n"
    )

    send(
        to_email=to_email,
        subject="Verify your CypherCrescent email",
        html=base_template(
            title="Verify your email",
            preheader="Confirm your email to activate your CypherCrescent account.",
            body_html=body,
        ),
        text=text,
    )

def send_password_reset_email(to_email: str, first_name: str, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"

    body = f"""
      <h2 style="margin:0 0 16px 0;font-size:20px;color:#ffffff;">Reset your password, {first_name}</h2>
      <p style="margin:0 0 12px 0;font-size:15px;line-height:1.6;color:#c8cee0;">
        We received a request to reset the password for your CypherCrescent account.
        Click the button below to choose a new one.
      </p>
      {button(reset_url, "Reset password")}
      <p style="margin:24px 0 8px 0;font-size:13px;color:#8a93b2;">
        Or paste this link into your browser:
      </p>
      <p style="margin:0;font-size:13px;word-break:break-all;">
        <a href="{reset_url}" style="color:#7c9cff;text-decoration:none;">{reset_url}</a>
      </p>
      <p style="margin:24px 0 0 0;font-size:13px;color:#8a93b2;">
        If you didn't request a password reset, no action is needed — your password will stay the same.
      </p>
    """

    text = (
        f"Hi {first_name},\n\n"
        f"Reset your CypherCrescent password by opening this link:\n{reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes. "
        f"If you didn't request this, ignore this email.\n"
    )

    send(
        to_email=to_email,
        subject="Reset your CypherCrescent password",
        html=base_template(
            title="Reset your password",
            preheader="Use this link to reset your CypherCrescent password.",
            body_html=body,
        ),
        text=text,
    )

def send_two_factor_code_email(to_email: str, first_name: str, code: str, action: str) -> None:
    body = f"""
      <h2 style="margin:0 0 16px 0;font-size:20px;color:#ffffff;">Your verification code</h2>
      <p style="margin:0 0 12px 0;font-size:15px;line-height:1.6;color:#c8cee0;">
        Hi {first_name}, use this code to {action}:
      </p>
      <p style="margin:24px 0;font-size:34px;font-weight:700;letter-spacing:8px;color:#ffffff;">{code}</p>
      <p style="margin:0;font-size:13px;color:#8a93b2;">
        This code expires in {settings.OTP_EXPIRE_MINUTES} minutes. If you didn't request it, you can ignore this email.
      </p>
    """

    text = (
        f"Hi {first_name},\n\n"
        f"Your CypherCrescent code to {action} is: {code}\n\n"
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes. If you didn't request it, ignore this email.\n"
    )

    send(
        to_email=to_email,
        subject="Your CypherCrescent verification code",
        html=base_template(
            title="Your verification code",
            preheader="Your CypherCrescent verification code.",
            body_html=body,
        ),
        text=text,
    )

def send_two_factor_code(email: str, first_name: str, code: str, action: str) -> None:
    """Safe, background-friendly: sends the code, swallowing/logging any SMTP failure."""
    try:
        send_two_factor_code_email(email, first_name, code, action)
    except Exception as e:
        logger.exception("Failed to send 2FA code to %s: %s", email, e)

def send_verification(email: str, first_name: str) -> None:
    """Safe, background-friendly: builds the token and sends, swallowing/logging any SMTP failure."""
    try:
        token = create_email_verification_token(email)
        send_verification_email(email, first_name, token)
    except Exception as e:
        logger.exception("Failed to send verification email to %s: %s", email, e)

def send_password_reset(email: str, first_name: str, token_version: int = 0) -> None:
    """Safe, background-friendly: builds the token and sends, swallowing/logging any SMTP failure."""
    try:
        token = create_password_reset_token(email, token_version)
        send_password_reset_email(email, first_name, token)
    except Exception as e:
        logger.exception("Failed to send reset email to %s: %s", email, e)

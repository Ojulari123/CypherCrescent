import logging
import resend
from Config.config import settings
from Utils.email_token import create_email_verification_token
from Utils.security import create_password_reset_token

resend.api_key = settings.RESEND_API_KEY
logger = logging.getLogger(__name__)

# Helper to send the emails
def send(to_email: str, subject: str, html: str, text: str) -> None:
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    })

# Site colors
BRAND = "#3861fb"
INK = "#0f172a"        # headings
BODY = "#475569"       # paragraph text
MUTE = "#94a3b8"       # footer / fine print
LINE = "#e6e9f4"       # hairline borders
PAGE_BG = "#eef2fb"    # outer canvas
SOFT = "#f4f6fc"       # inset boxes
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

def base_template(title: str, preheader: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="light only" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background-color:{PAGE_BG};font-family:{FONT};color:{BODY};-webkit-font-smoothing:antialiased;">
  <span style="display:none!important;visibility:hidden;mso-hide:all;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">{preheader}</span>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{PAGE_BG};padding:40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid {LINE};">
          <!-- brand accent bar -->
          <tr><td style="height:4px;background:{BRAND};font-size:0;line-height:0;">&nbsp;</td></tr>
          <!-- header / logo lockup -->
          <tr>
            <td style="padding:28px 40px 8px 40px;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="width:42px;height:42px;background:{BRAND};border-radius:11px;text-align:center;vertical-align:middle;font-size:20px;font-weight:800;color:#ffffff;font-family:{FONT};">C</td>
                  <td style="width:12px;">&nbsp;</td>
                  <td style="font-size:18px;font-weight:700;color:{INK};letter-spacing:-0.01em;">Cypher Crescent</td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- body -->
          <tr>
            <td style="padding:24px 40px 36px 40px;">
              {body_html}
            </td>
          </tr>
          <!-- footer -->
          <tr>
            <td style="padding:24px 40px 32px 40px;border-top:1px solid {LINE};">
              <p style="margin:0 0 6px 0;font-size:13px;font-weight:600;color:{INK};">Cypher Crescent</p>
              <p style="margin:0;font-size:12px;line-height:1.6;color:{MUTE};">
                This is an automated security message about your account. If you didn't request it,
                no action is needed — you can safely ignore this email.
              </p>
            </td>
          </tr>
        </table>
        <p style="max-width:600px;margin:16px auto 0 auto;font-size:11px;color:{MUTE};text-align:center;font-family:{FONT};">
          Cypher Crescent · Crypto portfolio tracking
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""


def button(href: str, label: str) -> str:
    return f"""
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px 0;">
        <tr>
          <td align="center" bgcolor="{BRAND}" style="border-radius:10px;">
            <a href="{href}" target="_blank"
               style="display:inline-block;padding:14px 30px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:10px;font-family:{FONT};">
              {label}
            </a>
          </td>
        </tr>
      </table>
    """

def fallback_link(href: str) -> str:
    return f"""
      <p style="margin:24px 0 8px 0;font-size:13px;color:{MUTE};">Or paste this link into your browser:</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{SOFT};border:1px solid {LINE};border-radius:8px;">
        <tr><td style="padding:12px 14px;font-size:12px;word-break:break-all;">
          <a href="{href}" style="color:{BRAND};text-decoration:none;">{href}</a>
        </td></tr>
      </table>
    """

def heading(text: str) -> str:
    return f'<h1 style="margin:0 0 14px 0;font-size:22px;line-height:1.3;font-weight:700;color:{INK};letter-spacing:-0.01em;">{text}</h1>'

def paragraph(text: str) -> str:
    return f'<p style="margin:0 0 14px 0;font-size:15px;line-height:1.65;color:{BODY};">{text}</p>'

def note(text: str) -> str:
    return f'<p style="margin:24px 0 0 0;font-size:13px;line-height:1.6;color:{MUTE};">{text}</p>'

def send_verification_email(to_email: str, first_name: str, token: str) -> None:
    verify_url = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"

    body = (
        heading(f"Confirm your email, {first_name}")
        + paragraph(
            "Welcome to Cypher Crescent. Confirm this address to finish setting up your account — "
            "then you can start tracking prices, building a watchlist, and following your portfolio."
        )
        + button(verify_url, "Confirm email address")
        + fallback_link(verify_url)
        + note(f"This link expires in {settings.EMAIL_VERIFY_EXPIRE_MINUTES} minutes for your security.")
    )

    text = (
        f"Hi {first_name},\n\n"
        f"Welcome to Cypher Crescent. Confirm your email to finish setting up your account:\n{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFY_EXPIRE_MINUTES} minutes.\n\n"
        f"If you didn't create an account, you can ignore this email.\n"
    )

    send(
        to_email=to_email,
        subject="Confirm your email · Cypher Crescent",
        html=base_template(
            title="Confirm your email",
            preheader="Confirm your email to finish setting up your Cypher Crescent account.",
            body_html=body,
        ),
        text=text,
    )

def send_password_reset_email(to_email: str, first_name: str, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"

    body = (
        heading(f"Reset your password, {first_name}")
        + paragraph(
            "We got a request to reset the password on your Cypher Crescent account. "
            "Choose a new password using the button below."
        )
        + button(reset_url, "Choose a new password")
        + fallback_link(reset_url)
        + note(
            f"This link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes. "
            "Didn't request this? Your password hasn't changed — you can safely ignore this email."
        )
    )

    text = (
        f"Hi {first_name},\n\n"
        f"Reset your Cypher Crescent password using this link:\n{reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes. "
        f"If you didn't request this, your password stays the same — ignore this email.\n"
    )

    send(
        to_email=to_email,
        subject="Reset your password · Cypher Crescent",
        html=base_template(
            title="Reset your password",
            preheader="Choose a new password for your Cypher Crescent account.",
            body_html=body,
        ),
        text=text,
    )

def send_two_factor_code_email(to_email: str, first_name: str, code: str, action: str) -> None:
    code_block = f"""
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <tr>
          <td style="background:{SOFT};border:1px solid {LINE};border-radius:12px;padding:18px 28px;font-size:34px;font-weight:700;letter-spacing:10px;color:{INK};font-family:'SFMono-Regular',Consolas,Menlo,monospace;">
            {code}
          </td>
        </tr>
      </table>
    """

    body = (
        heading("Your verification code")
        + paragraph(f"Hi {first_name}, use this code to {action}:")
        + code_block
        + note(
            f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes. "
            "Never share it — Cypher Crescent will never ask you for this code."
        )
    )

    text = (
        f"Hi {first_name},\n\n"
        f"Your Cypher Crescent code to {action} is: {code}\n\n"
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes. Never share this code with anyone.\n"
    )

    send(
        to_email=to_email,
        subject=f"{code} is your Cypher Crescent code",
        html=base_template(
            title="Your verification code",
            preheader=f"Your verification code is {code}.",
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

def _fmt_price(p: float) -> str:
    """Smart price formatting: fewer decimals for large coins, more for micro-caps."""
    if p >= 1_000:
        return f"${p:,.2f}"
    if p >= 1:
        return f"${p:,.4f}"
    return f"${p:,.6f}"


def send_price_alert_email(
    to_email: str,
    first_name: str,
    coin_name: str,
    coin_slug: str,
    direction: str,
    target_price: float,
    current_price: float,
) -> None:
    is_above = direction == "above"
    arrow       = "↑" if is_above else "↓"
    direction_label = "risen above" if is_above else "fallen below"
    accent      = "#16a34a" if is_above else "#dc2626"   # green / red
    accent_bg   = "#f0fdf4" if is_above else "#fef2f2"
    accent_line = "#bbf7d0" if is_above else "#fecaca"
    badge_label = "ABOVE TARGET" if is_above else "BELOW TARGET"

    coin_url = f"{settings.FRONTEND_URL.rstrip('/')}/coins/{coin_slug}"

    fmt_current = _fmt_price(current_price)
    fmt_target  = _fmt_price(target_price)

    price_block = f"""
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px 0;width:100%;">
        <tr>
          <td style="background:{accent_bg};border:1px solid {accent_line};border-radius:14px;padding:24px;">
            <!-- badge -->
            <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom:18px;">
              <tr>
                <td style="background:{accent};border-radius:6px;padding:4px 10px;font-size:11px;font-weight:700;letter-spacing:0.06em;color:#ffffff;font-family:{FONT};">
                  {arrow} {badge_label}
                </td>
              </tr>
            </table>
            <!-- prices -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="48%" style="border-right:1px solid {accent_line};padding-right:20px;">
                  <p style="margin:0 0 4px 0;font-size:12px;font-weight:600;color:{accent};text-transform:uppercase;letter-spacing:0.05em;">Current price</p>
                  <p style="margin:0;font-size:28px;font-weight:700;color:{INK};font-family:'SFMono-Regular',Consolas,Menlo,monospace;">{fmt_current}</p>
                </td>
                <td width="4%">&nbsp;</td>
                <td width="48%" style="padding-left:20px;">
                  <p style="margin:0 0 4px 0;font-size:12px;font-weight:600;color:{MUTE};text-transform:uppercase;letter-spacing:0.05em;">Your target</p>
                  <p style="margin:0;font-size:28px;font-weight:700;color:{MUTE};font-family:'SFMono-Regular',Consolas,Menlo,monospace;">{fmt_target}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    """

    body = (
        heading(f"Your {coin_name} alert fired 🔔")
        + paragraph(
            f"Hi {first_name} — <strong>{coin_name}</strong> has {direction_label} your target of "
            f"<strong>{fmt_target}</strong>. The current market price is <strong>{fmt_current}</strong>."
        )
        + price_block
        + button(coin_url, f"View {coin_name}")
        + note(
            "This alert has been marked as triggered and no longer counts toward your 10-alert limit. "
            "Head to your alerts page to set a new one."
        )
    )

    text = (
        f"Hi {first_name},\n\n"
        f"{arrow} {coin_name} price alert triggered.\n\n"
        f"Current price: {fmt_current}\n"
        f"Your target:   {fmt_target} ({direction})\n\n"
        f"View on Cypher Crescent: {coin_url}\n\n"
        f"This alert has been marked as triggered. You can set a new one from the alerts page.\n"
    )

    send(
        to_email=to_email,
        subject=f"{arrow} {coin_name} hit {fmt_current} · Cypher Crescent",
        html=base_template(
            title="Price alert triggered",
            preheader=f"{coin_name} has {direction_label} your target of {fmt_target}.",
            body_html=body,
        ),
        text=text,
    )

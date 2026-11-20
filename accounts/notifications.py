"""
Email OTP Delivery Service for Invenpro
Sends secure One-Time Passwords (OTP) for Admin and Developer password recovery
via Django's email subsystem (Gmail SMTP or local console fallback in development).
"""
import sys
from pathlib import Path
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def _read_env_value(key):
    """Reads a fresh value directly from project .env so edits take effect immediately."""
    try:
        env_path = Path(settings.BASE_DIR) / '.env'
        if not env_path.exists():
            return ''
        for raw_line in env_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return ''


def send_email_otp(user, email_address, otp_code):
    """
    Sends a styled HTML + Plaintext OTP email via configured Django EMAIL_BACKEND.
    """
    subject = f"Invenpro Password Reset OTP: {otp_code}"
    display_name = user.get_full_name() or user.username
    text_body = (
        f"Hello {display_name},\n\n"
        f"Your 6-digit Invenpro password reset OTP is: {otp_code}\n"
        f"This code expires in 10 minutes.\n\n"
        f"If you did not request this password reset, you can safely ignore this message.\n\n"
        f"— Invenpro Security Team"
    )
    html_body = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; background: #f7f8f5; border-radius: 16px;">
      <div style="background: linear-gradient(135deg, #064E3B, #09261D); padding: 20px; border-radius: 12px; text-align: center; color: #ffffff;">
        <h2 style="margin: 0; font-size: 22px;">Inven<span style="color: #c4fa03;">pro</span></h2>
        <p style="margin: 4px 0 0; font-size: 12px; opacity: 0.85;">Inventory Management System · Security Verification</p>
      </div>
      <div style="background: #ffffff; padding: 24px; border-radius: 12px; margin-top: 16px; border: 1px solid #e2e6e3;">
        <p style="margin-top: 0; color: #17231F;">Hello <strong>{display_name}</strong>,</p>
        <p style="color: #4b5563; font-size: 14px;">Use the 6-digit One-Time Password (OTP) below to reset your Invenpro account password:</p>
        <div style="text-align: center; margin: 22px 0;">
          <span style="display: inline-block; font-family: monospace; font-size: 30px; font-weight: 800; letter-spacing: 8px; padding: 12px 24px; background: #E8F5E9; color: #064E3B; border-radius: 10px; border: 1px solid #10B981;">{otp_code}</span>
        </div>
        <p style="color: #6b7280; font-size: 12px; margin-bottom: 0;">This OTP is valid for <strong>10 minutes</strong>. Do not share it with anyone.</p>
      </div>
    </div>
    """

    is_smtp = settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
    try:
        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [email_address])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        return {
            'sent_live': is_smtp,
            'provider': 'SMTP Email (Gmail)' if is_smtp else 'Local Console Email (SMTP not configured in .env)',
            'error': '',
        }
    except Exception as exc:
        return {
            'sent_live': False,
            'provider': 'SMTP Email',
            'error': str(exc),
        }

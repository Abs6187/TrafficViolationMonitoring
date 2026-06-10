from typing import Tuple

from config import Settings

try:
    from twilio.rest import Client
except Exception:  # pragma: no cover - optional dependency at runtime
    Client = None


def send_violation_sms(numberplate: str, recipient: str = "") -> Tuple[bool, str]:
    if not Settings.ENABLE_TWILIO:
        return False, "notification skipped: Twilio integration is disabled"

    destination = (recipient or Settings.DEFAULT_NOTIFICATION_TO).strip()
    if not destination:
        return False, "notification skipped: no destination phone number configured"

    if not all([Settings.TWILIO_ACCOUNT_SID, Settings.TWILIO_AUTH_TOKEN, Settings.TWILIO_FROM_NUMBER]):
        return False, "notification skipped: Twilio credentials are not fully configured"

    if Client is None:
        return False, "notification skipped: twilio package is unavailable"

    try:
        client = Client(Settings.TWILIO_ACCOUNT_SID, Settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Traffic violation detected for {numberplate}. Please review the generated e-challan.",
            from_=Settings.TWILIO_FROM_NUMBER,
            to=destination,
        )
        return True, f"message queued with sid {message.sid}"
    except Exception as exc:
        return False, f"notification failed: {exc}"

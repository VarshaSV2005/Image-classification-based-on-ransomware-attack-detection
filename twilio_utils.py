# twilio_utils.py — Final utilities (SMS, CALL, WhatsApp, Lookup, Video token)
import os
import logging
from typing import Optional

logger = logging.getLogger("twilio_utils")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Lazy import Twilio so import-time errors are clearer
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    from twilio.jwt.access_token import AccessToken
    from twilio.jwt.access_token.grants import VideoGrant
except Exception:
    Client = None
    TwilioRestException = Exception
    AccessToken = None
    VideoGrant = None


# -------------------------
# Helper: get Twilio client
# -------------------------
def get_twilio_client():
    if Client is None:
        raise RuntimeError("twilio package not installed in this environment.")
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise RuntimeError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment.")
    return Client(account_sid, auth_token)


# -------------------------
# Unified response helper
# -------------------------
def _ok_result(**kwargs):
    d = {"ok": True}
    d.update(kwargs)
    return d

def _err_result(message: str, code: Optional[int] = None, status: Optional[int] = None):
    r = {"ok": False, "message": str(message)}
    if code is not None:
        r["code"] = code
    if status is not None:
        r["status"] = status
    return r


# -------------------------
# SEND SMS
# -------------------------
def send_sms(to: str, body: str, from_number: Optional[str] = None):
    """
    Send SMS. Expects 'to' and 'from_number' in E.164.
    Returns dict: {"ok": True, "sid": "..."} or {"ok": False, "message": "...", "code": int}
    """
    try:
        client = get_twilio_client()
        from_number = from_number or os.environ.get("TWILIO_NUMBER")
        if not from_number:
            return _err_result("TWILIO_NUMBER environment variable not set.")
        msg = client.messages.create(body=body, from_=from_number, to=to)
        logger.info(f"SMS sent SID={msg.sid} to={to}")
        return _ok_result(sid=msg.sid)
    except TwilioRestException as e:
        logger.error(f"Twilio SMS error: code={getattr(e, 'code', None)} msg={e}")
        return _err_result(str(e), code=getattr(e, "code", None), status=getattr(e, "status", None))
    except Exception as e:
        logger.exception("Unexpected error sending SMS")
        return _err_result(e)


# -------------------------
# MAKE CALL (Inline TwiML)
# -------------------------
def make_call(to: str, twiml_inline: str, from_number: Optional[str] = None):
    """
    Make a voice call using inline TwiML. 'to' and 'from_number' must be E.164.
    Returns dict with ok/sid or ok=False and error info.
    """
    try:
        client = get_twilio_client()
        from_number = from_number or os.environ.get("TWILIO_NUMBER")
        if not from_number:
            return _err_result("TWILIO_NUMBER environment variable not set.")
        call = client.calls.create(to=to, from_=from_number, twiml=twiml_inline)
        logger.info(f"Call placed SID={call.sid} to={to}")
        return _ok_result(sid=call.sid)
    except TwilioRestException as e:
        logger.error(f"Twilio call error: code={getattr(e,'code',None)} msg={e}")
        return _err_result(str(e), code=getattr(e, "code", None), status=getattr(e, "status", None))
    except Exception as e:
        logger.exception("Unexpected error making call")
        return _err_result(e)


# -------------------------
# WHATSAPP (text & media)
# -------------------------
def send_whatsapp_text(to_whatsapp: str, body: str, from_whatsapp: Optional[str] = None):
    """
    Send WhatsApp text. 'to_whatsapp' should be 'whatsapp:+<number>'.
    """
    try:
        client = get_twilio_client()
        from_whatsapp = from_whatsapp or os.environ.get("TWILIO_WHATSAPP_NUMBER")
        if not from_whatsapp:
            return _err_result("TWILIO_WHATSAPP_NUMBER env var not set.")
        msg = client.messages.create(body=body, from_=from_whatsapp, to=to_whatsapp)
        logger.info(f"WhatsApp text SID={msg.sid} to={to_whatsapp}")
        return _ok_result(sid=msg.sid)
    except TwilioRestException as e:
        logger.error(f"Twilio WhatsApp error: code={getattr(e,'code',None)} msg={e}")
        return _err_result(str(e), code=getattr(e, "code", None), status=getattr(e, "status", None))
    except Exception as e:
        logger.exception("Unexpected WhatsApp send error")
        return _err_result(e)


def send_whatsapp_media(to_whatsapp: str, media_url: str, caption: Optional[str] = None, from_whatsapp: Optional[str] = None):
    try:
        client = get_twilio_client()
        from_whatsapp = from_whatsapp or os.environ.get("TWILIO_WHATSAPP_NUMBER")
        if not from_whatsapp:
            return _err_result("TWILIO_WHATSAPP_NUMBER env var not set.")
        msg = client.messages.create(body=caption or "", from_=from_whatsapp, to=to_whatsapp, media_url=[media_url])
        logger.info(f"WhatsApp media SID={msg.sid} to={to_whatsapp}")
        return _ok_result(sid=msg.sid)
    except TwilioRestException as e:
        logger.error(f"Twilio WhatsApp media error: code={getattr(e,'code',None)} msg={e}")
        return _err_result(str(e), code=getattr(e, "code", None), status=getattr(e, "status", None))
    except Exception as e:
        logger.exception("Unexpected WhatsApp media error")
        return _err_result(e)


# -------------------------
# LOOKUP (Phone validation)
# -------------------------
def lookup_number(phone_number: str, fetch_carrier: bool = False):
    """
    Uses Twilio Lookup API to validate a number. Returns dict on success or error dict.
    On success returns {ok: True, phone_number: ..., national_format: ..., carrier: {...} }
    """
    try:
        client = get_twilio_client()
        if fetch_carrier:
            num = client.lookups.v1.phone_numbers(phone_number).fetch(type=["carrier"])
        else:
            num = client.lookups.v1.phone_numbers(phone_number).fetch()
        info = {
            "phone_number": getattr(num, "phone_number", None),
            "national_format": getattr(num, "national_format", None),
            "carrier": getattr(num, "carrier", None)
        }
        logger.info(f"Lookup success for {phone_number}: {info}")
        return _ok_result(**info)
    except TwilioRestException as e:
        logger.error(f"Twilio lookup error: code={getattr(e,'code',None)} msg={e}")
        return _err_result(str(e), code=getattr(e, "code", None), status=getattr(e, "status", None))
    except Exception as e:
        logger.exception("Unexpected lookup error")
        return _err_result(e)


# -------------------------
# VIDEO TOKEN (optional)
# -------------------------
def generate_video_token(identity: str, ttl: int = 3600):
    """
    Generate a Twilio Access Token with Video grant.
    Requires TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET in env.
    Returns dict with ok/jwt or error.
    """
    if AccessToken is None or VideoGrant is None:
        return _err_result("twilio.jwt not available in this environment (install twilio>=6.x).")
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    api_key = os.environ.get("TWILIO_API_KEY_SID")
    api_secret = os.environ.get("TWILIO_API_KEY_SECRET")
    if not (account_sid and api_key and api_secret):
        return _err_result("TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID and TWILIO_API_KEY_SECRET required.")
    try:
        token = AccessToken(account_sid, api_key, api_secret, identity=identity, ttl=ttl)
        token.add_grant(VideoGrant())
        jwt = token.to_jwt().decode("utf-8")
        logger.info(f"Generated video token for identity={identity}")
        return _ok_result(jwt=jwt)
    except Exception as e:
        logger.exception("Failed to generate video token")
        return _err_result(e)


# -------------------------
# Trial account warnings
# -------------------------
def twilio_trial_warnings():
    warnings = []
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    if sid.startswith("AC"):
        warnings.append("If your account is TRIAL: you can only send/call to verified numbers.")
    if not os.environ.get("TWILIO_NUMBER"):
        warnings.append("TWILIO_NUMBER env var not set. Set your Twilio phone number.")
    if not os.environ.get("TWILIO_AUTH_TOKEN") or not os.environ.get("TWILIO_ACCOUNT_SID"):
        warnings.append("Twilio credentials missing: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set.")
    return warnings

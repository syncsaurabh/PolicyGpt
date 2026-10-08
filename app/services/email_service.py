import concurrent.futures
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Bounded thread pool executor for background email dispatching
_email_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=5,
    thread_name_prefix="policygpt-email-worker"
)


class EmailService:
    """Service for sending emails via SMTP (Gmail TLS)."""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email via Gmail SMTP using TLS.
        Supports HTML and optional plain-text multipart payload.
        Gracefully handles unconfigured credentials and connection/auth/TLS errors.
        """
        if not to_email:
            logger.warning("[SMTP Dispatcher] No recipient email address provided.")
            return False

        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.info(
                f"[SMTP Dispatcher] SMTP credentials not configured. Skipping email to {to_email}. Subject: '{subject}'"
            )
            return False

        from_email = settings.SMTP_FROM or settings.SMTP_USERNAME

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            if html_content:
                msg.attach(MIMEText(html_content, "html", "utf-8"))

            host = settings.SMTP_HOST or "smtp.gmail.com"
            port = settings.SMTP_PORT or 587

            # Connect to SMTP server with a reasonable timeout
            with smtplib.SMTP(host=host, port=port, timeout=15) as server:
                server.ehlo()
                if settings.SMTP_TLS:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()

                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"[SMTP Dispatcher] Email successfully dispatched to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            err_detail = getattr(e, "smtp_error", None)
            if isinstance(err_detail, bytes):
                err_text = err_detail.decode("utf-8", errors="ignore")
            elif isinstance(err_detail, str):
                err_text = err_detail
            else:
                err_text = str(e)
            logger.error(f"[SMTP Dispatcher] Authentication failed when sending to {to_email}: {err_text}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(
                f"[SMTP Dispatcher] Connection failed to {settings.SMTP_HOST}:{settings.SMTP_PORT} for {to_email}: {str(e)}"
            )
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"[SMTP Dispatcher] Recipient refused for {to_email}: {str(e)}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"[SMTP Dispatcher] Server unexpectedly disconnected for {to_email}: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"[SMTP Dispatcher] SMTP error occurred when sending to {to_email}: {str(e)}")
            return False
        except TimeoutError as e:
            logger.error(f"[SMTP Dispatcher] Connection timed out when sending to {to_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"[SMTP Dispatcher] Unexpected failure sending email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_email_background(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> None:
        """
        Dispatch an email asynchronously in a dedicated worker thread,
        ensuring the caller HTTP request is never blocked.
        """
        def _task():
            try:
                EmailService.send_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                )
            except Exception as ex:
                logger.error(f"[SMTP Dispatcher Background] Unexpected failure sending email to {to_email}: {str(ex)}")

        _email_executor.submit(_task)


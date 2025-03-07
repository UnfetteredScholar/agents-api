import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import getLogger
from os import getenv

from core.config import settings
from dotenv import load_dotenv

load_dotenv()


# def send_email(subject: str, body: str, receiver_email: str) -> None:
#     """
#     Sends an email to a receiver

#     Args:
#         subject: the email subject
#         body: the email body
#         receiver_email: the receiver email
#     """
#     logger = getLogger(__name__)
#     sender_email = getenv("EMAIL_ACCOUNT")
#     sender_password = getenv("EMAIL_PASSWORD")
#     mail_server = getenv("SMTP_HOST")
#     port = int(getenv("SMTP_PORT"))

#     html_body = body
#     # Set up the MIME
#     email_msg = MIMEMultipart()
#     email_msg["From"] = sender_email
#     email_msg["To"] = receiver_email
#     email_msg["Subject"] = subject

#     # Attach the message to the email
#     email_msg.attach(MIMEText(html_body, "html"))

#     context = ssl.create_default_context()

#     # Try to log in to server and send email
#     try:
#         logger.info("Started SMTP")
#         server = smtplib.SMTP(mail_server, port)
#         server.ehlo()
#         server.starttls(context=context)  # Secure the connection
#         server.ehlo()
#         server.login(sender_email, sender_password)
#         text = email_msg.as_string()
#         server.sendmail(sender_email, receiver_email, text)
#         logger.info("Sent email")
#     except Exception as ex:
#         logger.error(ex)
#         raise ex
#     finally:
#         logger.info("SMTP quit")
#         server.quit()


def send_email(subject: str, body: str, receiver_email: str) -> None:
    """
    Sends an email to a receiver

    Args:
        subject: the email subject
        body: the email body
        receiver_email: the receiver email
    """
    logger = getLogger(__name__ + ".send_email")
    try:
        sender_email = settings.EMAIL_ACCOUNT
        sender_password = settings.EMAIL_PASSWORD
        server = settings.SMTP_HOST
        port = settings.SMTP_PORT

        html_body = body
        # Set up the MIME
        email_msg = MIMEMultipart()
        email_msg["From"] = sender_email
        email_msg["To"] = receiver_email
        email_msg["Subject"] = subject

        # Attach the message to the email
        email_msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(server, port, context=context) as server:
            server.login(sender_email, sender_password)
            text = email_msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
        logger.info("Sent Email")
    except Exception as ex:
        logger.error(ex)
        raise ex


def send_agent_request(
    primary_goal: str,
    function_description: str,
    integrations: str,
    deployment_platform: str,
    additional_comments: str,
    company: str = "",
):
    logger = getLogger(__name__ + ".send_agent_request")
    try:
        ai_details = {
            "primary_goal": primary_goal,
            "function_description": function_description,
            "integrations": integrations,
            "deployment_platform": deployment_platform,
            "additional_comments": additional_comments,
        }

        # Read HTML template and replace placeholders
        html_template = """\
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Agent Details</title>
        </head>
        <body>
            <div class="container">
                <h2>AI Agent Overview</h2>

                <h3>Primary Goal:</h3>
                <p>{primary_goal}</p>

                <h3>Function Description:</h3>
                <p>{function_description}</p>

                <h3>Integrations:</h3>
                <p>{integrations}</p>

                <h3>Deployment Platform:</h3>
                <p>{deployment_platform}</p>

                <h3>Additional Comments:</h3>
                <p>{additional_comments}</p>

                <div class="footer">
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Fill in template with actual data
        html_content = html_template.format(**ai_details)
        subject = f"{company} : New Agent Request"

        send_email(
            subject=subject,
            body=html_content,
            receiver_email="n.brown@4th-ir.com",
        )
    except Exception as ex:
        logger.error(ex)
        raise ex

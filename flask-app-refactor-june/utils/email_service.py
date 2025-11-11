"""Email service for sending transactional emails

NOTE: This is a placeholder implementation. In production, you should:
1. Configure a real email service (SendGrid, AWS SES, Mailgun, etc.)
2. Use environment variables for API keys
3. Add proper error handling and retry logic
4. Create HTML email templates
"""
import os
from flask import current_app, url_for


class EmailService:
    """Email service for sending verification and notification emails"""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize email service with app config"""
        self.email_enabled = app.config.get('EMAIL_ENABLED', False)
        self.from_email = app.config.get('EMAIL_FROM', 'noreply@draftmode.app')
        self.app_name = app.config.get('APP_NAME', 'Draft Mode')

    def _send_email(self, to_email, subject, body_text, body_html=None):
        """
        Send email via configured service

        In production, implement this with your email provider:
        - SendGrid: https://sendgrid.com/docs/API_Reference/api_v3.html
        - AWS SES: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html
        - Mailgun: https://documentation.mailgun.com/en/latest/api-sending.html
        """
        if not self.email_enabled:
            # In development, just log the email
            print(f"\n{'='*60}")
            print(f"EMAIL SIMULATION (Email service not configured)")
            print(f"{'='*60}")
            print(f"To: {to_email}")
            print(f"From: {self.from_email}")
            print(f"Subject: {subject}")
            print(f"\n{body_text}")
            print(f"{'='*60}\n")
            return True

        # TODO: Implement actual email sending
        # Example with SendGrid:
        # import sendgrid
        # from sendgrid.helpers.mail import Mail
        #
        # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        # message = Mail(
        #     from_email=self.from_email,
        #     to_emails=to_email,
        #     subject=subject,
        #     plain_text_content=body_text,
        #     html_content=body_html
        # )
        # response = sg.send(message)
        # return response.status_code == 202

        return True

    def send_verification_email(self, user, verification_token):
        """Send email verification link to new user"""
        verification_url = url_for(
            'auth.verify_email',
            token=verification_token,
            _external=True
        )

        subject = f"Verify your {self.app_name} account"

        body_text = f"""
Welcome to {self.app_name}!

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account with {self.app_name}, please ignore this email.

Best regards,
The {self.app_name} Team
"""

        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Welcome to {self.app_name}!</h2>
    <p>Please verify your email address by clicking the button below:</p>
    <p style="margin: 30px 0;">
        <a href="{verification_url}"
           style="background-color: #28a745; color: white; padding: 12px 24px;
                  text-decoration: none; border-radius: 4px; display: inline-block;">
            Verify Email Address
        </a>
    </p>
    <p>Or copy and paste this link into your browser:</p>
    <p style="color: #666; font-size: 14px;">{verification_url}</p>
    <p style="color: #666; font-size: 12px; margin-top: 30px;">
        This link will expire in 24 hours.<br>
        If you didn't create an account with {self.app_name}, please ignore this email.
    </p>
</body>
</html>
"""

        return self._send_email(user.email, subject, body_text, body_html)

    def send_password_reset_email(self, user, reset_token):
        """Send password reset link to user"""
        reset_url = url_for(
            'auth.reset_password',
            token=reset_token,
            _external=True
        )

        subject = f"Reset your {self.app_name} password"

        body_text = f"""
Hi {user.name},

We received a request to reset your password for {self.app_name}.

Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email. Your password will remain unchanged.

Best regards,
The {self.app_name} Team
"""

        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Reset Your Password</h2>
    <p>Hi {user.name},</p>
    <p>We received a request to reset your password for {self.app_name}.</p>
    <p style="margin: 30px 0;">
        <a href="{reset_url}"
           style="background-color: #007bff; color: white; padding: 12px 24px;
                  text-decoration: none; border-radius: 4px; display: inline-block;">
            Reset Password
        </a>
    </p>
    <p>Or copy and paste this link into your browser:</p>
    <p style="color: #666; font-size: 14px;">{reset_url}</p>
    <p style="color: #666; font-size: 12px; margin-top: 30px;">
        This link will expire in 1 hour.<br>
        If you didn't request a password reset, please ignore this email.
    </p>
</body>
</html>
"""

        return self._send_email(user.email, subject, body_text, body_html)

    def send_password_changed_notification(self, user):
        """Send notification when password is successfully changed"""
        subject = f"Your {self.app_name} password was changed"

        body_text = f"""
Hi {user.name},

This is a confirmation that your password for {self.app_name} was successfully changed.

If you didn't make this change, please contact us immediately.

Best regards,
The {self.app_name} Team
"""

        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Password Changed</h2>
    <p>Hi {user.name},</p>
    <p>This is a confirmation that your password for {self.app_name} was successfully changed.</p>
    <p style="color: #dc3545; font-weight: bold;">
        If you didn't make this change, please contact us immediately.
    </p>
</body>
</html>
"""

        return self._send_email(user.email, subject, body_text, body_html)


# Create global instance
email_service = EmailService()

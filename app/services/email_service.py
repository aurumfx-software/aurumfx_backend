import os
import resend
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")

resend.api_key = RESEND_API_KEY


def send_registration_email(
    to_email: str,
    user_id: str,
):
    try:
        response = resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": "Registration Successful",
            "html": f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.6;">

                    <h2>Registration Successful</h2>

                    <p>Dear User,</p>

                    <p>
                        Your account has been successfully registered.
                    </p>

                    <p>
                        Your User ID is:
                    </p>

                    <h2 style="letter-spacing: 1px;">
                        {user_id}
                    </h2>

                    <p>
                        Please keep this User ID safe. You can use it
                        to log in and access your account.
                    </p>

                    <p>
                        Thank you for joining us.
                    </p>

                    <p>
                        Regards,<br>
                        Your Team
                    </p>

                </div>
            """
        })

        return response

    except Exception as e:
        print(f"Registration email failed: {str(e)}")
        return None
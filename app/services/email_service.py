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
    first_name: str,
    last_name: str | None,
    joining_date: str,
    enroller_id: str | None,
    password: str,
    plan_type: str = "14%",
):
    try:

        # ======================================================
        # USER NAME
        # ======================================================

        full_name = first_name

        if last_name:
            full_name = f"{first_name} {last_name}"


        # ======================================================
        # ENROLLER
        # ======================================================

        enroller = enroller_id if enroller_id else "N/A"


        # ======================================================
        # INVESTMENT PLAN MESSAGE
        # ======================================================

        if plan_type == "14%":

            investment_message = """
                <p>
                    At AurumFX, we offer a structured
                    <strong>10-month gold trading investment cycle</strong>
                    with the applicable plan terms communicated to you at
                    the time of investment.
                </p>
            """

        elif plan_type == "8%":

            investment_message = """
                <p>
                    At AurumFX, we offer a structured
                    <strong>30-month gold trading investment cycle</strong>
                    with the applicable plan terms communicated to you at
                    the time of investment.
                </p>
            """

        else:

            investment_message = """
                <p>
                    Your investment plan details will be communicated
                    separately based on your selected investment plan.
                </p>
            """


        # ======================================================
        # EMAIL
        # ======================================================

        response = resend.Emails.send({

            "from": RESEND_FROM_EMAIL,

            "to": [to_email],

            "subject": "Welcome to AurumFX - Your Account Details",

            "html": f"""
<!DOCTYPE html>

<html>

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

</head>


<body style="
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    font-family: Arial, Helvetica, sans-serif;
">


<div style="
    max-width: 700px;
    margin: 30px auto;
    background: #ffffff;
    padding: 35px;
    border-radius: 10px;
">


    <!-- HEADER -->

    <div style="
        text-align: center;
        margin-bottom: 30px;
    ">

        <h1 style="
            margin: 0;
            font-size: 28px;
        ">
            AurumFX
        </h1>

        <p style="
            margin-top: 8px;
            font-size: 14px;
        ">
            Gold Trading & Investment
        </p>

    </div>


    <!-- GREETING -->

    <h2>
        Dear {full_name},
    </h2>


    <p>
        A Warm Welcome to AurumFX,
    </p>


    <p>
        We are pleased to inform you that you have been
        successfully onboarded as an investor with AurumFX.
    </p>


    <p>
        Thank you for choosing AurumFX. We are committed to
        providing you with professional service and support
        throughout your investment journey.
    </p>


    <!-- ACCOUNT DETAILS -->

    <div style="
        background-color: #f7f7f7;
        padding: 20px;
        margin: 25px 0;
        border-radius: 8px;
    ">

        <h3>
            Account Details
        </h3>


        <p>
            <strong>Investor ID:</strong>
            {user_id}
        </p>


        <p>
            <strong>Name:</strong>
            {full_name}
        </p>


        <p>
            <strong>Joining Date:</strong>
            {joining_date}
        </p>


        <p>
            <strong>Enroller ID:</strong>
            {enroller}
        </p>


        <p>
            <strong>Login Password:</strong>
            {password}
        </p>

    </div>


    <!-- INVESTMENT -->

    <h3>
        Your Investment Journey
    </h3>

    {investment_message}


    <p>
        We will provide you with regular updates regarding
        your investment performance and account activity.
    </p>


    <p>
        Our support team is available to assist you with
        any questions or concerns regarding your account.
    </p>


    <p>
        Thank you for choosing AurumFX.
        We look forward to serving you.
    </p>


    <!-- FOOTER -->

    <div style="
        margin-top: 35px;
        padding-top: 20px;
        border-top: 1px solid #eeeeee;
    ">

        <p>
            Best regards,
        </p>

        <p>
            <strong>Team AurumFX</strong>
        </p>

    </div>


</div>

</body>

</html>
            """
        })

        print(
            f"Registration email sent successfully to {to_email}"
        )

        return response


    except Exception as e:

        print(
            f"Registration email failed: {str(e)}"
        )

        return None
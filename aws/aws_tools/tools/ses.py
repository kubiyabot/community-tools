from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

ses_send_email = AWSCliTool(
    name="ses_send_email",
    description="Send an email using AWS SES with optional attachments",
    content="""
# Create temporary raw email message
TMP_EMAIL="/tmp/raw_email_$RANDOM.txt"

# Create the raw email message
cat > $TMP_EMAIL << EOF
From: $sender
To: $recipients
Subject: $subject
MIME-Version: 1.0
Content-Type: ${attachment_path:+multipart/mixed}${attachment_path:-text/plain}; ${attachment_path:+boundary="NextPart"}charset=UTF-8

${attachment_path:+--NextPart
Content-Type: text/plain; charset=UTF-8}

$body

${attachment_path:+
--NextPart
Content-Type: application/octet-stream
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="$(basename $attachment_path)"

$(if [ -f "$attachment_path" ]; then base64 "$attachment_path"; else echo "Error: Attachment file not found"; exit 1; fi)

--NextPart--}
EOF

# Send the email
aws ses send-raw-email \
    --region $region \
    --profile $account_id \
    --raw-message "file://$TMP_EMAIL"

# Clean up
rm -f $TMP_EMAIL""",
    args=[
        Arg(name="account_id", type="str", description="AWS profile/account to use", required=True),
        Arg(name="region", type="str", description="AWS Region for SES", required=True),
        Arg(name="sender", type="str", description="Email address of the sender", required=True),
        Arg(name="recipients", type="str", description="Comma-separated list of recipient email addresses", required=True),
        Arg(name="subject", type="str", description="Email subject", required=True),
        Arg(name="body", type="str", description="Email body content", required=True),
        Arg(name="attachment_path", type="str", description="Path to file to attach", required=False),
    ],
)

tool_registry.register("aws", ses_send_email) 
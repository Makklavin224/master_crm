"""QR code generation for manual payment requisites.

Generates QR codes containing phone number (for SBP transfer) or card number
(for card-to-card transfer). Clients scan with their banking app.

Note: There is no universal SBP deeplink format for P2P transfers.
Each bank has its own scheme. Encoding the phone number as plain text
is the practical approach -- banking apps recognize phone numbers for SBP.
"""

import base64
import io

import qrcode


def generate_payment_qr(
    data: str,
    box_size: int = 8,
    border: int = 2,
) -> str:
    """Generate a QR code and return as base64-encoded PNG.

    Args:
        data: Phone number ("+79161234567") or card number ("2200123456789012").
        box_size: Size of each QR code box in pixels.
        border: Border width in boxes.

    Returns:
        Base64 string suitable for <img src="data:image/png;base64,...">
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("utf-8")

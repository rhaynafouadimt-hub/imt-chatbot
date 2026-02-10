import requests

FORM_URL = "https://www.imt.sn/contact"

HEADERS = {
    "User-Agent": "IMT-Chatbot/1.0",
    "Content-Type": "application/x-www-form-urlencoded"
}

def submit_contact_form(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    question: str,
    source: str
) -> dict:
    payload = {
        "prenom": first_name,
        "nom": last_name,
        "email": email,
        "telephone": phone,
        "question": question,
        "source": source,
        "verification": "2"
    }

    try:
        response = requests.post(
            FORM_URL,
            data=payload,
            headers=HEADERS,
            timeout=10
        )

        return {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "captcha_present": "captcha" in response.text.lower()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

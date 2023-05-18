import requests
import frappe
from requests.auth import HTTPBasicAuth
from .config.mpesa_config import consumer_key, consumer_secret

class MpesaClient:
    base_url = "https://sandbox.safaricom.co.ke"
    token_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    b2c_url = f"{base_url}/mpesa/b2c/v1/paymentrequest"

    def __init__(self):
        self.token = self.get_access_token()

    def get_access_token(self):
        try:
            response = requests.get(self.token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        except (requests.RequestException, ValueError) as err:
            frappe.throw(_("Error obtaining access token: {0}").format(str(err)))

        return response.json().get('access_token')

    def make_request(self, endpoint, method="POST", data={}):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(method, endpoint, headers=headers, json=data)
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        except (requests.RequestException, ValueError) as err:
            frappe.throw(_("Request failed: {0}").format(str(err)))

        return response.json()

    def b2c_payment(self, data):
        try:
            response_data = self.make_request(self.b2c_url, data=data)

            # create a new Mpesa Transaction document
            doc = frappe.get_doc({
                "doctype": "Mpesa Transaction",
                "transaction_id": response_data.get('Result', {}).get('TransactionID'),
                "amount": data.get('Amount'),
                "transaction_date": frappe.utils.now_datetime(),
                "phone_number": data.get('PartyB')
            })
            doc.insert()

        except Exception as e:
            frappe.throw(_("An error occurred while processing the payment: {0}").format(str(e)))
        else:
            frappe.msgprint(_("Payment processed successfully! Transaction ID: {0}").format(doc.transaction_id))

        return response_data

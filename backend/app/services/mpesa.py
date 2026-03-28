import base64
import secrets
from datetime import datetime
from typing import Optional

import httpx

from ..config import get_settings

settings = get_settings()

MPESA_BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class MpesaService:
    def __init__(self):
        self.base_url = MPESA_BASE_URLS.get(
            settings.environment, MPESA_BASE_URLS["sandbox"]
        )
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def _get_auth_header(self) -> str:
        credentials = f"{settings.mpesa_consumer_key}:{settings.mpesa_consumer_secret}"
        return base64.b64encode(credentials.encode()).decode()

    async def get_access_token(self) -> str:
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers={"Authorization": f"Basic {self._get_auth_header()}"},
            )

        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")

        data = response.json()
        self._access_token = data.get("access_token", "")
        expires_in = int(data.get("expires_in", 3600))
        self._token_expiry = datetime.now().replace(
            microsecond=0
        )
        from datetime import timedelta
        self._token_expiry = self._token_expiry + timedelta(seconds=expires_in - 60)

        return self._access_token

    def _generate_password(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{settings.mpesa_shortcode}{settings.mpesa_passkey}{timestamp}"
        return base64.b64encode(password_str.encode()).decode()

    def _generate_transaction_id(self) -> str:
        return secrets.token_hex(10).upper()

    async def stk_push(
        self,
        amount: int,
        phone: str,
        account_reference: str,
        transaction_desc: str = "School Fee Payment",
    ) -> dict:
        access_token = await self.get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = self._generate_password()
        transaction_id = self._generate_transaction_id()

        payload = {
            "BusinessShortCode": settings.mpesa_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": settings.mpesa_shortcode,
            "PhoneNumber": phone,
            "CallBackURL": settings.mpesa_callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

        if response.status_code not in (200, 201):
            raise Exception(f"STK Push failed: {response.text}")

        return {
            "response_code": response.json().get("ResponseCode"),
            "response_desc": response.json().get("ResponseDescription"),
            "merchant_id": response.json().get("MerchantRequestID"),
            "checkout_id": response.json().get("CheckoutRequestID"),
            "customer_message": response.json().get("CustomerMessage"),
            "transaction_id": transaction_id,
        }

    async def stk_status(self, checkout_request_id: str) -> dict:
        access_token = await self.get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = self._generate_password()

        payload = {
            "BusinessShortCode": settings.mpesa_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

        if response.status_code not in (200, 201):
            raise Exception(f"STK Status query failed: {response.text}")

        return response.json()


mpesa_service = MpesaService()

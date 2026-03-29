"""
M-Pesa Daraja 2.0 API Integration Service
Handles STK Push, callbacks, and transaction queries
"""
import base64
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx

from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Daraja API Base URLs
MPESA_BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class MpesaService:
    """
    M-Pesa Daraja 2.0 API Service
    
    Handles:
    - OAuth token generation and caching
    - STK Push (Lipa Na M-Pesa Online)
    - STK Push query
    - Callback processing
    """
    
    def __init__(self):
        self.environment = settings.environment
        self.base_url = MPESA_BASE_URLS.get(self.environment, MPESA_BASE_URLS["sandbox"])
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        # Log initialization
        logger.info(f"MpesaService initialized in {self.environment} mode")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Callback URL: {settings.mpesa_callback_url}")

    def _get_auth_header(self) -> str:
        """Generate Basic Auth header for OAuth"""
        credentials = f"{settings.mpesa_consumer_key}:{settings.mpesa_consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded

    def _generate_password(self, timestamp: str) -> str:
        """
        Generate password for STK Push
        Password = Base64.encode(BusinessShortCode + Passkey + Timestamp)
        """
        password_str = f"{settings.mpesa_shortcode}{settings.mpesa_passkey}{timestamp}"
        return base64.b64encode(password_str.encode()).decode()

    def _generate_timestamp(self) -> str:
        """Generate timestamp in format: YYYYMMDDHHmmss"""
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def _generate_transaction_id(self) -> str:
        """Generate unique transaction reference"""
        return f"TXN{secrets.token_hex(8).upper()}"

    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number to 254XXXXXXXXX format
        Accepts: 0712345678, +254712345678, 254712345678, 712345678
        """
        phone = phone.strip().replace(" ", "").replace("-", "")
        
        if phone.startswith("+"):
            phone = phone[1:]
        
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif phone.startswith("7") or phone.startswith("1"):
            phone = "254" + phone
        
        # Validate length
        if len(phone) != 12:
            raise ValueError(f"Invalid phone number format: {phone}")
        
        return phone

    async def get_access_token(self) -> str:
        """
        Get OAuth access token from Daraja API
        Caches token until expiry
        """
        # Return cached token if still valid
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            logger.debug("Using cached access token")
            return self._access_token

        logger.info("Requesting new access token from Daraja API")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                    headers={"Authorization": f"Basic {self._get_auth_header()}"},
                )
                
                logger.debug(f"OAuth Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"OAuth failed: {response.text}")
                    raise Exception(f"Failed to get access token: {response.text}")

                data = response.json()
                self._access_token = data.get("access_token", "")
                expires_in = int(data.get("expires_in", 3600))
                
                # Set expiry with 60 second buffer
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                
                logger.info(f"Access token obtained, expires in {expires_in}s")
                return self._access_token
                
        except httpx.RequestError as e:
            logger.error(f"Network error getting access token: {str(e)}")
            raise Exception(f"Network error: {str(e)}")

    async def stk_push(
        self,
        amount: int,
        phone: str,
        account_reference: str,
        transaction_desc: str = "School Fee Payment",
    ) -> Dict[str, Any]:
        """
        Initiate STK Push (Lipa Na M-Pesa Online)
        
        Args:
            amount: Amount in KES (minimum 1, maximum 150000)
            phone: Customer phone number
            account_reference: Reference shown on M-Pesa message (e.g., invoice number)
            transaction_desc: Description of the transaction
            
        Returns:
            dict with: response_code, merchant_id, checkout_id, etc.
        """
        # Format phone number
        formatted_phone = self._format_phone_number(phone)
        
        # Validate amount
        if amount < 1 or amount > 150000:
            raise ValueError("Amount must be between 1 and 150,000 KES")
        
        # Get access token
        access_token = await self.get_access_token()
        
        # Generate timestamp and password
        timestamp = self._generate_timestamp()
        password = self._generate_password(timestamp)
        
        # Prepare payload
        payload = {
            "BusinessShortCode": settings.mpesa_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": formatted_phone,
            "PartyB": settings.mpesa_shortcode,
            "PhoneNumber": formatted_phone,
            "CallBackURL": settings.mpesa_callback_url,
            "AccountReference": account_reference[:20],  # Max 20 chars
            "TransactionDesc": transaction_desc[:13],    # Max 13 chars
        }
        
        logger.info(f"Initiating STK Push: {formatted_phone}, KES {amount}, Ref: {account_reference}")
        logger.debug(f"Callback URL: {settings.mpesa_callback_url}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                )
                
                logger.info(f"STK Push Response Status: {response.status_code}")
                logger.debug(f"STK Push Response: {response.text}")
                
                response_data = response.json()
                
                if response.status_code not in (200, 201):
                    error_msg = response_data.get("errorMessage", response.text)
                    logger.error(f"STK Push failed: {error_msg}")
                    raise Exception(f"STK Push failed: {error_msg}")
                
                result = {
                    "response_code": response_data.get("ResponseCode"),
                    "response_desc": response_data.get("ResponseDescription"),
                    "merchant_id": response_data.get("MerchantRequestID"),
                    "checkout_id": response_data.get("CheckoutRequestID"),
                    "customer_message": response_data.get("CustomerMessage"),
                    "transaction_id": self._generate_transaction_id(),
                }
                
                logger.info(f"STK Push initiated: CheckoutRequestID={result['checkout_id']}")
                return result
                
        except httpx.RequestError as e:
            logger.error(f"Network error during STK Push: {str(e)}")
            raise Exception(f"Network error: {str(e)}")

    async def stk_query(self, checkout_request_id: str) -> Dict[str, Any]:
        """
        Query STK Push transaction status
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
            
        Returns:
            dict with ResultCode, ResultDesc, etc.
        """
        access_token = await self.get_access_token()
        timestamp = self._generate_timestamp()
        password = self._generate_password(timestamp)
        
        payload = {
            "BusinessShortCode": settings.mpesa_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }
        
        logger.info(f"Querying STK status: {checkout_request_id}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/mpesa/stkpushquery/v1/query",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                )
                
                logger.debug(f"STK Query Response: {response.text}")
                
                if response.status_code not in (200, 201):
                    raise Exception(f"STK Query failed: {response.text}")
                
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Network error during STK Query: {str(e)}")
            raise Exception(f"Network error: {str(e)}")

    def parse_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse M-Pesa callback data
        
        Returns parsed data with:
            - success: bool
            - checkout_request_id: str
            - result_code: int
            - result_desc: str
            - mpesa_receipt: str (if successful)
            - amount: float (if successful)
            - phone: str (if successful)
            - transaction_date: str (if successful)
        """
        try:
            body = callback_data.get("Body", {})
            stk_callback = body.get("stkCallback", {})
            
            result = {
                "success": False,
                "checkout_request_id": stk_callback.get("CheckoutRequestID"),
                "merchant_request_id": stk_callback.get("MerchantRequestID"),
                "result_code": stk_callback.get("ResultCode"),
                "result_desc": stk_callback.get("ResultDesc"),
            }
            
            # Result code 0 means success
            if result["result_code"] == 0:
                result["success"] = True
                
                # Extract callback metadata
                metadata = stk_callback.get("CallbackMetadata", {})
                items = metadata.get("Item", [])
                
                for item in items:
                    name = item.get("Name")
                    value = item.get("Value")
                    
                    if name == "Amount":
                        result["amount"] = value
                    elif name == "MpesaReceiptNumber":
                        result["mpesa_receipt"] = value
                    elif name == "TransactionDate":
                        result["transaction_date"] = str(value)
                    elif name == "PhoneNumber":
                        result["phone"] = str(value)
            
            logger.info(f"Callback parsed: success={result['success']}, receipt={result.get('mpesa_receipt')}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing callback: {str(e)}")
            raise


# Singleton instance
mpesa_service = MpesaService()

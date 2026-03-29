from app.services.mpesa import stk_push


def initiate_payment(phone: str, amount: int):
    """
    Handles payment initiation logic.
    Later: save to DB before sending STK
    """
    response = stk_push(phone, amount)

    return {
        "status": "pending",
        "message": "STK push sent to user",
        "data": response
    }


def process_callback(callback_data: dict):
    """
    Handles M-Pesa callback processing.
    Extracts useful fields.
    """
    try:
        stk_callback = callback_data["Body"]["stkCallback"]

        result_code = stk_callback["ResultCode"]
        result_desc = stk_callback["ResultDesc"]

        metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

        parsed_data = {item["Name"]: item.get("Value") for item in metadata}

        return {
            "result_code": result_code,
            "result_desc": result_desc,
            "amount": parsed_data.get("Amount"),
            "mpesa_receipt": parsed_data.get("MpesaReceiptNumber"),
            "phone": parsed_data.get("PhoneNumber")
        }

    except Exception as e:
        return {"error": str(e)}
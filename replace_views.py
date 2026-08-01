import re

with open('agricore/views.py', 'r') as f:
    content = f.read()

# We want to replace everything from `class WhatsAppWebhookView(APIView):` to the end of the file.
new_class = """from twilio.rest import Client

class WhatsAppWebhookView(APIView):
    \"\"\"
    FR-01: WhatsApp Conversational Advisory Interface.
    Handles incoming messages from Twilio Sandbox
    \"\"\"

    @swagger_auto_schema(
        operation_description="Twilio WhatsApp API Webhook Receiver. Processes incoming messages.",
        responses={
            200: openapi.Response(description="Webhook processed successfully")
        }
    )
    def post(self, request):
        # Twilio sends form-encoded data
        body = request.data
        
        incoming_msg = body.get('Body', '').strip()
        from_number = body.get('From', '')
        profile_name = body.get('ProfileName', '')
        num_media = int(body.get('NumMedia', '0'))
        
        # Determine message type
        if num_media > 0:
            incoming_msg = "[Image Uploaded]"
            msg_type = "image"
        else:
            msg_type = "text"

        if not from_number or not incoming_msg:
            return Response({"error": "Missing message or sender"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Strip "whatsapp:" if present in the from_number for internal storage, but keep it for replies
        db_phone = from_number.replace('whatsapp:', '')

        print(f"SECURE LOG: Webhook Received from phone: {db_phone} (Sender Profile Name: '{profile_name}')")  

        # get / create farmer (FR-11: Implicit onboarding) 
        farmer, created = Farmer.objects.get_or_create(phone_number=db_phone)

        if created or not farmer.name:
            if profile_name:
                farmer.name = profile_name
                farmer.save()
        
        # Log Farmer's Message (FR-01: History Retention)
        Conversation.objects.create(
            farmer=farmer,
            message_text=incoming_msg,
            sender_type='Farmer'
        )

        from .state_machine import process_message

        # We pass get_ai_response into the state machine for the Ask a Question state
        payloads_to_send = process_message(farmer, incoming_msg, message_type=msg_type, ai_func=get_ai_response)

        # Deliver response(s) back to farmer via Twilio WhatsApp API
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
        
        if not account_sid or not auth_token or not twilio_number:
            print("ERROR: Twilio credentials not set. Cannot reply.")
            return Response({"status": "processed, but unable to reply (missing credentials)"}, status=status.HTTP_200_OK)

        client = Client(account_sid, auth_token)

        # Send all payloads sequentially
        for partial_payload in payloads_to_send:
            # Twilio doesn't use the JSON payload format, we just send text
            out_msg = partial_payload.get("text", {}).get("body", "[Text Message]")
            
            try:
                message = client.messages.create(
                    body=out_msg,
                    from_=twilio_number,
                    to=from_number
                )
                print(f"Twilio message sent: {message.sid}")
            except Exception as e:
                print(f"ERROR: Failed to send Twilio message: {e}")

            # Log AI response sent back
            Conversation.objects.create(
                farmer=farmer,
                message_text=out_msg,
                sender_type='AI'
            )

        # Twilio requires a 200 OK response
        return Response({"status": "success"}, status=status.HTTP_200_OK)
"""

# Replace
pattern = r"class WhatsAppWebhookView\(APIView\):.*"
new_content = re.sub(pattern, new_class, content, flags=re.DOTALL)

with open('agricore/views.py', 'w') as f:
    f.write(new_content)

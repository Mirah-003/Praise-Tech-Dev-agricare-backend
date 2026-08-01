import os

new_code = """import datetime
from django.utils import timezone
from .models import HealthCase

# States
STATE_WELCOME = 'WELCOME'
STATE_ASK_NAME = 'ASK_NAME'
STATE_ASK_BIRD_TYPE = 'ASK_BIRD_TYPE'
STATE_ASK_BIRD_AGE = 'ASK_BIRD_AGE'
STATE_ASK_FLOCK_SIZE = 'ASK_FLOCK_SIZE'
STATE_ASK_LOCATION = 'ASK_LOCATION'
STATE_ASK_IOT = 'ASK_IOT'
STATE_ASK_IOT_ID = 'ASK_IOT_ID'
STATE_MAIN_MENU = 'MAIN_MENU'
STATE_HEALTH_CHECK_ASK_SYMPTOMS = 'HEALTH_CHECK_ASK_SYMPTOMS'
STATE_HEALTH_CHECK_UPLOAD_PHOTO = 'HEALTH_CHECK_UPLOAD_PHOTO'
STATE_HEALTH_CHECK_TREATMENT_PLAN = 'HEALTH_CHECK_TREATMENT_PLAN'
STATE_CONSULTATION_RATING = 'CONSULTATION_RATING'
STATE_CONSULTATION_COMMENT = 'CONSULTATION_COMMENT'
STATE_WEATHER = 'WEATHER'
STATE_ASK_QUESTION = 'ASK_QUESTION'

def create_text_message(text):
    return {
        "type": "text",
        "text": {"body": text}
    }

def create_button_message(text, buttons):
    menu_text = text + "\\n\\n"
    for i, btn_text in enumerate(buttons, 1):
        menu_text += f"{i}. {btn_text}\\n"
    menu_text += "\\n(Reply with the number)"
    return create_text_message(menu_text.strip())

def create_list_message(text, button_text, title, options):
    menu_text = f"{title}\\n{text}\\n\\n"
    for i, opt in enumerate(options, 1):
        menu_text += f"{i}. {opt}\\n"
    menu_text += "\\n(Reply with the number)"
    return create_text_message(menu_text.strip())

def get_ai_response_mock(farmer, message_text):
    pass

def process_message(farmer, incoming_msg, message_type="text", ai_func=None):
    state = farmer.conversation_state
    msg_lower = incoming_msg.lower().strip() if isinstance(incoming_msg, str) else ""

    # Global interrupt handling
    if msg_lower in ['menu', 'home', 'start']:
        if farmer.is_onboarded:
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return [
                create_text_message("What would you like to do today?"),
                create_list_message("Select an option below:", "Menu", "Options", 
                ["Health Check", "Reminders", "Alerts", "Dashboard", "Weather", "Ask a Question"])
            ]
        else:
            farmer.conversation_state = STATE_WELCOME
            farmer.save()

    if state == STATE_WELCOME:
        if msg_lower == "skip setup" or msg_lower == "3":
            farmer.is_onboarded = True
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return [
                create_text_message("What would you like to do today?"),
                create_list_message("Select an option below:", "Menu", "Options", 
                ["Health Check", "Reminders", "Alerts", "Dashboard", "Weather", "Ask a Question"])
            ]
        elif msg_lower in ["i'm a farmer", "i'm a veterinarian", "1", "2"]:
            farmer.role = "Farmer" if ("farmer" in msg_lower or msg_lower == "1") else "Veterinarian"
            farmer.conversation_state = STATE_ASK_NAME
            farmer.save()
            return [create_text_message("What's your name?")]
        else:
            return [
                create_text_message("👋 Hello! Welcome to AGRICARE.\\n\\nI'm your AI poultry assistant.\\nI can help you with poultry health, disease diagnosis, farm management and emergency support.\\n\\nTo get started, tell me who you are."),
                create_button_message("Choose your role:", ["I'm a Farmer", "I'm a Veterinarian", "Skip Setup"])
            ]

    elif state == STATE_ASK_NAME:
        farmer.name = incoming_msg
        farmer.conversation_state = STATE_ASK_BIRD_TYPE
        farmer.save()
        return [
            create_text_message(f"Nice to meet you, {farmer.name} 😊\\n\\nLet's set up your farm."),
            create_button_message("Ready?", ["Let's Go 🚀"])
        ]
        
    elif state == STATE_ASK_BIRD_TYPE:
        if msg_lower in ["let's go 🚀", "let's go", "1"]:
            pass
        elif incoming_msg:
            farmer.bird_type = incoming_msg
            farmer.conversation_state = STATE_ASK_BIRD_AGE
            farmer.save()
            return [create_text_message("How old are your birds?")]
            
        return [create_list_message("What type of birds do you raise?", "Select Bird Type", "Types", ["Broilers", "Layers", "Turkey", "Local Chicken", "Other"])]

    elif state == STATE_ASK_BIRD_AGE:
        farmer.bird_age = incoming_msg
        farmer.conversation_state = STATE_ASK_FLOCK_SIZE
        farmer.save()
        return [create_text_message("How many birds do you currently have?")]

    elif state == STATE_ASK_FLOCK_SIZE:
        if incoming_msg.isdigit():
            farmer.flock_size = int(incoming_msg)
        farmer.conversation_state = STATE_ASK_LOCATION
        farmer.save()
        return [create_text_message("What state is your farm located in?")]

    elif state == STATE_ASK_LOCATION:
        farmer.location = incoming_msg
        farmer.conversation_state = STATE_ASK_IOT
        farmer.save()
        return [create_button_message("Do you have a smart sensor installed on your farm?", ["✅ Yes (Connect IoT)", "Skip for now"])]

    elif state == STATE_ASK_IOT:
        if "yes" in msg_lower or msg_lower == "1":
            farmer.has_iot_device = True
            farmer.conversation_state = STATE_ASK_IOT_ID
            farmer.save()
            return [create_text_message("Please enter the Device ID printed on your sensor.")]
        else:
            farmer.has_iot_device = False
            farmer.is_onboarded = True
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return [
                create_text_message("What would you like to do today?"),
                create_list_message("Select an option below:", "Menu", "Options", 
                ["Health Check", "Reminders", "Alerts", "Dashboard", "Weather", "Ask a Question"])
            ]

    elif state == STATE_ASK_IOT_ID:
        if incoming_msg.startswith("DEV") or len(incoming_msg) > 3:
            farmer.iot_device_id = incoming_msg
            farmer.is_onboarded = True
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return [
                create_text_message("✅ Device connected successfully.\\n\\nYou'll now receive live updates for:\\n🌡 Temperature\\n💧 Humidity\\n💨 Air Quality\\n🚰 Water Level"),
                create_button_message("Proceed to Main Menu", ["Continue"])
            ]
        else:
            return [create_text_message("I couldn't find that device.\\n\\nPlease check the ID and try again.")]

    elif state == STATE_MAIN_MENU:
        if "health check" in msg_lower or msg_lower == "1":
            farmer.conversation_state = STATE_HEALTH_CHECK_ASK_SYMPTOMS
            farmer.save()
            return [create_button_message("Are your birds showing symptoms?", ["Yes", "No"])]
        elif "dashboard" in msg_lower or msg_lower == "4":
            return [
                create_text_message("📊 Farm Dashboard\\n\\n🌡 Temperature: 32°C\\n💧 Humidity: 60%\\n💨 Air Quality: Good\\n🚰 Water Level: Normal\\n\\nLast Updated: Just now"),
                create_button_message("Actions", ["Main Menu"])
            ]
        elif "weather" in msg_lower or msg_lower == "5":
            return [
                create_text_message("🌤 Today's Weather\\n\\n🌡 Temperature: 35°C\\n💧 Humidity: 70%\\n🌧 Rain Probability: 10%\\n💨 Wind: 12 km/h"),
                create_text_message("Recommendation:\\nAvoid vaccinations today due to high temperatures."),
                create_button_message("Next Steps", ["Main Menu"])
            ]
        elif "ask a question" in msg_lower or msg_lower == "6":
            farmer.conversation_state = STATE_ASK_QUESTION
            farmer.save()
            return [create_text_message("What is your question?")]
        elif "continue" in msg_lower or msg_lower == "1" or msg_lower == "main menu": # Wait, if it's main menu, handled globally
            return [
                create_text_message("What would you like to do today?"),
                create_list_message("Select an option below:", "Menu", "Options", 
                ["Health Check", "Reminders", "Alerts", "Dashboard", "Weather", "Ask a Question"])
            ]
        else:
            return [
                create_text_message("What would you like to do today?"),
                create_list_message("Select an option below:", "Menu", "Options", 
                ["Health Check", "Reminders", "Alerts", "Dashboard", "Weather", "Ask a Question"])
            ]

    elif state == STATE_HEALTH_CHECK_ASK_SYMPTOMS:
        if "yes" in msg_lower or msg_lower == "1":
            farmer.conversation_state = STATE_HEALTH_CHECK_UPLOAD_PHOTO
            farmer.save()
            return [create_text_message("Please upload a clear photo of the affected birds.")]
        else:
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return [
                create_text_message("Glad they are healthy! Returning to Main Menu..."),
                create_button_message("Next Steps", ["Main Menu"])
            ]

    elif state == STATE_HEALTH_CHECK_UPLOAD_PHOTO:
        if message_type == "image" or "simulated_image" in msg_lower:
            farmer.conversation_state = STATE_HEALTH_CHECK_TREATMENT_PLAN
            farmer.save()
            return [
                create_text_message("Thanks!\\n\\nI've analyzed the image."),
                create_text_message("Possible condition: Coccidiosis\\n\\nCommon in young birds with diarrhea and weakness."),
                create_button_message("Next Step", ["View Treatment Plan"])
            ]
        else:
            return [create_text_message("Please upload a photo so I can assist you better. If you can't, type 'menu' to go back.")]

    elif state == STATE_HEALTH_CHECK_TREATMENT_PLAN:
        if "view treatment plan" in msg_lower or msg_lower == "1":
            farmer.conversation_state = STATE_CONSULTATION_RATING
            farmer.save()
            return [
                create_text_message("Treatment Plan:\\n\\n• Separate affected birds immediately.\\n• Administer Amprolium in drinking water for 5-7 days.\\n• Ensure litter is dry and well-ventilated.\\n• Clean and disinfect waterers daily."),
                create_button_message("Would you like to speak to a veterinarian?", ["Talk to a Vet", "Back to Menu"])
            ]
        elif "talk to a vet" in msg_lower or msg_lower == "2":
            farmer.conversation_state = STATE_CONSULTATION_RATING
            farmer.save()
            return [
                create_text_message("Consultation Summary\\n\\nDiagnosis: Suspected Coccidiosis\\nRecommendations: Amprolium, litter management\\nFollow-up: 3 days\\nTimestamp: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
                create_button_message("Review", ["Rate Your Consultation"])
            ]
        else:
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return [create_button_message("Next Steps", ["Main Menu"])]

    elif state == STATE_CONSULTATION_RATING:
        if "rate" in msg_lower or msg_lower == "1":
            return [create_text_message("How was your experience with Dr. Smith? (Reply with 1-5 stars)")]
        elif incoming_msg.isdigit() and 1 <= int(incoming_msg) <= 5:
            farmer.conversation_state = STATE_CONSULTATION_COMMENT
            farmer.save()
            return [create_text_message("Write a comment (optional)")]
        else:
            return [create_text_message("Please reply with a number from 1 to 5.")]

    elif state == STATE_CONSULTATION_COMMENT:
        farmer.conversation_state = STATE_MAIN_MENU
        farmer.save()
        return [
            create_text_message("Thank you ❤️\\n\\nYour feedback helps improve our service."),
            create_text_message(f"Thank you {farmer.name} ❤️\\n\\nYour consultation has been saved.\\nYou can continue this conversation anytime."),
            create_button_message("Options", ["View Session", "Main Menu"])
        ]

    elif state == STATE_ASK_QUESTION:
        if ai_func:
            ai_response, is_high_risk = ai_func(farmer, incoming_msg)
            return [create_text_message(ai_response)]
        else:
            return [create_text_message("I am processing your question...")]

    # Fallback for unrecognized state
    farmer.conversation_state = STATE_WELCOME
    farmer.save()
    return [create_text_message("Let's start over. Welcome to AGRICARE!")]
"""

with open('agricore/state_machine.py', 'w') as f:
    f.write(new_code)

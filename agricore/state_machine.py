import datetime
from django.utils import timezone
from .models import HealthCase, Conversation

# States
STATE_WELCOME = 'WELCOME'
STATE_ASK_ROLE = 'ASK_ROLE'
STATE_ASK_NAME = 'ASK_NAME'
STATE_ASK_BIRD_TYPE = 'ASK_BIRD_TYPE'
STATE_ASK_BIRD_AGE = 'ASK_BIRD_AGE'
STATE_ASK_FLOCK_SIZE = 'ASK_FLOCK_SIZE'
STATE_ASK_LOCATION = 'ASK_LOCATION'
STATE_MAIN_MENU = 'MAIN_MENU'
STATE_CONVERSATION = 'CONVERSATION'
STATE_HEALTH_CHECK_UPLOAD_PHOTO = 'HEALTH_CHECK_UPLOAD_PHOTO'

# Symptom/disease keywords that signal the user is describing a health problem
HEALTH_KEYWORDS = [
    'sick', 'die', 'dying', 'dead', 'diarrhea', 'diarrhoea', 'blood', 'bloody',
    'cough', 'sneeze', 'swollen', 'swelling', 'not eating', 'weak', 'weakness',
    'paralysis', 'paralyzed', 'lame', 'limping', 'drop', 'dropping', 'poop',
    'watery', 'green', 'white', 'yellow', 'eye', 'discharge', 'nose', 'nasal',
    'respiratory', 'breathing', 'gasping', 'rattle', 'twisted', 'neck', 'head',
    'feather', 'loss', 'losing', 'bald', 'sore', 'wound', 'bump', 'lump',
    'wart', 'scab', 'pox', 'egg', 'laying', 'stopped', 'reduced', 'production',
    'thin', 'weight', 'appetite', 'feed', 'refuse', 'water', 'vomit',
    'symptom', 'symptoms', 'disease', 'infection', 'virus', 'bacteria',
    'help', 'problem', 'issue', 'treatment', 'medicine', 'drug', 'vaccine',
    'worm', 'parasit', 'mite', 'lice', 'foul', 'fowl', 'flu',
    # Hausa
    'zawo', 'mutu', 'ciwon', 'kaji', 'tari', 'hanci',
    # Yoruba
    'arun', 'adìẹ', 'ẹjẹ', 'omi', 'igbẹ',
    # Igbo
    'ọrịa', 'ọkụkọ', 'ọbara', 'nsị',
    # Pidgin
    'dey', 'sick', 'die', 'shit', 'chop', 'abeg', 'wetin', 'happen',
]


def create_text_message(text):
    return {
        "type": "text",
        "text": {"body": text}
    }


def create_button_message(text, buttons):
    menu_text = text + "\n\n"
    for i, btn_text in enumerate(buttons, 1):
        menu_text += f"{i}. {btn_text}\n"
    menu_text += "\n(Reply with the number)"
    return create_text_message(menu_text.strip())


def create_list_message(text, button_text, title, options):
    menu_text = f"{title}\n{text}\n\n"
    for i, opt in enumerate(options, 1):
        menu_text += f"{i}. {opt}\n"
    menu_text += "\n(Reply with the number)"
    return create_text_message(menu_text.strip())


def looks_like_health_problem(text):
    """Check if the user's message contains health-related keywords."""
    text_lower = text.lower()
    match_count = sum(1 for kw in HEALTH_KEYWORDS if kw in text_lower)
    return match_count >= 2


def get_conversation_history(farmer, limit=10):
    """
    Retrieve recent conversation history for multi-turn context.
    Returns a formatted string the AI engine can use.
    """
    recent = Conversation.objects.filter(
        farmer=farmer
    ).order_by('-timestamp')[:limit]

    # Reverse so oldest is first
    messages = list(reversed(recent))

    if not messages:
        return ""

    history_lines = []
    for msg in messages:
        role = "Farmer" if msg.sender_type == "Farmer" else "Assistant"
        history_lines.append(f"{role}: {msg.message_text}")

    return "\n".join(history_lines)


def build_ai_context(farmer, incoming_msg):
    """
    Build a rich context string for the AI engine with conversation history
    and farmer profile, so the AI can have a real conversation.
    """
    history = get_conversation_history(farmer, limit=8)

    context_parts = [
        "=== FARMER PROFILE ===",
        f"Name: {farmer.name or 'Unknown'}",
        f"Bird Type: {farmer.bird_type or 'Unknown'}",
        f"Bird Age: {farmer.bird_age or 'Unknown'}",
        f"Flock Size: {farmer.flock_size or 'Unknown'}",
        f"Location: {farmer.location or 'Unknown'}",
    ]

    if history:
        context_parts.append("\n=== CONVERSATION HISTORY ===")
        context_parts.append(history)

    context_parts.append(f"\n=== CURRENT MESSAGE ===")
    context_parts.append(f"Farmer: {incoming_msg}")

    return "\n".join(context_parts)


def map_bird_type(msg_lower):
    """Map numbered input or text to a bird type."""
    mapping = {
        "1": "Broilers", "broilers": "Broilers",
        "2": "Layers", "layers": "Layers",
        "3": "Turkey", "turkey": "Turkey",
        "4": "Local Chicken", "local chicken": "Local Chicken", "local": "Local Chicken",
        "5": "Other", "other": "Other",
    }
    return mapping.get(msg_lower)


def process_message(farmer, incoming_msg, message_type="text", ai_func=None):
    state = farmer.conversation_state
    msg_lower = incoming_msg.lower().strip() if isinstance(incoming_msg, str) else ""

    # ── Global shortcuts ──────────────────────────────────────────────
    if msg_lower in ['menu', 'home', 'start over']:
        farmer.conversation_state = STATE_MAIN_MENU
        farmer.save()
        return _show_main_menu(farmer)

    # ── WELCOME (brand new user) ──────────────────────────────────────
    if state == STATE_WELCOME:

        # If the first message is a health complaint, fast-track them
        if looks_like_health_problem(incoming_msg):
            farmer.is_onboarded = True
            farmer.conversation_state = STATE_CONVERSATION
            farmer.save()
            return _handle_ai_conversation(farmer, incoming_msg, ai_func)

        # Show welcome message
        farmer.conversation_state = STATE_ASK_ROLE
        farmer.save()
        return [
            create_text_message(
                "👋 Hello! Welcome to AGRICARE.\n\n"
                "I'm your AI poultry health assistant.\n"
                "I can help you diagnose diseases, recommend treatments, "
                "and manage your farm.\n\n"
                "Let's get you set up quickly (takes 30 seconds)."
            ),
            create_button_message(
                "What best describes you?",
                ["Farmer", "Veterinarian", "Skip Setup"]
            )
        ]

    # ── ASK_ROLE ──────────────────────────────────────────────────────
    elif state == STATE_ASK_ROLE:
        if msg_lower in ["3", "skip", "skip setup"]:
            farmer.is_onboarded = True
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return _show_main_menu(farmer)

        if msg_lower in ["1", "farmer"]:
            farmer.role = "Farmer"
        elif msg_lower in ["2", "veterinarian", "vet"]:
            farmer.role = "Veterinarian"
        else:
            farmer.role = "Farmer"  # Default assumption

        farmer.conversation_state = STATE_ASK_NAME
        farmer.save()
        return [create_text_message("What's your name?")]

    # ── ASK_NAME ──────────────────────────────────────────────────────
    elif state == STATE_ASK_NAME:
        farmer.name = incoming_msg.title()
        farmer.conversation_state = STATE_ASK_BIRD_TYPE
        farmer.save()
        return [
            create_list_message(
                "What type of birds do you raise?",
                "Select Bird Type", f"Nice to meet you, {farmer.name}! 😊",
                ["Broilers", "Layers", "Turkey", "Local Chicken", "Other"]
            )
        ]

    # ── ASK_BIRD_TYPE ─────────────────────────────────────────────────
    elif state == STATE_ASK_BIRD_TYPE:
        bird = map_bird_type(msg_lower)
        if bird:
            farmer.bird_type = bird
            farmer.conversation_state = STATE_ASK_BIRD_AGE
            farmer.save()
            return [create_text_message(
                f"Great, {bird}! 🐔\n\n"
                "How old are your birds?\n"
                "(e.g. '3 weeks', '2 months', '1 year')"
            )]
        else:
            # Accept free-text bird type
            farmer.bird_type = incoming_msg.title()
            farmer.conversation_state = STATE_ASK_BIRD_AGE
            farmer.save()
            return [create_text_message(
                "Got it!\n\nHow old are your birds?\n"
                "(e.g. '3 weeks', '2 months', '1 year')"
            )]

    # ── ASK_BIRD_AGE ──────────────────────────────────────────────────
    elif state == STATE_ASK_BIRD_AGE:
        farmer.bird_age = incoming_msg
        farmer.conversation_state = STATE_ASK_FLOCK_SIZE
        farmer.save()
        return [create_text_message("How many birds do you currently have?")]

    # ── ASK_FLOCK_SIZE ────────────────────────────────────────────────
    elif state == STATE_ASK_FLOCK_SIZE:
        if incoming_msg.isdigit():
            farmer.flock_size = int(incoming_msg)
        else:
            # Try to extract a number from the text
            import re
            nums = re.findall(r'\d+', incoming_msg)
            if nums:
                farmer.flock_size = int(nums[0])
        farmer.conversation_state = STATE_ASK_LOCATION
        farmer.save()
        return [create_text_message(
            "Where is your farm located?\n"
            "(State or city, e.g. 'Kano', 'Lagos', 'Ibadan')"
        )]

    # ── ASK_LOCATION ──────────────────────────────────────────────────
    elif state == STATE_ASK_LOCATION:
        farmer.location = incoming_msg.title()
        farmer.is_onboarded = True
        farmer.conversation_state = STATE_MAIN_MENU
        farmer.save()
        return [
            create_text_message(
                f"✅ All set, {farmer.name}!\n\n"
                f"📋 Your Farm Profile:\n"
                f"🐔 Birds: {farmer.bird_type}\n"
                f"📅 Age: {farmer.bird_age}\n"
                f"🔢 Flock: {farmer.flock_size}\n"
                f"📍 Location: {farmer.location}\n\n"
                "You can update this anytime by typing 'menu'."
            ),
            *_show_main_menu(farmer)
        ]

    # ── MAIN MENU ─────────────────────────────────────────────────────
    elif state == STATE_MAIN_MENU:
        # Option 1: Health Check → go to conversational AI
        if msg_lower in ["1", "health check", "health", "diagnose", "diagnosis"]:
            farmer.conversation_state = STATE_CONVERSATION
            farmer.save()
            return [create_text_message(
                "🩺 Tell me what's happening with your birds.\n\n"
                "Describe the symptoms you're seeing in your own words. "
                "For example:\n"
                "• \"My birds have watery diarrhea and are not eating\"\n"
                "• \"I found 3 dead birds this morning\"\n"
                "• \"My hens stopped laying eggs\"\n\n"
                "You can also send a photo of the affected bird."
            )]

        # Option 2: Ask a Question → also conversational AI
        elif msg_lower in ["2", "ask", "ask a question", "question"]:
            farmer.conversation_state = STATE_CONVERSATION
            farmer.save()
            return [create_text_message(
                "💬 Ask me anything about poultry care!\n\n"
                "I can help with feeding, housing, vaccination schedules, "
                "disease prevention, and more."
            )]

        # Option 3: Farm Dashboard
        elif msg_lower in ["3", "dashboard", "farm", "profile"]:
            return [
                create_text_message(
                    f"📊 Farm Dashboard — {farmer.name or 'Farmer'}\n\n"
                    f"🐔 Birds: {farmer.bird_type or 'Not set'}\n"
                    f"📅 Age: {farmer.bird_age or 'Not set'}\n"
                    f"🔢 Flock Size: {farmer.flock_size or 0}\n"
                    f"📍 Location: {farmer.location or 'Not set'}\n\n"
                    "Type 'menu' to go back."
                )
            ]

        # Option 4: Emergency
        elif msg_lower in ["4", "emergency", "urgent", "vet"]:
            farmer.conversation_state = STATE_CONVERSATION
            farmer.save()
            return [create_text_message(
                "🚨 Emergency Mode\n\n"
                "Describe what's happening urgently and I'll give you "
                "immediate first-aid steps while we alert nearby vets.\n\n"
                "What's the emergency?"
            )]

        # If user types something that looks like a health problem from the menu
        elif looks_like_health_problem(incoming_msg):
            farmer.conversation_state = STATE_CONVERSATION
            farmer.save()
            return _handle_ai_conversation(farmer, incoming_msg, ai_func)

        else:
            return _show_main_menu(farmer)

    # ── CONVERSATION (the core AI-powered dialogue) ───────────────────
    elif state == STATE_CONVERSATION:
        # Handle photo uploads
        if message_type == "image":
            return [
                create_text_message(
                    "📸 Thanks for the photo!\n\n"
                    "⚠️ Note: Full image diagnosis is coming soon. "
                    "For now, please describe what you see in words:\n"
                    "• What do the affected birds look like?\n"
                    "• Any visible sores, swelling, or discharge?\n"
                    "• What color is their droppings?"
                )
            ]

        # If user wants to go back to menu
        if msg_lower in ['menu', 'back', 'done', 'thanks', 'thank you', 'bye']:
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return [
                create_text_message("Glad I could help! 😊"),
                *_show_main_menu(farmer)
            ]

        # Core: Send to AI engine with full context
        return _handle_ai_conversation(farmer, incoming_msg, ai_func)

    # ── Fallback ──────────────────────────────────────────────────────
    else:
        # Unknown state — recover gracefully
        if farmer.is_onboarded:
            farmer.conversation_state = STATE_MAIN_MENU
            farmer.save()
            return _show_main_menu(farmer)
        else:
            farmer.conversation_state = STATE_WELCOME
            farmer.save()
            return process_message(farmer, incoming_msg, message_type, ai_func)


def _show_main_menu(farmer):
    """Render the main menu."""
    name = farmer.name or "there"
    return [
        create_text_message(
            f"Hi {name}! What can I help you with today?"
        ),
        create_list_message(
            "Choose an option below:", "Menu", "🏠 Main Menu",
            [
                "🩺 Health Check",
                "💬 Ask a Question",
                "📊 Farm Dashboard",
                "🚨 Emergency"
            ]
        )
    ]


def _handle_ai_conversation(farmer, incoming_msg, ai_func):
    """
    Send the message to the AI engine with full conversation context.
    This is where the real intelligence lives.
    """
    if not ai_func:
        return [create_text_message(
            "I'm having trouble connecting to my brain right now. "
            "Please try again in a moment."
        )]

    # Build context with conversation history for multi-turn support
    context = build_ai_context(farmer, incoming_msg)

    try:
        ai_response, is_high_risk = ai_func(farmer, context)
    except Exception as e:
        print(f"AI engine error: {e}")
        return [create_text_message(
            "Sorry, I encountered an error processing your request. "
            "Please try again or type 'menu' to go back."
        )]

    # Build response messages
    messages = [create_text_message(ai_response)]

    # If high risk, add emergency escalation
    if is_high_risk:
        messages.append(create_text_message(
            "🚨 This looks serious. Please:\n"
            "1. Isolate the affected birds immediately\n"
            "2. Contact the nearest vet clinic\n"
            "3. Do NOT sell or eat affected birds\n\n"
            "Type 'menu' when you're done, or keep describing symptoms."
        ))

        # Create a HealthCase record for vet dashboard
        try:
            HealthCase.objects.create(
                farmer=farmer,
                symptoms_summary=incoming_msg,
                ai_preliminary_diagnosis=ai_response[:500],
                severity_score=0.9,
                status='Pending'
            )
        except Exception as e:
            print(f"Failed to create HealthCase: {e}")

    return messages

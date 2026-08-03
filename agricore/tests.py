from django.test import TestCase, Client
from django.urls import reverse
from .models import Farmer, Conversation, HealthCase
from .state_machine import (
    process_message,
    looks_like_health_problem,
    map_bird_type,
    STATE_WELCOME,
    STATE_ASK_ROLE,
    STATE_ASK_NAME,
    STATE_MAIN_MENU,
    STATE_CONVERSATION,
)
from .ai_engine import AgricareAIEngine, detect_language_heuristic, run_fallback_matcher


class ModelAndStateMachineTests(TestCase):
    def setUp(self):
        self.farmer = Farmer.objects.create(
            phone_number="+2348012345678",
            name="Ibrahim",
            conversation_state=STATE_WELCOME
        )

    def test_farmer_creation(self):
        self.assertEqual(str(self.farmer), "Ibrahim (+2348012345678)")
        self.assertFalse(self.farmer.is_onboarded)

    def test_health_keyword_detection(self):
        self.assertTrue(looks_like_health_problem("My chickens are sick and dying with bloody diarrhea"))
        self.assertTrue(looks_like_health_problem("Kaji na suna zawo mai jini da tari"))
        self.assertFalse(looks_like_health_problem("Hello good morning"))

    def test_onboarding_flow(self):
        # 1. Welcome -> Ask Role
        res = process_message(self.farmer, "Hello")
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.conversation_state, STATE_ASK_ROLE)
        self.assertEqual(len(res), 2)

        # 2. Ask Role -> Ask Name
        res = process_message(self.farmer, "1")
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.role, "Farmer")
        self.assertEqual(self.farmer.conversation_state, STATE_ASK_NAME)

        # 3. Ask Name -> Ask Bird Type
        res = process_message(self.farmer, "Musa")
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.name, "Musa")

    def test_emergency_fast_track(self):
        # A new user reporting sick birds should bypass setup into conversation
        emergency_msg = "My broilers have bloody diarrhea and are dying fast"
        res = process_message(self.farmer, emergency_msg, ai_func=lambda f, c: ("Coccidiosis detected", True))
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.conversation_state, STATE_CONVERSATION)
        self.assertTrue(self.farmer.is_onboarded)
        # Verify a HealthCase was created
        self.assertEqual(HealthCase.objects.count(), 1)
        hc = HealthCase.objects.first()
        self.assertEqual(hc.farmer, self.farmer)
        self.assertEqual(hc.status, "Pending")


class AIEngineTests(TestCase):
    def setUp(self):
        self.engine = AgricareAIEngine()

    def test_language_detection(self):
        self.assertEqual(detect_language_heuristic("My chickens have green diarrhea"), "en")
        self.assertEqual(detect_language_heuristic("Kaji na suna zawo mai jini ko mutu"), "ha")
        self.assertEqual(detect_language_heuristic("Dem dey shit blood and no fit chop"), "pcm")
        self.assertEqual(detect_language_heuristic("Adìẹ mi n ya gbẹ́ ẹjẹ"), "yo")

    def test_offline_fallback_coccidiosis(self):
        res = self.engine.process("My broilers have bloody droppings and weight loss")
        self.assertIn(res["disease_id"], ["coccidiosis", "newcastle"])
        self.assertIn("Offline Mode", res["answer"])

    def test_offline_fallback_critical(self):
        res = self.engine.process("My chickens have twisted neck and are dying rapidly with green poop")
        self.assertEqual(res["urgency"], "RED")
        self.assertTrue(res["escalate"])


class WebhookViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_webhook_missing_data(self):
        response = self.client.post("/webhook/whatsapp/", data={})
        self.assertEqual(response.status_code, 400)

    def test_webhook_valid_ping(self):
        response = self.client.post("/webhook/whatsapp/", data={
            "Body": "Hello",
            "From": "whatsapp:+2348099999999",
            "ProfileName": "TestFarmer"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Farmer.objects.filter(phone_number="+2348099999999").exists())
        self.assertTrue(Conversation.objects.filter(sender_type="Farmer").exists())

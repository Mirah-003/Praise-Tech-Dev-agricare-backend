import os
import json
import re
import requests
from typing import List, Dict, Any, Optional

def get_system_prompt(knowledge: List[Dict[str, Any]]) -> str:
    kb_str = json.dumps(knowledge, ensure_ascii=False, indent=2)
    return (
        "You are Agricare AI, an expert poultry veterinarian for Nigerian smallholder farmers.\n"
        "Your job is to diagnose poultry diseases based on the farmer's query and provide advice using the verified veterinary knowledge base.\n\n"
        f"Here is the verified veterinary knowledge base containing poultry diseases:\n{kb_str}\n\n"
        "Instructions:\n"
        "1. Detect the farmer's language (English, Hausa, Yoruba, Igbo, Nigerian Pidgin).\n"
        "2. Act as a careful veterinary triage assistant. When a farmer first describes a problem, DO NOT immediately diagnose the disease. You MUST first ask 1 or 2 clarifying questions to gather more context (e.g., What is the age of the birds? How long have they been sick? Are there any other symptoms like diarrhea or coughing? Have they been vaccinated?).\n"
        "3. Only after the farmer has answered your clarifying questions and you have enough context should you match their symptoms to the most logical disease in the knowledge base and provide a final diagnosis.\n"
        "4. When asking questions, set `disease_id` and `disease_name` to null, and `urgency` to 'GREEN'.\n"
        "5. If a matching disease is confidently found (after gathering context), you MUST use the verified 'advice' and 'names' from the knowledge base in the farmer's language. If the language isn't explicitly supported, use English.\n"
        "6. Clinical Veterinary Guidance Standards:\n"
        "   - Medication & Dosing: Always advise farmers to check the product label on their specific packaging for the exact dosage/concentration. Medicated water must be the birds' ONLY drinking water during the full treatment period (usually 5-7 days).\n"
        "   - Drug Interactions: NEVER recommend Vitamin B or thiamine supplements during Amprolium treatment for Coccidiosis, as Amprolium works by blocking thiamine.\n"
        "   - Herbal Remedies Safety: Supportive herbs (Bitter Leaf, Aloe Vera, Garlic) must NEVER be mixed into medicated drinking water and must NEVER replace medical treatment during an active, acute/bloody outbreak. Use herbs only for prevention or recovery after pharmaceutical treatment.\n"
        "   - Litter & Sanitation: Always emphasize environmental hygiene (e.g. replacing damp litter for coccidiosis, improving ventilation).\n"
        "7. Keep your final answer text concise, conversational, polite, and suitable for a WhatsApp/USSD message. Do not overwhelm the user with long blocks of text.\n"
        "8. Triage the severity (only when providing a final diagnosis): \n"
        "   - Set urgency to 'RED' (and 'escalate' to true) if the confidently matched disease has severity 'CRITICAL' or if the user's message describes a fatal emergency (e.g. birds dying rapidly).\n"
        "   - Set urgency to 'ORANGE' if severity is 'HIGH'.\n"
        "   - Set urgency to 'YELLOW' if severity is 'MEDIUM'.\n"
        "   - Set urgency to 'GREEN' for general care / info or when asking clarifying questions.\n"
        "9. Provide your output in JSON format with these exact keys:\n"
        "   - 'language': The detected language code ('en', 'ha', 'yo', 'ig', 'pcm')\n"
        "   - 'disease_id': The ID of the confidently matched disease (or null if asking questions / none matched)\n"
        "   - 'disease_name': The name of the matched disease in the detected language (or null if asking questions)\n"
        "   - 'urgency': 'RED', 'ORANGE', 'YELLOW', or 'GREEN'\n"
        "   - 'escalate': true or false\n"
        "   - 'answer': Your helpful, conversational message to the farmer in their language. Either your clarifying questions OR your final diagnosis/advice.\n\n"
        "Always output raw JSON ONLY. Do not enclose in markdown code blocks."
    )

def detect_language_heuristic(text: str) -> str:
    text_lower = text.lower()
    lang_indicators = {
        "ha": ["kaji", "zawo", "mutu", "hanci", "tari", "kore", "fari", "baki", "ciki", "da", "sannu"],
        "yo": ["adìẹ", "arun", "gbẹ́", "ẹjẹ", "omi", "ewé", "orí", "enà", "ní", "tó", "pé"],
        "ig": ["ọkụkọ", "ọrịa", "nsị", "ọbara", "mmiri", "nri", "isi", "taa", "na", "ndụ", "ndewo"],
        "pcm": ["dey", "wey", "go", "fit", "chop", "sabi", "abeg", "shit", "blood", "body", "dem", "wetin"]
    }
    words = set(re.findall(r'\b\w+\b', text_lower))
    for lang, indicators in lang_indicators.items():
        if any(ind in words for ind in indicators):
            return lang
    return "en"

def run_fallback_matcher(text: str, knowledge: List[Dict[str, Any]]) -> Dict[str, Any]:
    text_lower = text.lower()
    lang = detect_language_heuristic(text)

    best_match = None
    max_matches = 0

    for disease in knowledge:
        matches = 0
        symptom_list = disease.get("symptoms", {}).get(lang, []) + disease.get("symptoms", {}).get("en", [])

        for symptom in symptom_list:
            if symptom.lower() in text_lower:
                matches += 2
            else:
                s_words = set(symptom.lower().split())
                q_words = set(text_lower.split())
                if len(q_words.intersection(s_words)) >= 2:
                    matches += 1

        for ew in disease.get("escalation_words", []):
            if ew.lower() in text_lower:
                matches += 3

        if matches > max_matches:
            max_matches = matches
            best_match = disease

    if max_matches < 2:
        best_match = None

    if best_match:
        name = best_match["names"].get(lang, best_match["names"].get("en", "Unknown Condition"))
        advice = best_match["advice"].get(lang, best_match["advice"].get("en", "Please consult a veterinarian."))
        severity = best_match.get("severity", "MEDIUM")

        urgency = "GREEN"
        escalate = False
        if severity == "CRITICAL":
            urgency = "RED"
            escalate = True
        elif severity == "HIGH":
            urgency = "ORANGE"

        templates = {
            "RED": "🚨 EMERGENCY (Offline Mode): ",
            "ORANGE": "⚠️ URGENT (Offline Mode): ",
            "YELLOW": "📋 INFO (Offline Mode): ",
            "GREEN": "✅ ADVICE (Offline Mode): "
        }
        prefix = templates.get(urgency, "📋 ")
        answer = f"{prefix}{name}\n\nAdvice: {advice}\n\n*Note: Running in offline backup mode.*"

        return {
            "language": lang,
            "disease_id": best_match["id"],
            "disease_name": name,
            "urgency": urgency,
            "escalate": escalate,
            "answer": answer
        }

    return {
        "language": lang,
        "disease_id": None,
        "disease_name": None,
        "urgency": "GREEN",
        "escalate": False,
        "answer": "I cannot identify the condition from my database. Please isolate the sick birds immediately, ensure access to fresh water/warmth, and contact a veterinarian."
    }

class AgricareAIEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")

        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.knowledge = json.load(f)
        else:
            self.knowledge = []

        self.system_prompt = get_system_prompt(self.knowledge)

    def process(self, text: str) -> Dict[str, Any]:
        if not self.api_key:
            res = run_fallback_matcher(text, self.knowledge)
            res["status"] = "fallback"
            return res

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": self.system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"].strip()

            # Strip markdown code fences if present
            if raw_json_str.startswith("```"):
                raw_json_str = re.sub(r'^```(?:json)?\s*', '', raw_json_str)
                raw_json_str = re.sub(r'\s*```$', '', raw_json_str)

            result = json.loads(raw_json_str)
            return {
                "language": result.get("language", "en"),
                "disease_id": result.get("disease_id"),
                "disease_name": result.get("disease_name"),
                "urgency": result.get("urgency", "GREEN"),
                "escalate": result.get("escalate", False),
                "answer": result.get("answer", "No answer provided."),
                "status": "success"
            }
        except Exception as e:
            print(f"Error with Gemini API: {e}. Using offline matcher.")
            res = run_fallback_matcher(text, self.knowledge)
            res["status"] = "fallback"
            return res

# Global instance
engine = AgricareAIEngine()

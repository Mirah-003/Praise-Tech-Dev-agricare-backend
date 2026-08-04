# Agricare AI Engine

**Submission for:** Africa Agility Cohort 9 Hackathon  
**Targeted SDG:** SDG 13 (Climate Action)  

## 🚀 Live Demos
- **Live Interactive USSD Simulator:** [https://agricare-django-portal.onrender.com/ussd/simulator/](https://agricare-django-portal.onrender.com/ussd/simulator/)
- **Live API Endpoint:** [https://agricare-django-portal.onrender.com](https://agricare-django-portal.onrender.com)

---

**AGRICARE AI** is an intelligent, multi-channel advisory AI Engine designed to help smallholder poultry farmers diagnose diseases instantly, manage climate-related heat stress, and get connected to veterinary help when needed. 

While originally prototyped as a standalone ML service, this repository represents the final, production-ready monolithic architecture. The **AI Engine** has been directly integrated into a robust delivery backend, prioritizing speed, offline reliability, and low-bandwidth access across rural African telecom networks without relying on fragile external LLM endpoints.

## 🧠 The AI Engine & Clinical Logic

The core of Agricare is its localized AI engine and conversation state machine (`agricore/state_machine.py`), which manages intelligent multi-turn diagnostics.

### 1. Offline Knowledge Base Integration
The engine relies on a rigorously audited, localized JSON knowledge base (`knowledge_base.json`) containing strict clinical rules for diagnosing diseases like Coccidiosis and Fowl Pox. This eliminates the hallucination risks associated with generative LLMs in medical contexts.

### 2. Urgent Triage & Escalation (Red/Yellow Flags)
If the AI engine detects critical keywords (e.g., *Newcastle*, *Acute Mortality*), it instantly bypasses the standard diagnostic conversation, triggers a `HealthCase` escalation for human veterinary intervention, and logs a high severity score (8.0 - 10.0).

### 3. Clinical Safety & SDG-13 Enforcement
- **Climate Action (SDG 13):** The engine actively injects actionable Heat Stress Management protocols (cooling, ventilation, feeding schedule adjustments) into advice to combat climate-induced flock mortality.
- **Strict Contraindications:** The logic safely partitions traditional herbal remedies (Aloe Vera, Bitter Leaf) from active pharmaceutical treatments, strictly prohibiting the mixing of remedies (e.g., blocking Vitamin B1 supplements during Amprolium administration).

## 📡 Omnichannel Delivery System

To ensure no farmer is left behind due to the digital divide, the AI Engine delivers its advice through a unified backend routing system (`agricore/views.py`):

- **GSM USSD Gateway (`/webhook/ussd/`):** Implements the official Africa's Talking GSM USSD protocol. Farmers can access the AI Engine on 2G feature phones without internet using standard `CON` and `END` session states.
- **Twilio WhatsApp Webhook (`/webhook/whatsapp/`):** Processes rich text interactions and automatically registers farmers.
- **Twilio SMS Webhook (`/webhook/sms/`):** Handles 2-way SMS routing for users without WhatsApp.
- **Interactive USSD Simulator (`/ussd/simulator/`):** A built-in web simulator allowing users (and hackathon judges!) to dial `*384*400#` directly in the browser to experience the 2G interface without a physical African SIM card.

## 🛠️ Project Structure

- `agricore/`: The heart of the platform. Contains the AI Engine, offline fallback logic, unified state machine, database models (`Farmer`, `Conversation`, `HealthCase`), and webhook views.
- `core/`: Main Django settings, middleware, and base URL routes.
- `requirements.txt`: Cleaned dependencies, specifically targeting Django, Twilio, and Render deployment requirements.
- `render.yaml`: Infrastructure-as-Code configuration for automated seamless deployment to Render.

## 💻 Local Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: .\venv\Scripts\Activate.ps1
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root folder alongside `manage.py`:
   ```ini
   AI_API_KEY=your_actual_ai_api_key
   SECRET_KEY=your_django_secret_key
   ```

4. **Run Migrations & Tests:**
   ```bash
   python manage.py migrate
   python manage.py test  # Runs the 14 comprehensive unit tests verifying the AI engine and routing
   ```

5. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```

## ☁️ Production Deployment (Render)

This repository is pre-configured to deploy seamlessly on Render.com using the included `render.yaml`. 
- **SQLite Database Warning:** The platform currently utilizes SQLite for rapid prototyping. For production at scale, Render allows easy attachment of a managed PostgreSQL instance by updating the `DATABASES` configuration.

## 👥 Credits and Contributions

This project represents a collaborative merger between two original architectures to create a production-ready monolith:

- **Agricare AI Engine & Integrations (Hafsat Abdulhamid):** Full credit for the core AI logic, clinical knowledge base, system integrations, and final platform connections. Specific, sole contributions include:
  - Designing and implementing the **Offline Clinical Knowledge Base**, **AI Fallback logic**, and **Urgent Triage**.
  - Developing the **Conversation State Machine** for multi-turn diagnostic advisory.
  - Enforcing the **SDG 13 (Climate Action)** heat stress protocols and **Clinical Safety Logic** (drug contraindications).
  - Implementing the **GSM USSD Gateway** and **Interactive Web Simulator**.
  - Integrating the **Twilio SMS and WhatsApp Webhooks**.
  - Migrating the original `agricare-ai-engine` into this unified Django application.

- **Backend Architecture (Praise-Tech-Dev / [Ailee12/AGRICARE](https://github.com/Ailee12/AGRICARE)):** Full credit for the core foundational Django backend architecture, initial model definitions, database configuration, and basic routing goes to the original development team.

# Agricare AI Backend (Final Audit & Documentation)

**Submission for:** Africa Agility Cohort 9 Hackathon  
**Targeted SDG:** SDG 13 (Climate Action)  

## 🚀 Live Demos
- **Live Interactive USSD Simulator:** [https://agricare-django-portal.onrender.com/ussd/simulator/](https://agricare-django-portal.onrender.com/ussd/simulator/)
- **Live API Endpoint:** [https://agricare-django-portal.onrender.com](https://agricare-django-portal.onrender.com)

---

This is the production-ready backend system for **Agricare AI**, an intelligent multi-channel advisory platform designed to help smallholder poultry farmers diagnose diseases instantly, manage climate-related heat stress, and get connected to veterinary help when needed.

This repository represents the final, consolidated backend structure optimized for deployment on **Render**, completely independent of legacy endpoints like Railway or external HuggingFace dependencies.

## Architecture Audit & Flow

The core system handles asynchronous requests through a centralized state machine across three main communication channels: WhatsApp, SMS, and GSM USSD.

### 1. Unified Message Routing (`agricore/views.py`)
- **Twilio WhatsApp Webhook (`/webhook/whatsapp/`)**: Processes incoming WhatsApp messages via Twilio, automatically registering new farmers using their WhatsApp profile names.
- **Twilio SMS Webhook (`/webhook/sms/`)**: Handles 2-way SMS routing for farmers using 2G feature phones without WhatsApp.
- **GSM USSD Gateway (`/webhook/ussd/` & `/ussd/`)**: Implements the official Africa's Talking / Telco GSM USSD protocol using strict `CON` (Continue) and `END` (Terminate) session states.

### 2. State Machine & Fallback AI (`agricore/state_machine.py`)
All incoming requests are passed to `process_message()`, which manages context across multi-turn conversations:
- **Offline Knowledge Base Integration**: Relies on a rigorously audited, localized JSON knowledge base (`knowledge_base.json`) containing clinical rules, eliminating dependence on fragile external LLM endpoints for primary triage.
- **Urgent Triage (Red/Yellow Flags)**: If the system detects critical keywords (e.g., Newcastle, Coccidiosis, Acute Mortality), it bypasses normal conversation, instantly triggers a `HealthCase` escalation for human vets, and logs a high severity score (8.0 - 10.0).

### 3. Clinical Safety & SDG-13 Enforcement
- **Strict Dosing & Contraindications**: The system strictly separates herbal remedies (Aloe Vera, Bitter Leaf) from active pharmaceutical treatments (e.g., Amprolium). It explicitly prohibits mixing herbal extracts with synthetic drugs like Amprolium (which blocks Vitamin B1).
- **Climate Action (SDG 13)**: Integrates actionable Heat Stress Management protocols (cooling, ventilation, feeding schedule adjustments) to combat climate-induced flock mortality.

### 4. Interactive USSD Simulator (`/ussd/simulator/`)
To facilitate testing and hackathon judging without requiring a physical Africa's Talking integration or African SIM card, a fully interactive **Web USSD Simulator** is built into the Django application. Navigating to this endpoint allows users to dial `*384*400#` directly in their browser.

## Project Structure

- `core/`: Main project settings, middleware, and base URL routes.
- `agricore/`: Core application logic containing database models (`Farmer`, `Conversation`, `HealthCase`), unified state machine, the offline fallback AI engine, and webhook views.
- `requirements.txt`: Cleaned dependencies, specifically targeting Django, Twilio, and Render deployment requirements (Legacy HuggingFace/Transformers dependencies have been purged).
- `render.yaml`: Infrastructure-as-Code configuration for automated seamless deployment to Render.

## Local Setup Instructions

To run this backend on your local machine:

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
   python manage.py test  # Runs the 14 comprehensive unit tests
   ```

5. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```

## Production Deployment (Render)

This repository is pre-configured to deploy seamlessly on Render.com using the included `render.yaml`. 
- No Docker configuration is necessary for the web service.
- **SQLite Database Warning:** The platform currently utilizes SQLite for rapid prototyping and hackathon purposes. For production at scale, Render allows easy attachment of a managed PostgreSQL instance by updating the `DATABASES` configuration in `core/settings.py`.

## Credits and Contributions

This project represents a collaborative merger between two original architectures:

- **Backend Architecture (Praise-Tech-Dev / Teammates):** Full credit for the core foundational Django backend architecture, initial model definitions, database configuration, and basic routing goes to the original development team.
- **Agricare AI Engine & Integrations (Hafsat Abdulhamid):** Full credit for the AI logic, clinical knowledge base, system integrations, and final platform connections. Specific, sole contributions include:
  - Migrating and connecting the original `agricare-ai-engine` into the unified Django application.
  - Designing and implementing the **Offline Clinical Knowledge Base** and AI Fallback logic.
  - Developing the **Conversation State Machine** for multi-turn advisory.
  - Implementing the **GSM USSD Gateway** and **Interactive Web Simulator**.
  - Integrating the **Twilio SMS and WhatsApp Webhooks**.
  - Enforcing the **SDG 13 (Climate Action)** heat stress protocols and **Clinical Safety Logic** (contraindications).

---

*Note: This repository has been audited and cleaned to remove deprecated Railway references and heavy NLP endpoints, prioritizing speed, reliability, and low-bandwidth access across rural African telecom networks.*

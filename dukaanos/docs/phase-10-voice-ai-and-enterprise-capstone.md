# Phase 10: Indic Voice AI Copilot & Multi-Store Enterprise Capstone (बोलती दुकान और मल्टी-स्टोर एंटरप्राइज)

## 1. Executive Summary & Capstone Vision

Phase 10 is the pinnacle of the **DukaanOS** AI engineering journey, delivering two capstone enterprise capabilities:

1. **Indic Voice AI Copilot ("बोलती दुकान" - The Talking Store):**
   - During evening rush hours (7 PM – 10 PM), Indian Kirana shopkeepers have their hands physically occupied measuring grains, packing carry bags, and collecting cash. They cannot type on keyboards or tap touchscreen POS buttons.
   - The Indic Voice AI enables **hands-free voice-driven store operations** across **Hindi (हिंदी)**, **Hinglish**, **Bengali**, and **English**.
   - Handles end-to-end voice checkout:
     *"Bhaiya, do bori Aashirvaad Atta aur teen bottle Fortune Tel ka bill banao"* &rarr; Automated speech-to-intent entity slot filling &rarr; Atomic POS sale commit &rarr; Audio voice confirmation read-out.
2. **Multi-Store Enterprise Network & Cross-Store Stock Balancing:**
   - Multi-outlet enterprise management for retail owners operating 2 to 10+ branch stores.
   - Consolidated P&L, real-time cross-store stockout visibility, and **inter-store stock rebalancing recommendations** (*"Store A is stocked out of Atta, but Store B has 45 excess bags. Transfer 20 bags to avoid ₹4,900 in unfulfilled sales"*).

---

## 2. Technical Architecture & Component Flow

```
                      +-----------------------------------------------------------+
                      |         HANDS-FREE PHYSICAL SHOP ENVIRONMENT              |
                      |  * Storekeeper speaks into smartphone / mic                |
                      |  * Ambient background shop noise (Traffic, Mandi chatter) |
                      +-----------------------------------------------------------+
                                                    |
                                    [Raw Audio Stream / Voice Utterance]
                                                    v
                      +-----------------------------------------------------------+
                      |       LAYER 1: INDIC VOICE PIPELINE (SPEECH-TO-INTENT)    |
                      |  * Acoustic Preprocessing & Noise Suppression             |
                      |  * Phoneme Tokenizer (Devanagari + Latin transliteration) |
                      |  * Slot Filling (Entity Extraction: Item, Qty, Unit, Rate)|
                      +-----------------------------------------------------------+
                                                    |
                                    [Structured Voice Command Payload]
                                                    v
                      +-----------------------------------------------------------+
                      |       LAYER 2: DETERMINISTIC ACTION ENGINE                |
                      |  * Voice POS Billing ("Bill बनाओ")                        |
                      |  * Voice Stock Lookup ("Atta कितना बचा है?")              |
                      |  * Voice PO Generation ("10 पेटी Parle-G मंगवाओ")         |
                      |  * Generates Synthesized Text-to-Speech (TTS) Confirmation|
                      +-----------------------------------------------------------+
                                                    |
                                                    v
                      +-----------------------------------------------------------+
                      |       LAYER 3: MULTI-STORE ENTERPRISE ORCHESTRATION       |
                      |  * Cross-store inventory pooling (Stores A, B, C)         |
                      |  * Inter-Store Stock Transfer Rebalancer                  |
                      |  * Consolidated Multi-Outlet Financial Dashboard          |
                      +-----------------------------------------------------------+
```

---

## 3. Engineering Specifications

### 3.1 Indic Voice Slot Filling & Entity Resolution
- **Input Utterance:** *"Do bori Aashirvaad Atta aur teen bottle Fortune Tel bill banao"*
- **Entity Extraction Pipeline:**
  ```json
  {
    "detected_intent": "VOICE_POS_BILLING",
    "detected_language": "hinglish",
    "confidence": 0.94,
    "entities": [
      {
        "raw_item": "Aashirvaad Atta",
        "matched_sku": "STP-001",
        "quantity": 2,
        "unit": "bori"
      },
      {
        "raw_item": "Fortune Tel",
        "matched_sku": "OIL-003",
        "quantity": 3,
        "unit": "bottle"
      }
    ],
    "action": "COMMIT_POS_CHECKOUT",
    "voice_feedback_text": "Theek hai Ramesh Ji! 2 bori Aashirvaad Atta aur 3 bottle Fortune Tel ka bill bana diya hai. Total hua ₹955.00."
  }
  ```

### 3.2 Inter-Store Inventory Rebalancing Algorithm
When Store $A$ is below its Safety Stock ($S_A < \text{SS}_A$) and Store $B$ has excess stock ($S_B > \text{ROP}_B + \text{ExcessThreshold}$):
$$\text{TransferQty} = \min\left(\text{SS}_A - S_A, S_B - \text{ROP}_B\right)$$
- Eliminates emergency wholesale procurement costs.
- Prevents customer cart abandonment at Store $A$ without purchasing new inventory.

---

## 4. Verification & Testing Requirements
1. `test_indic_voice_slot_extraction`: Verifies entity extraction (item, quantity, unit) from spoken Hindi/Hinglish text.
2. `test_voice_pos_checkout_execution`: Verifies that a voice command automatically commits a sale and deducts the inventory ledger.
3. `test_cross_store_rebalancing`: Confirms inter-store excess detection and transfer recommendation math.
4. `test_consolidated_enterprise_rollup`: Verifies multi-store consolidated revenue, margin, and stock metrics.


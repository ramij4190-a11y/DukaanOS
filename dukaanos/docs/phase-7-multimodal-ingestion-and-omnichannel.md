# Phase 7: Multimodal Ingestion, Omnichannel WhatsApp & Interactive Store UI (मल्टीमॉडल इनजेशन और डिजिटल दुकान)

## 1. Executive Overview & FDE Scope
In real Indian Kirana operations, shopkeepers do not type structured SQL queries or upload clean CSVs. Their primary operational inputs are:
1. **Handwritten / printed paper invoices (Mandi Parchis):** Received from wholesale distributors with non-standard item abbreviations (e.g., *"Aashir Atta 5k"*, *"Fort Sun 1L"*).
2. **WhatsApp conversations:** Everyday ordering, price negotiation, and delivery updates with Mandi dealers happen on WhatsApp.
3. **Voice instructions in native dialect:** During rush hours, shopkeepers prefer speaking (*"5 peti Parle-G likh lo"*) rather than typing.

Phase 7 bridges the gap between DukaanOS's analytical backend and the chaotic physical reality of Indian retail by building a complete **Multimodal Data Ingestion & Omnichannel Bridge**.

---

## 2. Technical Architecture & Component Flow

```
                      +-----------------------------------------------------+
                      |             PHYSICAL STORE INPUT CHANNELS           |
                      |  * Paper Invoices (Mandi Parchis)                   |
                      |  * WhatsApp Messages & Voice Audio                  |
                      |  * Barcode Scanner / POS Touchscreen                |
                      +-----------------------------------------------------+
                                                 |
                                                 v
                      +-----------------------------------------------------+
                      |           LAYER 1: MULTIMODAL INGESTION HUB         |
                      |                                                     |
                      |  1. OCR Engine & Text Normalizer                   |
                      |     - Extracts line items, rates, quantities        |
                      |                                                     |
                      |  2. Fuzzy Catalog Matcher (Levenshtein Distance)    |
                      |     - Maps raw text -> Canonical 100-SKU catalog    |
                      |     - Scored confidence: [0.0, 1.0]                 |
                      |                                                     |
                      |  3. Human-in-the-Loop Confidence Gate               |
                      |     - High confidence (>=0.85): Auto-staged         |
                      |     - Low confidence (<0.85): Flagged for review    |
                      +-----------------------------------------------------+
                                                 |
                                                 v
                      +-----------------------------------------------------+
                      |           LAYER 2: ACTION & LEDGER DISPATCH         |
                      |  * Owner Confirmation ("Approve Bill")             |
                      |  * Atomic Ledger Posting (PURCHASE event)           |
                      |  * Supplier Outbound PO via WhatsApp Webhook        |
                      +-----------------------------------------------------+
                                                 |
                                                 v
                      +-----------------------------------------------------+
                      |           LAYER 3: INTERACTIVE SHOP UI (WEB/PWA)    |
                      |  * Live Morning AI Brief                            |
                      |  * Real-Time POS Counter Billing with Idempotency    |
                      |  * Invoice Upload & Visual Line-Item Review         |
                      |  * Multilingual Voice/Text Copilot                  |
                      +-----------------------------------------------------+
```

---

## 3. Detailed Engineering Specifications

### 3.1 Wholesale Invoice OCR & Fuzzy Catalog Matcher
- **Problem:** A distributor invoice reads `"Aashirvad Atta 5kg pkts x 20 @ 225"`. The system catalog has SKU `STP-001: Aashirvaad Superior MP Atta 5kg`.
- **Matching Algorithm:**
  1. Token normalization (lowercase, punctuation stripping, unit standardization: `kg`, `gm`, `ltr`, `pkt`).
  2. Composite string similarity:
     $$\text{Score} = 0.6 \cdot \text{TokenSetRatio}(S_{\text{raw}}, S_{\text{catalog}}) + 0.4 \cdot \text{CategoryPrior}$$
  3. Safety Thresholds:
     - **$\ge 0.85$:** Confirmed match.
     - **$0.60 \le \text{Score} < 0.85$:** Flagged for owner 1-click verification.
     - **$< 0.60$:** Treated as a potential New SKU or unmapped item.

### 3.2 Human-in-the-Loop Purchase Ingestion Workflow
Every purchase invoice creates a draft staging payload:
```json
{
  "invoice_number": "INV-MANDI-8841",
  "supplier_name": "ITC North Wholesale Mandi",
  "total_amount": 13275.0,
  "confidence_score": 0.92,
  "items": [
    {
      "raw_text": "Aashir Atta 5kg",
      "matched_sku": "STP-001",
      "matched_name": "Aashirvaad Superior MP Atta 5kg",
      "confidence": 0.94,
      "quantity": 35,
      "unit_cost": 225.0,
      "status": "CONFIRMED"
    }
  ]
}
```
Upon owner approval, stock is automatically committed to the **immutable inventory ledger** (`event_type="PURCHASE"`), immediately updating the running balance.

### 3.3 Omnichannel WhatsApp Mandi Dispatcher
- Converts approved PO drafts into standard WhatsApp URL triggers (`https://wa.me/<phone>?text=<encoded_msg>`).
- Supports multilingual message templates:
  - **Hindi (हिंदी):** *"नमस्ते भाईजी, श्री गणेश किराना से ऑर्डर: आशीर्वाद आटा 5kg (35 बोरी), फॉर्च्यून तेल 1L (40 बोतल)..."*
  - **Hinglish:** *"Bhaiji, please dispatch tomorrow: Aashirvaad Atta 5kg (35 pcs)..."*
  - **English:** *"Purchase Order PO-000101 from Shree Ganesh Kirana..."*

### 3.4 Interactive Store Dashboard & PWA
- Served directly by FastAPI at `http://localhost:8000/` and `/dashboard`.
- Single-page application built with HTML5, Tailwind CSS, and Vanilla JavaScript (leveraging frontend web performance).
- Real-time interaction with the `/api/v1` backend endpoints.

---

## 4. Verification & Testing Requirements
1. `test_invoice_fuzzy_matcher`: Confirms fuzzy match accuracy on noisy Mandi invoice text strings.
2. `test_invoice_confidence_thresholding`: Verifies high-confidence auto-mapping and low-confidence human review flagging.
3. `test_invoice_ledger_commit`: Verifies that approving an invoice posts atomic `PURCHASE` ledger movements and increments stock.
4. `test_whatsapp_po_formatter`: Verifies localized WhatsApp message serialization across Hindi, Hinglish, and English.
5. `test_frontend_routes`: Verifies that the dashboard and static assets are served seamlessly with HTTP 200.


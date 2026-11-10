# Phase 8: Offline-First Edge Sync & AI Khata (Credit Risk) Intelligence (ऑफलाइन सिंक और स्मार्ट बही-खाता)

## 1. Executive Summary & FDE Context
In the Indian retail landscape, two physical realities dictate whether retail software succeeds or fails in the field:
1. **Network Fragility (The Offline Dilemma):** Kirana stores located in basements, dense Mandis, or tier-2/3 towns experience frequent power cuts and broadband dropouts. If an POS counter freezes because an API endpoint is unreachable, the shopkeeper will abandon the software immediately.
2. **The Udhar Economy (Customer Credit):** Between **40% and 65%** of daily Kirana sales are conducted on credit (*Udhar / Khatabook*). Traditional POS tools fail because they assume instant cash or card settlement. Small retailers require an intelligent ledger that tracks credit balances, assesses default risk, and automates payment recovery without damaging customer relationships.

Phase 8 elevates DukaanOS with two mission-critical enterprise systems:
- **Offline-First Edge Sync Engine:** Instant local checkout with asynchronous, conflict-free queue reconciliation when connectivity resumes.
- **AI Khata & Credit Intelligence Engine:** Customer credit ledger, dynamic repayment risk scoring, and automated polite WhatsApp UPI payment reminders.

---

## 2. Technical Architecture & Component Flow

```
                      +-----------------------------------------------------------+
                      |               LOCAL STORE EDGE / CLIENT (POS)             |
                      |  * Intermittent / Flaky 4G Connection                      |
                      |  * Local SQLite / IndexedDB Storage                       |
                      +-----------------------------------------------------------+
                                   |                                     |
                         [Online: Direct API]                  [Offline: Queued]
                                   v                                     v
                      +-----------------------+               +-----------------------+
                      |   Cloud REST API      |               |  Local Sync Queue     |
                      |   (/api/v1/sales)     |               |  (Replay buffer)      |
                      +-----------------------+               +-----------------------+
                                   ^                                     |
                                   |         [Internet Restored]         |
                                   +-------------------------------------+
                                            Batch Reconcile & Dedupe
                                                       |
                                                       v
                      +-----------------------------------------------------------+
                      |        CENTRAL DUKAANOS MULTI-TENANT SERVER               |
                      |                                                           |
                      |  1. Conflict-Free Reconciler                              |
                      |     - Idempotency verification prevents double charging   |
                      |     - Immutable ledger timestamp ordering                 |
                      |                                                           |
                      |  2. AI Khata & Credit Intelligence Engine                 |
                      |     - Customer Credit Ledger (+/- Udhar balance)          |
                      |     - Default Risk Scoring (Repayment velocity, DPD)      |
                      |     - WhatsApp UPI Deep-Link Collection Generator         |
                      +-----------------------------------------------------------+
```

---

## 3. Engineering Specifications

### 3.1 Offline-First Edge Synchronization
- **Optimistic Local Execution:** Counter sales checkout executes immediately on the local edge client, decrementing the local stock cache and buffering the transaction payload in an append-only sync queue.
- **Queue Payload Schema:**
  ```json
  {
    "sync_id": "SYNC-UUID-9812",
    "store_id": "STORE-001",
    "idempotency_key": "IDEMP-OFFLINE-781293",
    "offline_timestamp": "2026-11-10T14:30:00Z",
    "payload": {
      "payment_method": "KHATA",
      "customer_id": 101,
      "items": [{"product_id": 1, "quantity": 2}]
    }
  }
  ```
- **Reconciliation Engine:**
  - Server accepts batches of offline transactions via `/api/v1/sync/batch`.
  - Verifies idempotency keys against the central database to guarantee zero double deductions.
  - Commits inventory ledger events with original transaction timestamps.

### 3.2 AI Khata (Credit Ledger) & Default Risk Scoring
- **Customer Entity:** Tracks credit limit, current outstanding balance, total lifetime purchases, and days-past-due (DPD).
- **Credit Risk Model:**
  $$\text{Risk Score} = 0.4 \cdot \left(\frac{\text{Current Balance}}{\text{Credit Limit}}\right) + 0.4 \cdot \left(\frac{\text{Days Overdue}}{30}\right) - 0.2 \cdot \text{Repayment Velocity}$$
  - **LOW RISK ($< 0.40$):** Healthy customer, automatic credit extension approved.
  - **MODERATE RISK ($0.40 - 0.75$):** Soft credit alert, gentle WhatsApp reminder.
  - **HIGH RISK ($> 0.75$):** Credit freeze recommended, immediate settlement required.
- **Polite Recovery WhatsApp Generator:**
  - Non-intrusive, culturally sensitive reminder messages in Hindi, Hinglish, and English with dynamic UPI QR payment links (`upi://pay?pa=...`).

---

## 4. Verification & Testing Requirements
1. `test_offline_queue_serialization`: Verifies queue buffering and payload integrity.
2. `test_batch_sync_deduplication`: Confirms that syncing the same offline batch twice produces zero duplicated transactions or ledger drifts.
3. `test_khata_credit_ledger_movement`: Verifies debiting customer credit on sale and crediting on repayment.
4. `test_credit_risk_scoring`: Confirms risk classification across low, medium, and high credit profiles.
5. `test_upi_recovery_message_generation`: Verifies polite localized WhatsApp message formatting with valid UPI payment deep links.

# Phase 11 Visual Architecture Guide
### The Self-Learning Kirana Brain & Autonomous Store Operations

---

## 1. End-to-End Autonomous Learning Cycle

```mermaid
sequenceDiagram
    autonumber
    actor Shopkeeper as Shopkeeper (Ramesh Ji)
    participant Mic as Voice Recognition (Browser)
    participant VoiceEngine as Indic Voice NLP Engine
    participant Ledger as Immutable Ledger
    participant ML as Autonomous ML Brain
    participant AutoPilot as Auto-Pilot Decision Engine
    participant Supplier as Mandi Supplier WhatsApp

    Shopkeeper->>Mic: "Aashirvaad Atta 20 packet naya aaya"
    Mic->>VoiceEngine: Streams spoken Hindi transcript
    VoiceEngine->>Ledger: Atomic Ledger Mutation (+20 units)
    Ledger-->>ML: Event Hook (Event=PURCHASE, SKU=STP-001, Qty=+20)
    
    activate ML
    ML->>ML: Update EWMA Demand Velocity (mu_k)
    ML->>ML: Update Variance (sigma^2_k)
    ML->>ML: Recalculate Dynamic ROP & Days to Depletion
    ML-->>AutoPilot: Updated Store State & Forecasts
    deactivate ML

    activate AutoPilot
    AutoPilot->>AutoPilot: Check Safety Margins (Stock vs ROP)
    alt Stock <= Lead Time Buffer
        AutoPilot->>AutoPilot: Auto-Draft Purchase Order
        AutoPilot-->>Shopkeeper: Speaks audible alert & WhatsApp draft
    else Stock Healthy
        AutoPilot-->>Shopkeeper: Audio Voice Confirmation ("Stock updated to 112")
    end
    deactivate AutoPilot
```

---

## 2. Continual Learning Architecture (Dual Engine)

```mermaid
flowchart TD
    subgraph Inputs["Multi-Modal Store Signals"]
        A1["🎙️ Voice Commands (Arrivals, Wastage, Audits)"]
        A2["🛒 POS Billing Counter Sales"]
        A3["📄 Mandi OCR Wholesale Invoices"]
    end

    subgraph CoreEngine["The Self-Learning Brain"]
        B1["Incremental EWMA Burn-Rate Calculator"]
        B2["Dynamic Lead-Time Learner"]
        B3["Depletion Horizon Forecaster"]
        B4["Customer Khata Velocity Tracker"]
    end

    subgraph AutoActions["Autonomous Self-Driving Actions"]
        C1["📦 Auto-Draft Restock POs Before Stockout"]
        C2["⚠️ Supplier Overcharging & Quality Alerts"]
        C3["💰 Slow-Moving Batch Auto-Markdown Suggestions"]
        C4["📱 1-Tap UPI WhatsApp Payment Reminders"]
    end

    Inputs --> CoreEngine
    CoreEngine --> AutoActions
```

---

## 3. Autonomous State Machine

```mermaid
stateDiagram-v2
    [*] --> IdleMonitoring: Background Watchdog Active
    IdleMonitoring --> SignalIngested: Voice Inward / POS Sale / Audit
    SignalIngested --> OnlineLearning: Increment EWMA Velocity
    OnlineLearning --> RiskAssessment: Evaluate Stockout & Spoilage Horizons
    
    state RiskAssessment {
        [*] --> CheckStockout
        CheckStockout --> Starved: DaysToDepletion <= LeadTime
        CheckStockout --> Healthy: DaysToDepletion > LeadTime
        CheckStockout --> Overstocked: Stock > 3x ROP
    }

    Starved --> AutoDraftPO: Trigger Autonomous PO
    Overstocked --> AutoPromotion: Trigger Clearance Markdown
    Healthy --> IdleMonitoring: Log Normal State
    AutoDraftPO --> IdleMonitoring: Notify Storekeeper
    AutoPromotion --> IdleMonitoring: Notify Storekeeper
```

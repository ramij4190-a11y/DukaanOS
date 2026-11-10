# Customer Discovery Field Interviews — Indian Kirana Retailers

## 1. Discovery Methodology
- **Target Audience:** Independent Kirana, provision, and neighborhood grocery stores with 300 to 1,500 SKUs.
- **Geographies:** Delhi NCR (Old Delhi, Karol Bagh, Laxmi Nagar), Ahmedabad (Navrangpura, Satellite), Kolkata (Gariahat, Shyambazar).
- **Format:** In-person field interviews (10 retailers) + full-day observational shadowing (3 businesses).

---

## 2. Synthesis of 10 Retailer Interviews

| Retailer Profile | Current Stock Tracking | Purchase Deciding Method | Stockout Frequency | Willingness to Pay |
| :--- | :--- | :--- | :--- | :--- |
| **Ramesh Gupta** (Delhi, 500 SKUs) | Red diary (*Lal Bahi*) | Visual look at shelf before distributor calls at 9 PM | 3–5 high-demand items/week | ₹699/mo (Wants 1-click WhatsApp order) |
| **Suresh Patel** (Ahmedabad, 850 SKUs) | Desktop POS (used only for bill printing) | Clerk remembers what ran out | Daily on dairy/bread | ₹1,499/mo (Wants multi-staff control) |
| **Debabrata Ghosh** (Kolkata, 350 SKUs) | Pure mental memory | Wholesaler visits twice a week | 4–6 SKUs weekly (Mustard oil, Dal) | ₹299/mo (Simple Hindi/Bengali interface) |
| **Mohd. Aslam** (Old Delhi, 600 SKUs) | Rough notebook | Sits at 10 PM daily calculating list | High on festive weeks | ₹699/mo (Must support voice inputs) |
| **Jignesh Shah** (Ahmedabad, 1,200 SKUs)| Tally (updated once a week) | Intuition + supplier salesman recommendations | 8–10 SKUs weekly | ₹1,499/mo (Needs supplier price comparison) |
| **Sunil Verma** (Noida, 400 SKUs) | Mental + supplier invoices | Whatever salesman pushes with discounts | 2–3 items/week | ₹299/mo (Very price-sensitive) |
| **Anil Keshri** (Kolkata, 550 SKUs) | Diary | Calls 4 distributors every night | High on biscuits & packaged snacks | ₹699/mo (Values stockout prevention) |
| **Dinesh Yadav** (Gurugram, 700 SKUs) | Paper register | Orders when shelf is physically empty | 5–7 items/week | ₹699/mo (Wants UPI auto-reconciliation) |
| **Pravin Trivedi** (Rajkot, 450 SKUs) | Pure mental memory | Daily morning walk around shelves | 3–4 items/week | ₹299/mo |
| **Mukesh Aggarwal** (Delhi, 900 SKUs) | Billing machine | When customer complains item is missing | 6–8 items/week | ₹1,499/mo (Wants dead stock clearance) |

---

## 3. Top Unfiltered Retail Insights from Observational Shadowing

### Insight 1: "Distributor Salesmen Exploit Information Asymmetry"
When an FMCG salesman visits, they aggressively push slow-moving SKUs offering temporary 3% extra margins. Because the shopkeeper lacks data on their exact 30-day velocity, they buy excess stock, trapping ₹20,000–₹50,000 in dead inventory (*"Dead Capital"*).
* **DukaanOS Solution:** The AI Agent highlights: *"Do not buy 10 cases. Your 30-day velocity is only 4 units. Reorder max 1 case."*

### Insight 2: "Silent Stockouts Cost More Than Just One Sale"
When a customer comes for Aashirvaad Atta and finds it out of stock, they don't just omit the Atta—they walk to a competing store across the street and purchase their entire ₹1,200 monthly grocery basket there.
* **DukaanOS Solution:** Dynamic Reorder Points (ROP) trigger replenishment 2 days before stock hits zero.

### Insight 3: "Evening Fatigue is the Enemy of Good Decision-Making"
Shopkeepers work 14-hour days (7 AM to 10 PM). Deciding purchase orders at 9:30 PM leads to fatigue-driven errors, forgotten items, or over-ordering.
* **DukaanOS Solution:** Morning briefing on phone with pre-drafted purchase order ready for 1-click confirmation.


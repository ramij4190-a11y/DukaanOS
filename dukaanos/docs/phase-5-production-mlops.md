# Phase 5: Production ML Systems, MLOps & Observability

## 1. Executive Summary & Goals
- **Role Transition:** From Prototype AI Engineer to Production Systems / MLOps Engineer
- **Core Mission:** Ensure that ML models, automated pipelines, and agent tools are automated, observable, containerized, and resilient against data drift and operational failures.
- **Timeframe:** Months 5–6
- **Tech Stack:** Docker, GitHub Actions CI/CD, MLflow, OpenTelemetry, Prometheus/Grafana or cloud monitoring.

---

## 2. Production Architecture & Drift Monitoring

```
[Store Daily Sales] ---> [Automated Ingestion Pipeline]
                                  │
                                  ▼
                     [Data Freshness & Integrity Check]
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
            [Prediction Service]        [Drift Detector]
             (Cached in Redis)           - Data Drift (KS-test / PSI)
                     │                   - Model Drift (WAPE degradation)
                     ▼                         │
            [Retailer Dashboard]               ▼
                                        [Alert / Retrain Trigger]
```

### Metrics Monitored in Production:
1. **Model Performance Drift:** Rolling 14-day WAPE compared against baseline. If WAPE exceeds threshold (e.g. > 35%), trigger automated backtest & retraining alert.
2. **Feature Drift (PSI - Population Stability Index):** Detecting significant changes in consumer purchasing behaviors (e.g. sudden inflation spikes or new competitors).
3. **Agent Reliability:** Tool execution latency, function call success rate, hallucination check, and fallback invocation rate.
4. **API Latency & SLA:** 95th percentile response times under 200ms for point-of-sale transactions.


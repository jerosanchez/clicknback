# AI & Augmented Features

This document identifies opportunities to incorporate AI and retrieval-augmented generation (RAG) features into ClickNBack. The goal is to use this project as a practice ground for modern AI techniques that are increasingly relevant in production systems. Each item is scoped to be independently implementable and approachable for learning and experimentation.

---

## 1. Fraud Scoring

**Where:** Purchase ingestion, admin review dashboard.

**Why here:** Adds a layer of automated fraud risk scoring, surfacing suspicious purchases for admin review and demonstrating AI integration in a financial context.

**General approach:** Implement a rule-based scorer for basic heuristics (e.g., unusual amount, new merchant, odd hour). When a score exceeds a threshold, call an LLM API for anomaly explanation and store the result for admin review. Flagged purchases require manual approval or rejection.

**Benefits:**

- Demonstrates AI as a decision support tool.
- Adds a new entity state and admin workflow.
- Practical prompt engineering and testable interface.

---

## 2. Smart Offer Recommendations

**Where:** User dashboard, offer listing endpoints.

**Why here:** Users benefit from personalized suggestions, increasing engagement and demonstrating retrieval-augmented generation (RAG) in a real product context.

**General approach:** Start with simple retrieval of offers based on user purchase history, merchant affinity, or similar user profiles. Enhance with a basic ML model for ranking. Can be implemented as a service layer method or a microservice.

**Benefits:**

- Demonstrates RAG and basic ML ranking.
- Immediate user-facing value.
- Extensible to more advanced recommendation techniques.

---

## 3. Automated FAQ/Support Chatbot

**Where:** User help endpoints, admin dashboard.

**Why here:** Many user questions are answered in documentation/specs. A chatbot powered by RAG can retrieve relevant answers, reducing support load and showcasing LLM integration.

**General approach:** Use a small LLM or open-source model with retrieval from markdown docs. Integrate as a FastAPI endpoint or web widget.

**Benefits:**

- Demonstrates RAG with domain docs.
- Useful for onboarding and support.
- Simple to extend with more sources.

---

## 4. Fraud Pattern Detection

**Where:** Purchase ingestion, admin review dashboard.

**Why here:** Adds a layer of automated anomaly detection, surfacing suspicious activity for admin review.

**General approach:** Implement basic anomaly detection or clustering on purchase data. Flag outliers and alert admins. Can be paired with the existing fraud scoring system.

**Benefits:**

- Demonstrates simple ML for anomaly detection.
- Directly relevant to the domain.
- Can be visualized for learning.

---

## 5. Personalized Cashback Insights

**Where:** User dashboard, monthly summary endpoints.

**Why here:** Users appreciate insights into their cashback activity. Summarization via RAG/LLM is a practical, user-facing AI feature.

**General approach:** Use RAG to pull user transaction data and summarize with a small LLM. Present insights like "You earned 20% more cashback this month than last."

**Benefits:**

- Demonstrates summarization and retrieval.
- Immediate user value.
- Easy to extend with more metrics.

---

## 6. Natural Language Query for Admins

**Where:** Admin dashboard, reporting endpoints.

**Why here:** Allows admins to query the system in natural language, lowering the barrier to analytics and reporting.

**General approach:** Use RAG to translate NL queries into SQL or API calls. Start with a simple parser and retrieval from reporting endpoints.

**Benefits:**

- Demonstrates NL-to-SQL or NL-to-API.
- Useful for admin productivity.
- Extensible to more complex queries.

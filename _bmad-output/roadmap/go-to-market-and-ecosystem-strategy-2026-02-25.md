# Microsimulation — Go-to-Market & Ecosystem Strategy

**Author:** Lucas
**Date:** 2026-02-25
**Purpose:** Parallel activities alongside product development — visibility, credibility, adoption, and funding

---

## Legend

- ✅ **Done** — Completed step
- 🔨 **In Progress** — Currently active (update colors as work begins)
- 🔲 **Not Started** — Upcoming work

---

```mermaid
---
title: Microsimulation — Go-to-Market & Ecosystem Strategy
---
flowchart LR
    classDef upcoming fill:#adb5bd,stroke:#6c757d,color:#000

    subgraph OSS ["🔓 Open Source Setup"]
        direction TB
        GH["🔲 GitHub Public Repo<br><i>License, README,<br>contributing guide</i>"]:::upcoming
        PYPI["🔲 PyPI Package<br><i>pip install microsimulation<br>ready for users</i>"]:::upcoming
        GH --> PYPI
    end

    subgraph WEB ["🌐 Website & Visibility"]
        direction TB
        LAND["🔲 Landing Page<br><i>What it does, who it's for,<br>live demo link</i>"]:::upcoming
        DOCS["🔲 Public Docs Site<br><i>Quickstart, API reference,<br>tutorials</i>"]:::upcoming
        LAND --> DOCS
    end

    subgraph OUT ["📣 Prospection & Outreach"]
        direction TB
        OF["🔲 OpenFisca Community<br><i>Engage maintainers,<br>position as companion tool</i>"]:::upcoming
        GOV["🔲 Government Teams<br><i>Ministries, evaluation depts,<br>pilot partnerships</i>"]:::upcoming
        CONF["🔲 Conferences & Demos<br><i>Policy events, Python meetups,<br>live showcase</i>"]:::upcoming
        OF --> GOV
        OF --> CONF
    end

    subgraph ACA ["🎓 Academic Track"]
        direction TB
        DATA["🔲 Data Partnerships<br><i>INSEE, Eurostat,<br>real microdata access</i>"]:::upcoming
        WP["🔲 Working Paper<br><i>Methodology, architecture,<br>carbon tax case study</i>"]:::upcoming
        PEER["🔲 Journal Submission<br><i>Peer-reviewed publication<br>using Microsimulation</i>"]:::upcoming
        DATA --> WP
        WP --> PEER
    end

    subgraph FUND ["💰 Funding & Grants"]
        direction TB
        GRANT["🔲 Research Grants<br><i>Public funding for<br>open-source policy tools</i>"]:::upcoming
        INST["🔲 Institutional Support<br><i>University or ministry<br>sponsorship</i>"]:::upcoming
        GRANT --> INST
    end

    subgraph ELECT ["🗳️ Election App Prep"]
        direction TB
        SCOPE["🔲 Scope & Design<br><i>What voters see,<br>candidate comparison UX</i>"]:::upcoming
        PARTNER["🔲 Media Partnerships<br><i>News outlets, civic tech<br>orgs for distribution</i>"]:::upcoming
        SCOPE --> PARTNER
    end

    OSS -.->|"Start during Sprint 1-2"| WEB
    OSS -.->|"Enables"| OUT
    WEB -.->|"Supports"| ACA
    OUT -.->|"Feeds"| FUND
    ACA -.->|"Credibility for"| ELECT
```

---

## Timing Guide

| When | Product Track | Go-to-Market & Ecosystem |
|------|--------------|--------------------------|
| **Now** | Planning complete, ready to build | Set up GitHub repo, start OpenFisca community conversations |
| **Sprints 1-3** | Building the core engine | Landing page, open-source scaffolding, working paper draft |
| **Sprints 4-6** | Indicators, GUI, pilot | Government outreach with demo-ready product, grant applications |
| **Post Phase 1** | External pilot validated | Conference submissions, journal paper, data partnership asks |
| **Phase 2-3** | Behavioral layer, web UI | Election app groundwork, media partnerships |

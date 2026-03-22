# Tech Spec — ReformLab Commercial Website

**Date:** 2026-03-20
**Type:** New static marketing site
**Domain:** `www.reform-lab.eu`
**Hosting:** Existing Hetzner CX22 (178.104.67.235) via Kamal accessory

---

## Goal

Build a state-of-the-art, original commercial website for ReformLab — a single-page marketing site that presents the platform to policy analysts, researchers, and evaluation teams across France and Europe. The site must feel premium, modern, and distinctive — not like a generic SaaS landing page.

---

## Domain Architecture

| Subdomain | Purpose | Status |
|---|---|---|
| `www.reform-lab.eu` | Commercial / marketing site (this spec) | **New** |
| `app.reform-lab.eu` | Web application (React frontend) | **Move** from `reform-lab.eu` |
| `api.reform-lab.eu` | Backend API (FastAPI) | No change |

DNS: Add `www` A record pointing to `178.104.67.235`. Update existing root/app records as needed.

---

## Design Direction

### Personality
- **Serious but not boring** — this is public policy, not a toy. But it should feel alive, not like a government PDF.
- **European institutional quality** — think French public research labs, Nordic design clarity, not Silicon Valley startup energy.
- **Data-forward** — the site should feel like the product: precise, transparent, structured.

### Visual Identity
- **Color palette:** Deep navy/slate as primary. Warm accent (amber/gold or muted teal) for CTAs and highlights. Clean whites for content areas. Subtle gradients — no flat blocks.
- **Typography:** A distinctive serif or semi-serif for headlines (gives gravitas, sets apart from generic sans-serif SaaS sites). Clean sans-serif for body text. Large type sizes — let the copy breathe.
- **Layout:** Generous whitespace. Asymmetric grids where appropriate. Full-width sections with alternating visual rhythm. No cookie-cutter card grids.
- **Motion:** Subtle scroll-triggered animations (fade-in, parallax, number counters). Nothing flashy — movement should feel like the page is revealing itself, not performing.
- **Illustrations/Graphics:** Abstract data visualizations as decorative elements (not stock photos). Stylized chart fragments, flow diagrams, or dot-grid patterns that evoke data analysis without being literal screenshots.

### State-of-the-Art Techniques
- **Scroll-driven storytelling:** The "How it works" pipeline section should animate as you scroll — stages lighting up sequentially.
- **Glassmorphism or mesh gradients** for hero background — distinctive, modern.
- **Bento grid layout** for the features section — irregular grid with varying card sizes, not a uniform 3-column grid.
- **Comparison table with horizontal scroll on mobile** — the competitive comparison should be interactive, not a cramped table.
- **Dark/light section alternation** — visual rhythm that breaks monotony.
- **Micro-interactions** on CTAs — subtle hover effects, not just color change.

---

## Content Structure (Single Page)

All content comes from `_bmad-output/website-content/`. Use the "WINNERS" selections from `copy-variations-2026-02-25.md`.

### 1. Navigation Bar
- Logo (text: "ReformLab") + tagline
- Anchored links: How it Works, Features, Use Cases, FAQ
- CTA button: "Get Early Access" (product is not live yet)
- Language toggle placeholder (FR/EN) — not functional yet, just visual

### 2. Hero Section
- **Headline:** "See who your policy actually helps."
- **Subheadline:** "Connect open data to policy models. See distributional impact. No coding, no waiting."
- **CTA:** "Get Early Access" (primary) + "See How It Works" (secondary, anchor scroll)
- **Visual:** Abstract animated data visualization — not a product screenshot (product isn't polished enough). Think: flowing particles forming a distribution curve, or a stylized Sankey diagram.

### 3. Problem Statement
- **Header:** "The data is there. The tooling isn't."
- Content from `homepage-narrative-2026-02-25.md` problem section
- Pull-quote: "Policies worth billions go live without anyone knowing who they actually reach."

### 4. How It Works (Pipeline)
- **Header:** "How it works"
- 4 stages from `how-it-works-2026-02-25.md`: Data → Population → Simulation → Results
- **Visual:** Animated horizontal pipeline that lights up on scroll
- Each stage: icon + short description + "what you do / what you skip"

### 5. Features (Bento Grid)
- **Header:** "What you get"
- Source: `features-2026-02-25.md`
- 7 feature cards in a bento layout (varying sizes):
  - Open Data Pipeline (large)
  - Scenario Templates
  - Dynamic Orchestrator (large)
  - Scenario Comparison
  - Indicators & Analysis
  - Run Manifests / Reproducibility
  - No-Code GUI + Python API (large, spans width)

### 6. Before/After Transformation
- **Header:** "From months to minutes"
- The comparison table from `homepage-narrative-2026-02-25.md`
- **Visual:** Two-column layout, "Before" in muted/faded style, "After" in vibrant style

### 7. Use Cases
- **Header:** "Built for the people closest to policy"
- 3 persona cards from `homepage-narrative-2026-02-25.md` (analyst, researcher, evaluation team)
- Expandable use case stories from `use-cases-2026-02-25.md` (accordion or tabs)

### 8. Competitive Landscape
- **Header:** "Nothing like this exists in Europe"
- Comparison table from `homepage-narrative-2026-02-25.md`
- Brief competitor descriptions below the table

### 9. Why Now
- **Header:** "Why now"
- Two cards: "Open data is ready" + "AI changed what's possible"

### 10. FAQ
- **Header:** "Questions"
- Accordion from `faq-2026-02-25.md`
- Group by category: General, Data & Privacy, Technical, Reproducibility, Comparison

### 11. Closing / CTA
- **Quote:** "The next time someone asks 'who does this policy actually help?' — they'll be able to answer."
- **Values line:** "Open-source. Open-data-first. France and Europe."
- **CTA:** "Get Early Access" + "View on GitHub"
- Contact email link

### 12. Footer
- Logo, copyright
- Links: GitHub, Contact, Privacy (placeholder)
- "Built with OpenFisca" mention
- EU flag or similar subtle European identity mark

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | **Astro** | Static-first, zero JS by default, islands for interactive bits. Fastest possible load. |
| Styling | **Tailwind CSS v4** | Already used in the main app. Utility-first, great for one-off marketing designs. |
| Animations | **CSS scroll-driven animations** + small JS for intersection observer fallback | Native performance, no heavy animation library. |
| Interactive bits | Astro islands with **vanilla JS** or tiny Preact components | FAQ accordion, mobile nav, smooth scroll. No React needed for a marketing site. |
| Build | Astro build → static HTML/CSS/JS | Output is a `dist/` folder served by nginx. |
| Fonts | Self-hosted (e.g., **Fraunces** or **Instrument Serif** for headlines, **Inter** or **DM Sans** for body) | Distinctive typography, no Google Fonts dependency. |

### Project Location

```
website/                    ← New directory at repo root
├── src/
│   ├── layouts/
│   │   └── Layout.astro    ← Base HTML layout
│   ├── pages/
│   │   └── index.astro     ← Single page
│   ├── components/
│   │   ├── Nav.astro
│   │   ├── Hero.astro
│   │   ├── Problem.astro
│   │   ├── HowItWorks.astro
│   │   ├── Features.astro
│   │   ├── BeforeAfter.astro
│   │   ├── UseCases.astro
│   │   ├── Comparison.astro
│   │   ├── WhyNow.astro
│   │   ├── FAQ.astro
│   │   ├── Closing.astro
│   │   └── Footer.astro
│   ├── styles/
│   │   └── global.css
│   └── assets/
│       └── fonts/
├── public/
│   ├── favicon.svg
│   └── og-image.png
├── Dockerfile
├── nginx.conf
├── package.json
├── astro.config.mjs
├── tailwind.config.mjs
└── tsconfig.json
```

---

## Deployment

### Dockerfile

```dockerfile
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8090
```

### nginx.conf

```nginx
server {
    listen 8090;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Cache static assets aggressively
    location ~* \.(css|js|woff2|png|svg|jpg|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

### Kamal Accessory (add to `config/deploy.yml`)

```yaml
accessories:
  # ... existing frontend ...
  website:
    image: ghcr.io/reformlab/reformlab-website
    hosts:
      - 178.104.67.235
    port: 8090:8090
    proxy:
      ssl: true
      host: www.reform-lab.eu
      app_port: 8090
```

### CI/CD (add to `.github/workflows/deploy.yml`)

Add a `deploy-website` job that builds `website/Dockerfile`, pushes to `ghcr.io/reformlab/reformlab-website`, and runs `kamal accessory reboot website`. Same pattern as the existing frontend deploy.

---

## Performance Targets

- **Lighthouse score:** 95+ across all categories
- **First Contentful Paint:** < 1s
- **Total page weight:** < 500KB (excluding fonts)
- **Zero layout shift** — all images/elements have explicit dimensions
- **Works without JavaScript** — all content readable, animations are progressive enhancement

---

## SEO & Meta

- `<title>`: "ReformLab — Policy Impact Analysis for France and Europe"
- `<meta description>`: "Open-source platform connecting European open data to policy simulation models. See distributional impact of carbon taxes, subsidies, and social transfers — no coding required."
- Open Graph image with headline + abstract data viz
- `<html lang="en">` with FR version planned later
- Semantic HTML: proper heading hierarchy, `<article>`, `<section>`, `<nav>`

---

## Out of Scope

- Multi-language (FR/EN) — placeholder toggle only, content stays English for now
- Blog / CMS — static content only
- Contact form backend — just a `mailto:` link
- Analytics — can add Plausible or similar later
- Product screenshots — product isn't polished enough yet; use abstract visualizations

---

## Implementation Notes

- Use the `/frontend-design` skill to generate the actual code
- All copy comes verbatim from the website-content files — don't rewrite it
- The site should be buildable and deployable independently from the main app
- Font files go in `src/assets/fonts/` and are self-hosted (no external requests)
- Prefer CSS-only animations where possible; JS only for intersection observer triggers

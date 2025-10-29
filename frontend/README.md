# Study Companion Frontend

Premium React + Vite interface for ELEC5620 Group 78. The UI now ships with an AI-company inspired theme: dark-first palette, glass surfaces, gradient beams, and motion-crafted interactions across all routes.

## Stack Highlights
- React 19 + TypeScript + Vite
- Tailwind CSS with custom tokens (aurora gradients, glass utilities, aurora timing)
- shadcn/ui primitives (Radix) + Lucide icons (0.452)
- Framer Motion for page + micro interactions
- React Query for data access to the existing backend APIs

## Running Locally
```bash
npm install
npm run dev
```
The existing API routes and contracts remain unchanged. Update `VITE_API_BASE_URL` in `frontend/.env` if needed.

## Design System & Components
- Responsive App Shell with collapsible sidebar, command palette (`⌘/Ctrl + K`), and breadcrumb-aware top bar
- Reusable `components/ui/*` atoms: `Button`, `Card`, `Tabs`, `Select`, `SegmentedControl`, `Dialog`, `Drawer`, `Toast`, `Tooltip`, `Command`, `Switch`, `Skeleton`, `Badge`, `Kbd`
- Gradient utilities (`bg-aurora`, `ring-aurora`), noise backgrounds, glass morph cards, animated beams
- Screenshots: add dark/light hero and page captures to `/docs` (placeholders: `/docs/dashboard.png`, `/docs/emails.png`, `/docs/summarize.gif`)

## Route Experiences
- **/** Dashboard hero with animated border, quick action flows, KPI glass cards, and weekly engagement sparkline (Recharts)
- **/emails** Motion email cards with avatar initials, hover lift, fallback badges, and empty/refresh states
- **/study/plan** Zod-validated stepped form with animated success banner + ICS download CTA
- **/summarize** Split layout: input tabs (text/URL) vs. animated results pane with TL;DR and Q&A chips
- **/quiz** Framer Motion question stack, elevated option pills, animated rationale reveal
- **/travel** Gradient-ring advice card with weather icons, route button, and fallback messaging
- **/todo** Drag-to-reorder drafts (Framer Motion Reorder), due date quick chips, confidence select, animated saved list
- **/places** Debounced search, glass result cards with route CTA, alias/tag badges
- **/settings** Digest toggle, theme segmented control (light/dark), and privacy copy deck

## Notes for QA
- Color contrast ≥ WCAG AA on dark/light themes
- Respect `prefers-reduced-motion` via Framer Motion defaults
- Pages remain responsive down to 320px width
- Command palette covers all routes + quick actions; notifications + theme toggle accessible via keyboard

## Next Steps
1. Capture fresh screenshots/GIFs for the README placeholders
2. Run `npm run build` to confirm type safety + Tailwind compilation
3. Optionally add Cypress/Playwright smoke flows for critical actions (summaries, quiz, todo save)

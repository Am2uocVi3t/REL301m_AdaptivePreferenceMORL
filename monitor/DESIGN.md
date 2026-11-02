---
name: MORL Training Console
colors:
  primary: "#70E4C4"
  canvas: "#09111B"
  surface: "#111E2C"
  border: "#293A4E"
  text: "#F0F5FC"
  muted: "#A7B8CC"
  warning: "#FFD08B"
  error: "#FF8A94"
typography:
  headline: {fontFamily: Segoe UI, fontSize: 30px, fontWeight: 600, lineHeight: 1.2}
  numeric: {fontFamily: Cascadia Code, fontSize: 13px, fontWeight: 400, lineHeight: 1.5}
rounded: {sm: 4px, md: 6px}
spacing: {xs: 6px, sm: 12px, md: 18px, lg: 28px}
---

# MORL Training Console

## Overview
An actual local research operations console, not a mock terminal. It inherits
the root DESIGN.md palette and uses a denser monospace variant for telemetry.
DESIGN_VARIANCE 4, MOTION_INTENSITY 1, VISUAL_DENSITY 8. No dependencies/CDN.

## Colors
Mint is live activity, amber is pending/stale, rose is a technical failure.
Completion is a neutral execution fact. Task success is a separate number.

## Typography
Local Cascadia Code / Consolas for data, local Segoe UI for headings. Tabular
numbers, uppercase compact panel labels, regular case for explanatory text.

## Layout
Slim left rail, full-width progress band, dense worker table, adjacent selected
worker inspector, loss plot and log stream. On mobile the rail becomes a header,
panels stack and only the worker table scrolls horizontally.

## Elevation & Depth
Flat navy surfaces, thin borders and one restrained accent. No glow or fake CRT
noise, decorative gradients, fabricated shell output or animated counters.

## Shapes
Small corner radii, square progress segments and compact controls.

## Components
Auto-refresh status, pause-view/refresh controls, job filter and real log tabs.
Keyboard-operable selection, strong focus rings, readable error/empty/offline
states. Connection state must distinguish a failed API refresh from a stopped
training process. Show stale data timestamps and never invent loss/ETA.

## Do's and Don'ts
Keep training progress separate from experimental qualification. Never label a
job healthy solely because a stored status says running. Observe process metadata,
append-only logs and finalized results; do not open rotating telemetry JSON.
Never modify training files, launch/kill workers or read a final test split.
The terminal aesthetic is the functional UI, not a screenshot.

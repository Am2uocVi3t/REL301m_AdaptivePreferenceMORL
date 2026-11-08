---
name: MORL Flight & Field Lab
colors:
  primary: "#70E4C4"
  reference: "#BCA9FF"
  canvas: "#09111B"
  surface: "#111E2C"
  border: "#293A4E"
  text: "#F0F5FC"
  muted: "#A7B8CC"
  warning: "#FFD08B"
typography:
  headline: {fontFamily: system-ui, fontSize: 28px, fontWeight: 650, lineHeight: 1.15}
  title: {fontFamily: system-ui, fontSize: 18px, fontWeight: 600, lineHeight: 1.3}
  body: {fontFamily: system-ui, fontSize: 14px, fontWeight: 400, lineHeight: 1.5}
  caption: {fontFamily: system-ui, fontSize: 12px, fontWeight: 400, lineHeight: 1.4}
  numeric: {fontFamily: ui-monospace, fontSize: 13px, fontWeight: 500, lineHeight: 1.4}
rounded: {sm: 6px, md: 12px, lg: 18px}
spacing: {xs: 6px, sm: 12px, md: 18px, lg: 28px}
components:
  button-primary: {backgroundColor: "{colors.primary}", textColor: "{colors.canvas}", rounded: "{rounded.sm}", padding: 12px}
  stage: {backgroundColor: "{colors.surface}", rounded: "{rounded.md}"}
---

# MORL Flight & Field Lab

## Overview
A cinematic interactive instrument, not a document reader. The user has approved
same-checkpoint inference comparison: fixed default preference left, user slider
preference right, no retraining. UI and Python engine run locally, no cloud calls.
Token organization studied from the ElevenLabs entry in the design-spec collection;
the visual direction here is original, dark mission-control rather than editorial.

## Colors
Mint identifies user preference; lavender identifies the fixed reference. Amber
is for pending preferences, changed-mid-episode caveats and Minecart qualification.

## Typography
Local system fonts only; no CDN. Strong numeric alignment for rewards and steps.

## Layout
Compact header, environment/run controls, two equal large canvas stages, and
preference controls and reward telemetry visible in one desktop viewport. Narrow
screens stack panels without hiding controls. Avoid landing-page hero sections.

## Elevation & Depth
Use tonal layers and thin borders. Environment artwork carries depth: star field,
crater terrain, shaded ship; mineral outcrops, base station and shaded minecart.

## Shapes
Restrained rounded panels; technical buttons with consistent focus rings.

## Components
Two scenes show real engine coordinates. Cosmetic renderer changes artwork only;
offer original environment renderer as an audit view. Do not interpolate physics,
invent cargo, move sprites independently of the backend, or fake successful actions.
Preference bars sum to one, remaining bars redistribute proportionally. A pending
slider change is not active until reset/run, except explicit live preference mode.

## Do's and Don'ts
Do display checkpoint identity, no-gradient status, current/pending weights,
terminal status, raw vector returns and deterministic seed. Live edits must be
marked history-dependent, not matched-start outcomes. Never promise the failed
Minecart checkpoint will deliver ore. Never silently auto-reset finished episodes.

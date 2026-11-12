---
name: REL301m Recording Desk
colors:
  primary: "#14201B"
  secondary: "#0C5A50"
  tertiary: "#DE5A26"
  neutral: "#F7F4EE"
  surface: "#FFFFFF"
  error: "#A52B2B"
typography:
  headline: {fontFamily: "Georgia, serif", fontSize: 36px, fontWeight: 600, lineHeight: 1.2}
  body: {fontFamily: "Segoe UI, sans-serif", fontSize: 16px, fontWeight: 400, lineHeight: 1.6}
  prompter: {fontFamily: "Segoe UI, sans-serif", fontSize: 28px, fontWeight: 500, lineHeight: 1.6}
rounded: {sm: 4px, md: 10px}
spacing: {sm: 8px, md: 16px, lg: 28px}
---

## Overview

An English local recording desk for a student narrating an actual MORL demo.
Clear controls, a readable script and reliable exports take priority over effects.
This scoped design governs the recording utility, not the existing research demo.

## Colors

Warm paper, dark pine ink and a restrained FPT-orange record action. Teal marks
secondary navigation. Red is reserved for recording/failure states.

## Typography

System fonts avoid network/font-loading dependencies. The prompter has adjustable
text size and reading speed. Labels remain readable without all-caps paragraphs.

## Layout

Wide screens: preview and script side by side, controls underneath. On narrow
screens the script follows the preview. Keep a visible recording state and timer.

## Elevation & Depth

Use borders and tonal surfaces rather than glass effects or large shadows.

## Shapes

Small, consistent radii and generous hit targets. Native file and select controls.

## Components

Source selection, video canvas, editable script, prompter transport, microphone
meter, record/stop, take playback, audio import and asynchronous MP4 export.

## Do's and Don'ts

Keep narration outside the exported picture. Ask for microphone access only on
an explicit record action. Never claim an exported silent preview contains the
user's voice. Preserve recordings on errors; permit local download before export.
Real demo footage and generated explanatory title cards must remain distinct.
Use the video media clock for word highlighting, seeking and pauses. The slow
default is 95 words per minute with breathing room; changing pace must also
change video speed. Keep original scene-to-word timing with the exported master.

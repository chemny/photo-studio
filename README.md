# Photo Studio

English | [中文](./README.zh.md)

## Overview

Photo Studio is an Agent Skill for photography studios and portrait teams. Give it a client photo and a request to plan portraits, compare directions, make a finished image, or edit an existing photo. It keeps the requested people recognizable and checks the result before delivery.

It covers ID photos, wedding portraits, family and parent-child portraits, personal-branding portraits, and artistic portraits. Pet portraits, memes, and mixed collections have lighter routes.

## Preview

![Illustration of Photo Studio's nine supported photo categories](./assets/previews/photo-studio-overview.png)

AI-generated illustration of the supported categories, not a client case or a sample of their final layouts.

## Features

| Capability | What it helps you do |
| --- | --- |
| Creative portrait preview | Compare nine wedding, personal-branding, or artistic directions in one portrait sheet, with varied scenes, actions, framing, and styling. |
| Family and parent-child preview | Compare four landscape scenes and activities while keeping every requested person in each panel. |
| Selected portrait final | Turn an approved panel into a new single image, preserving the chosen scene and styling while checking the person against the original reference. |
| ID photos | Make one file to an explicit size and background when the specification is clear; check the receiving organization's rules for official use. |
| Existing-photo editing | Change a requested background, outfit, photographic look, or retouching detail while protecting the parts meant to stay. |
| Quality checks and revisions | Check identity, body proportions, margins, scene variety, and image proportions; revise the requested detail. |
| Optional studio package | Create job records, contact sheets, exact output formats, and delivery checks when a formal package is requested. |

## Installation

### Requirements

For portrait previews, prepare a subject photo and an Agent with an image tool. Multi-panel previews also use the bundled Python composition helper.

| Item | Requirement |
| --- | --- |
| Agent client | Codex, Claude Code, or OpenClaw with Skill support. |
| Image creation | An image generation or editing tool available to the Agent; no image model is bundled. |
| Portrait source | A clear photo of the subject; for official ID photos, also provide current receiving-channel requirements. |
| Multi-panel composition and exact formatting | Python 3.10+ and Pillow. |

### Quick Installation

Send this to your Agent:

```text
Check the core requirements, install this Skill from https://github.com/chemny/photo-studio, and verify that it loads. Tell me if an image tool or permission is missing. Set up optional image services only if I ask.
```

Image results depend on the tools available in your Agent client. The Python helpers use portable paths; repository CI checks macOS, Windows, and Linux.

## Quick Start

Upload a clear portrait and ask:

```text
Create a nine-panel personal portrait preview with different believable settings, outfits, and actions. Keep me recognizable.
```

You should receive one preview sheet. Compare the scenes and framing, then request a revision or name a panel to make as a separate final image.

## Usage Examples

- **Wedding portraits:** “Use these two reference photos for a nine-panel wedding preview. Vary the locations and actions, and keep both people recognizable.”
- **Family portrait:** “Use this family photo for four landscape scenes. Include everyone in every panel, with different activities.”
- **Parent-child portrait:** “Use this photo of me and my child for four landscape directions with different activities. Keep our faces and ages recognizable.”
- **ID photo:** “Make one blue-background two-inch ID photo from this image. Preserve my face and clothing.” For an official application, give the receiving channel's current pixel, file-size, and background rules.
- **Existing photo:** “Replace this photo's background with a bright studio. Keep my face, outfit, and pose.”

## How It Works

The [Skill entry point](./SKILL.md) identifies the photo product and reads its matching rule in [`references/`](./references/). Creative previews use independently generated 3:4 portrait cells for a nine-panel sheet, or 4:3 landscape cells for a four-panel family or parent-child sheet. The [composition helper](./scripts/compose_grid.py) checks matching sizes and proportions, then joins the cells without stretching them. A selected final is generated as its own image and checked against both the original person reference and the chosen panel.

Product guidance covers [ID sizes](./references/id-photo-size-map.md), [wedding](./references/wedding-photo.md), [family and parent-child](./references/family-portrait.md), [personal branding](./references/personal-branding.md), [artistic portraits](./references/artistic-portrait.md), [portrait direction](./references/portrait-direction.md), and [existing-photo editing](./references/photo-editing.md). Only formal package requests use the optional job and delivery scripts. The [workflow acceptance cases](./references/workflow-acceptance.md) check routing and conversation behavior.

## Repository Structure

```text
photo-studio/
├── SKILL.md                  # Agent entry point
├── references/               # Photo-product and quality rules
├── scripts/                  # Grid, formatting, and optional delivery helpers
├── assets/                   # Presets and category illustration
├── agents/                   # Agent metadata
├── requirements.txt         # Python helper dependency
├── README.md
├── README.zh.md
└── LICENSE
```

## License

[MIT](./LICENSE) covers this repository. It does not grant rights to a user's uploaded photos or third-party material.

## About Me

Maintained by Neo Chen. For project feedback, use [GitHub Issues](https://github.com/chemny/photo-studio/issues).

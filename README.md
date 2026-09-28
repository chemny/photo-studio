# Photo Studio

English | [中文](./README.zh.md)

Photo Studio is an Agent Skill for photography studios and portrait businesses. It turns client reference photos and requests into usable previews or finished files without a long intake conversation. It routes clear ID-photo requests directly to a finished file, asks once when a required specification is missing, previews family and parent-child portraits in a four-panel sheet, and uses a nine-panel sheet for other creative portraits before individual finals.

The core workflows cover ID photos, wedding portraits, family and parent-child portraits, personal-branding portraits, and artistic portraits. Meme, pet-portrait, and mixed-collection routes are lighter workflows.

## Who Is This For?

- Photography studios that need a repeatable intake, preview, quality-check, and delivery workflow.
- Staff preparing an electronic ID photo with a named size and background.
- Couples or individuals exploring wedding-portrait directions.
- Families comparing four distinct group or parent-child scenes and actions.
- Creators and professionals comparing personal-branding or artistic portrait ideas.
- Studios producing a formal package with optional proofing and delivery records.

## What It Does

The Skill reads the uploaded image and request together. It preserves each subject's recognizable identity, fills safe defaults, and asks for genuinely missing information in one place. A clear ID-photo request goes to one final image. Family and parent-child portraits start with one 2 × 2 sheet of landscape 4:3 panels; wedding, personal-branding, and artistic portraits normally start with one 3 × 3 sheet of portrait 3:4 panels. Approving a concept does not silently create individual final files.

## Core Capabilities

| Capability | What it helps you do |
| --- | --- |
| Direct ID-photo routing | Map names such as small one-inch, one-inch, small two-inch, and two-inch to explicit output sizes; apply a requested background and check composition. |
| One-sheet creative preview | Compare nine wedding, personal-branding, or artistic directions without producing nine individual finals. |
| Family and parent-child preview | Compare four landscape scenes with distinct actions while keeping every requested family member in every panel. |
| Identity and composition checks | Keep faces and natural body proportions recognizable; check headroom, side room, wardrobe, hands, and panel ratios. |
| Focused revisions | Change the requested detail while retaining the confirmed person and other accepted parts. |
| Optional studio delivery | Use job, contact-sheet, formatting, and validation scripts only when a formal package is requested. |

## Platform Compatibility

The Markdown instructions are designed for Codex, Claude Code, and OpenClaw; image generation depends on the tools available in the running Agent. The optional Python/Pillow helpers use portable paths, and repository CI is configured for macOS, Windows, and Linux.

## Install

Send this to your Agent:

```text
Install this Skill for me:
https://github.com/chemny/photo-studio
```

The Agent will choose the installation method for the current client, check dependencies, and verify that the Skill loads.

This is a private repository. The installing Agent must have GitHub access to it.

## Quick Start

Upload a clear portrait and say:

```text
Create one standard two-inch ID photo with a blue background from this image. Preserve my face and clothing.
```

Expected result: one ID-photo file at the mapped pixel size. For an official application, provide the receiving channel and its current pixel, file-size, and background requirements; a paper-photo size may differ from an online upload requirement, and no general preset can guarantee acceptance.

## Usage Examples

```text
Use these two reference photos to show me wedding-portrait directions. Start with one nine-panel preview; do not make individual finals yet.
```

```text
Use this clear family group photo to show four landscape family-portrait directions. Keep all family members in each panel, with different locations and actions.
```

```text
Use this photo of me and my child to show four landscape parent-child directions with varied activities. Keep our faces and ages recognizable.
```

```text
Create a personal-branding portrait preview that shows both my work and everyday life. Keep the same person in every panel.
```

```text
Make an artistic portrait concept sheet with more expressive lighting and styling, while keeping my face recognizable.
```

## How It Works

The main [Skill instructions](./SKILL.md) route the request to a product-specific reference. [Size mapping](./references/id-photo-size-map.md), [wedding guidance](./references/wedding-photo.md), [family and parent-child guidance](./references/family-portrait.md), [personal-branding guidance](./references/personal-branding.md), and [artistic-portrait guidance](./references/artistic-portrait.md) provide the detailed rules. A [workflow acceptance matrix](./references/workflow-acceptance.md) captures conversation regressions. The scripts format exact files and support formal studio packages; ordinary concept previews do not require a job directory.

## Repository Structure

```text
photo-studio/
├── SKILL.md
├── README.md
├── README.zh.md
├── LICENSE
├── agents/
├── assets/                 # size, composition, and portrait presets
├── references/             # product rules and quality checks
├── scripts/                # optional formatting and delivery helpers
└── requirements.txt
```

## Requirements

- An Agent with an available image-generation or image-editing tool for photo creation. The repository provides the workflow and helpers; it does not bundle an image model.
- Python 3.10+ and Pillow for exact image formatting or optional studio-delivery scripts.
- A clear subject reference image; official ID-photo uses should include the receiving organization's current rules.

## License

MIT. See [LICENSE](./LICENSE). The license applies to this repository, not to a user's uploaded photographs or third-party material.

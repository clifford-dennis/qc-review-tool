# Image QC Checker

A desktop tool for QA teams to review, score and action images - built in Python with a Tkinter GUI.

## Background

Built at CarCutter to replace a manual spreadsheet-based QC process. The image processing team reviewed hundreds of car images per day across multiple clients, flagging defects and assigning next actions. The existing workflow was slow and error-prone - reviewers had to open images separately, type decisions into a spreadsheet, and track progress manually.

This tool puts the image and the decision form side by side in one window, saves state automatically, and lets reviewers move through an entire batch using only keyboard shortcuts.

## What it does

- Loads a batch of images from a structured directory (organised by week, date, and client namespace)
- Displays each image fullscreen alongside QC controls
- Lets reviewers record:
  - **QC Decision** — Right / Wrong
  - **QC Observations** — Clipping, Shadow, Perspective, Background, LP missing, LP alignment, Haziness
  - **Retouch Quality** — Good / Bad
  - **Retouch Observations** - same categories
  - **Next Action** - Ignore / Retouch / Retake
- Saves results to CSV per batch session
- Persists session state to JSON so reviewers can pause and resume without losing progress
- Keyboard shortcuts for every action — no mouse required during review

## Tech stack

- Python 3
- Tkinter (GUI)
- Pillow / PIL (image loading and display)
- argparse (CLI interface)
- csv, json (output and state persistence)

## Usage

```bash
python qc_comp.py \
  --root /path/to/images \
  --output /path/to/output \
  --week_num W38 \
  --date 20250910 \
  --namespace client-namespace
```

**Expected directory structure:**

```
/root/
  W38/
    20250910/
      client-namespace/
        image1.jpeg
        image2.jpeg
        ...
```

**Output:**

```
/output/
  W38-20250910-client-namespace.CSV
  W38-20250910-client-namespace.json
```

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `←` / `→` | Previous / Next image |
| `q` | Focus QC section |
| `r` | Focus Retouch section |
| `Escape` | Quit |

## Requirements

```bash
pip install Pillow
```

Tkinter is included with standard Python installations.

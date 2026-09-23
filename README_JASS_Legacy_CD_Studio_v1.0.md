# JASS Legacy CD Studio

### Prepare, validate, build, document and verify CD-ROM images for legacy software preservation and emulation.

**Python • PySide6 • SQLite-friendly workflow • ISO 9660 • 86Box**

---

## 💿 What is JASS Legacy CD Studio?

**JASS Legacy CD Studio** is a lightweight desktop application for creating CD-ROM ISO images from legacy software folders.

It is designed especially for **software preservation, vintage computing and emulator workflows**, including projects using **86Box, Windows 95/98, DOS and other historical PC environments**.

Instead of being only an ISO generator, the application brings several preservation tasks together:

```text
Legacy Software Folder
        │
        ▼
   Analyze Content
        │
        ├── File count
        ├── Directory count
        ├── Size
        ├── Legacy filename checks
        └── CD capacity check
        │
        ▼
     Build ISO
        │
        ├── ISO 9660
        ├── Legacy-safe filenames
        └── Volume label
        │
        ▼
   Documentation
        │
        ├── Manifest
        └── SHA-256
        │
        ▼
   86Box / Other Emulator
```

---

# 🕰️ Why this project?

A large amount of useful software from the DOS and Windows 9x era exists only as old folders, optical media, extracted archives or miscellaneous files.

Modern operating systems make it easy to copy those files, but legacy operating systems often expect software to arrive in a much more historically appropriate form:

> **a CD-ROM containing the original-style software distribution.**

JASS Legacy CD Studio provides a simple way to turn a preserved folder into a documented ISO image suitable for an emulator workflow.

---

# 🎯 Primary Use Case

For example, a preserved FoxPro installation might look like:

```text
D:\LegacySoftware\FoxPro26\
│
├── SETUP.EXE
├── FOXPRO.EXE
├── README.TXT
├── TOOLS\
├── HELP\
└── ...
```

JASS Legacy CD Studio can turn that folder into:

```text
FOXPRO26.ISO
```

which can then be attached to a virtual CD-ROM drive in an emulator such as 86Box.

---

# ✨ Features

### 📁 Folder Analysis

Before creating an image, the application analyzes:

- File count
- Directory count
- Total data size
- Filename characteristics
- Potential legacy naming problems
- Potential ISO 8.3 collisions
- CD capacity

---

### 💿 ISO Creation

Creates an **ISO 9660 Level 1** CD image using `pycdlib`.

The v1.0 workflow favors conservative **DOS-style 8.3 filenames** for broad compatibility with older systems.

Example:

```text
LONG_FILENAME.EXE
```

can be represented inside the legacy image with a safe ISO alias such as:

```text
LONG_F~1.EXE
```

The original source folder is not modified.

---

### 🏷️ Volume Labels

Set a CD volume label such as:

```text
FOXPRO26
OFFICE97
WIN98UTIL
DBASETOOLS
```

---

### 📊 CD Capacity

Built-in capacity presets:

```text
650 MB CD-ROM
700 MB CD-ROM
Custom
```

The application reports whether the source data fits the selected CD capacity.

---

### 📋 Manifest Generation

The application can create a companion manifest:

```text
FOXPRO26_MANIFEST.txt
```

The manifest records information such as:

```text
Volume label
Source folder
ISO filename
File count
Directory count
Source data size
ISO size
File listing
SHA-256
```

This makes the resulting image easier to document and archive.

---

### 🔐 SHA-256

The finished ISO can be hashed using SHA-256.

Example:

```text
ISO SHA-256
--------------------------------
7c9b...a21f
```

This allows the image to be verified later.

---

# 🖥️ Designed for 86Box Workflows

JASS Legacy CD Studio is particularly useful alongside a personal 86Box laboratory.

Example:

```text
                 JASS Legacy Software Lab

                         │
             ┌───────────┴───────────┐
             │                       │
        Legacy Files              86Box
             │                       │
             ▼                       ▼
    JASS Legacy CD Studio      Windows 95/98
             │                       │
             ▼                       ▼
          ISO Image ───────────► CD-ROM
                                     │
                                     ▼
                              Legacy Software
```

Typical examples include:

- DOS software
- Windows 3.x software
- Windows 95 software
- Windows 98 software
- FoxPro
- dBase
- DBF-based applications
- Old development tools
- Historical utilities
- Office software
- Archived installers

---

# 🧰 Technology

| Component | Technology |
|---|---|
| Language | Python |
| GUI | PySide6 |
| ISO backend | pycdlib |
| Image format | ISO 9660 |
| Checksums | SHA-256 |
| Platform | Windows / Linux |
| Primary use | Legacy software preservation |

---

# 🚀 Installation

## Requirements

Python 3.x

Install dependencies:

```bash
pip install PySide6 pycdlib
```

---

# ▶️ Running

```bash
python JASS_Legacy_CD_Studio_v1.0.py
```

On Windows:

```powershell
py JASS_Legacy_CD_Studio_v1.0.py
```

---

# 📖 Typical Workflow

### 1. Select the source folder

Choose the folder containing the legacy software.

### 2. Analyze

Click:

**Analyze Folder**

Review:

- files
- directories
- total size
- filename warnings
- CD capacity

### 3. Set the volume label

Example:

```text
FOXPRO26
```

### 4. Choose ISO destination

Example:

```text
D:\LegacyISO\FOXPRO26.iso
```

### 5. Build

Click:

**Build ISO**

### 6. Verify

Review:

- ISO size
- SHA-256
- generated manifest

### 7. Attach to 86Box

Configure the emulator's virtual CD-ROM drive to use the generated ISO.

---

# 🗂️ Preservation Workflow

A recommended archive structure is:

```text
LegacyArchive/
│
├── FoxPro26/
│   ├── Source/
│   ├── ISO/
│   ├── Documentation/
│   └── Checksums/
│
├── Office97/
│   ├── Source/
│   ├── ISO/
│   ├── Documentation/
│   └── Checksums/
│
└── Windows98Utilities/
    ├── Source/
    ├── ISO/
    ├── Documentation/
    └── Checksums/
```

The important idea is to preserve both:

```text
SOURCE
+
DERIVED ISO
+
DOCUMENTATION
+
CHECKSUM
```

rather than keeping only the ISO.

---

# 🛡️ Source Preservation

JASS Legacy CD Studio does not modify the selected source directory.

The ISO is a **derived artifact**.

Conceptually:

```text
Original Files
      │
      │ read-only workflow
      ▼
JASS Legacy CD Studio
      │
      ├── ISO
      ├── Manifest
      └── SHA-256
```

This makes the original software folder suitable for continued archival use.

---

# 🧪 Current Version

## v1.0 — Initial Legacy CD Builder

Current release provides:

- Source folder analysis
- CD capacity analysis
- Legacy filename analysis
- ISO 9660 Level 1 creation
- DOS-style 8.3 naming
- Volume labels
- Manifest generation
- SHA-256 calculation
- Build log
- PySide6 desktop interface

---

# 🗺️ Roadmap

Possible future versions may add:

### v1.1

- [ ] Persistent project files
- [ ] Recent projects
- [ ] Drag-and-drop source folders
- [ ] Improved ISO verification
- [ ] Better collision reporting
- [ ] Dedicated archive metadata

### v1.2

- [ ] Bootable ISO support
- [ ] Joliet option
- [ ] Multiple ISO profiles
- [ ] CD image inspection
- [ ] Existing ISO information viewer

### v2.x

- [ ] 86Box project integration
- [ ] DOS / Windows 95 / Windows 98 presets
- [ ] Legacy software archive catalog
- [ ] ISO library
- [ ] Automatic metadata manifests
- [ ] Batch ISO creation
- [ ] Archive verification
- [ ] CD image comparison

The roadmap is intentionally focused on **software preservation rather than becoming a general-purpose disc-burning application**.

---

# 🔬 Legacy Software Preservation

This project is part of a broader interest in preserving and understanding historical software environments.

The intended workflow is:

```text
Discover
   ↓
Preserve
   ↓
Document
   ↓
Build Media
   ↓
Emulate
   ↓
Study
```

The objective is not simply to run old software.

It is also to preserve:

- installation media
- directory structures
- executable files
- documentation
- data files
- compatibility information
- checksums
- historical software environments

---

# 🧭 JASS Legacy Software Lab

JASS Legacy CD Studio is part of the **JASS Digital Lab** ecosystem.

The wider Legacy Software Lab explores technologies such as:

```text
DOS
Windows 3.x
Windows 95
Windows 98
FoxPro
dBase
DBF
Legacy databases
Industrial software
Emulation
Software preservation
Data migration
```

The project also complements modern legacy-system modernization work involving:

```text
FoxPro / dBase
       │
       ▼
DBF / Legacy Data
       │
       ▼
Python
       │
       ▼
SQLite / PostgreSQL
       │
       ▼
PySide6
       │
       ▼
Modernized Applications
```

---

# 🔐 Offline and Local-First

The application is designed for local operation.

It does not require:

- cloud accounts
- remote APIs
- hosted databases
- online services
- AI services

The source software and resulting ISO remain under the user's control.

---

# ⚖️ Preservation and Copyright

JASS Legacy CD Studio is a **software preservation and image-building tool**.

Users are responsible for ensuring that they have the legal right to copy, archive, modify or redistribute the software and media they process.

The project does not provide copyrighted legacy software.

---

# ❤️ JASS Legacy CD Studio

> **Preserve the files. Build the image. Document the software.**

A lightweight desktop tool for the practical preservation of legacy software and vintage computing environments.

---

## Part of JASS Digital Lab

**JASS Digital Lab**

*Building practical software for preserving, exploring and understanding digital knowledge.*

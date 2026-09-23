#!/usr/bin/env python3
"""
JASS Legacy CD Studio v1.0
A PySide6 desktop application for preparing, analyzing, building,
documenting, and verifying CD-ROM ISO images for legacy software
preservation and emulation.

Backend:
    pycdlib

Install:
    pip install PySide6 pycdlib
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QSplitter, QStatusBar, QTabWidget, QTextEdit, QVBoxLayout, QWidget
)

try:
    import pycdlib
except ImportError:
    pycdlib = None


APP_NAME = "JASS Legacy CD Studio"
VERSION = "1.0"
CD_CAPACITIES = {
    "650 MB CD-ROM": 650 * 1000 * 1000,
    "700 MB CD-ROM": 700 * 1000 * 1000,
    "Custom": 0,
}


@dataclass
class FileEntry:
    source: Path
    relative: str
    size: int
    iso_name: str = ""


@dataclass
class Analysis:
    files: list[FileEntry]
    directories: int
    total_bytes: int
    long_names: int
    invalid_names: int
    duplicate_iso_names: int


def human_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(n)
    for unit in units:
        if value < 1000 or unit == units[-1]:
            return f"{value:,.1f} {unit}" if unit != "B" else f"{int(value):,} B"
        value /= 1000
    return f"{n:,} B"


def sanitize_83(name: str) -> str:
    p = Path(name)
    stem = re.sub(r"[^A-Za-z0-9_$%'-]", "_", p.stem.upper())
    ext = re.sub(r"[^A-Za-z0-9_$%'-]", "_", p.suffix[1:].upper())
    stem = stem[:8] or "_"
    ext = ext[:3]
    return f"{stem}.{ext}" if ext else stem


def make_unique_83(name: str, used: set[str]) -> str:
    candidate = sanitize_83(name)
    if candidate not in used:
        used.add(candidate)
        return candidate
    p = Path(candidate)
    stem, ext = p.stem[:6], p.suffix
    i = 1
    while True:
        c = f"{stem[:6]}~{i}{ext}"
        if c not in used:
            used.add(c)
            return c
        i += 1


def analyze_folder(root: Path) -> Analysis:
    files = []
    dirs = 0
    total = 0
    long_names = 0
    invalid = 0
    used = set()
    duplicates = 0

    for current, dirnames, filenames in os.walk(root):
        dirs += len(dirnames)
        current_path = Path(current)
        for fn in filenames:
            p = current_path / fn
            rel = p.relative_to(root).as_posix()
            size = p.stat().st_size
            total += size
            if len(fn) > 12 or len(Path(fn).stem) > 8 or len(Path(fn).suffix[1:]) > 3:
                long_names += 1
            if re.search(r"[^A-Za-z0-9_$%'\-\.]", fn):
                invalid += 1
            alias = sanitize_83(fn)
            if alias in used:
                duplicates += 1
            used.add(alias)
            files.append(FileEntry(p, rel, size, alias))

    return Analysis(files, dirs, total, long_names, invalid, duplicates)


def iso_path_parts(relative: str, mapping: dict[str, str]) -> list[str]:
    parts = relative.replace("\\", "/").split("/")
    result = []
    for part in parts:
        result.append(mapping.get(part, sanitize_83(part)))
    return result


class BuildWorker(QObject):
    progress = Signal(int)
    message = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, root: Path, output: Path, label: str, entries: list[FileEntry]):
        super().__init__()
        self.root = root
        self.output = output
        self.label = label
        self.entries = entries

    def run(self):
        if pycdlib is None:
            self.finished.emit(False, "pycdlib is not installed. Run: pip install pycdlib")
            return

        iso = pycdlib.PyCdlib()
        try:
            iso.new(interchange_level=1, vol_ident=self.label[:32])

            # Build directory aliases and file aliases.
            dir_map = {"": ""}
            used_by_dir: dict[str, set[str]] = {"": set()}
            for entry in self.entries:
                parts = entry.relative.replace("\\", "/").split("/")
                parent = ""
                for d in parts[:-1]:
                    key = f"{parent}/{d}" if parent else d
                    if key not in dir_map:
                        used_by_dir.setdefault(parent, set())
                        alias = make_unique_83(d, used_by_dir[parent])
                        dir_map[key] = alias
                        used_by_dir[key] = set()
                        iso_parent = "/" + "/".join(
                            dir_map[x] for x in key.split("/")
                        )
                        iso.add_directory(iso_path=iso_parent)
                    parent = key

            # File aliases within each directory.
            file_maps: dict[str, dict[str, str]] = {}
            for entry in self.entries:
                parts = entry.relative.replace("\\", "/").split("/")
                parent_parts = parts[:-1]
                parent_key = "/".join(parent_parts)
                file_maps.setdefault(parent_key, {})
                used = set(file_maps[parent_key].values())
                alias = make_unique_83(parts[-1], used)
                file_maps[parent_key][parts[-1]] = alias

            total = max(len(self.entries), 1)
            for idx, entry in enumerate(self.entries, 1):
                parts = entry.relative.replace("\\", "/").split("/")
                parent_key = "/".join(parts[:-1])
                parent_iso = "/" + "/".join(
                    dir_map[x] for x in parts[:-1]
                ) if parts[:-1] else "/"
                alias = file_maps[parent_key][parts[-1]]
                iso.add_file(
                    str(entry.source),
                    iso_path=parent_iso.rstrip("/") + "/" + alias
                )
                self.progress.emit(int(idx * 100 / total))
                self.message.emit(f"Added: {entry.relative}")

            self.message.emit("Writing ISO image...")
            self.output.parent.mkdir(parents=True, exist_ok=True)
            iso.write(str(self.output))
            self.message.emit("ISO image written successfully.")
            self.finished.emit(True, str(self.output))
        except Exception as exc:
            self.finished.emit(False, f"ISO build failed: {exc}")
        finally:
            try:
                iso.close()
            except Exception:
                pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.resize(1180, 760)
        self.analysis: Analysis | None = None
        self.thread = None
        self.worker = None
        self.build_entries: list[FileEntry] = []
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #07101d; color: #e7eef7; }
            QGroupBox { border: 1px solid #26384d; border-radius: 8px;
                        margin-top: 12px; padding: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
            QLineEdit, QComboBox, QTextEdit, QListWidget {
                background: #0c1828; border: 1px solid #2a4058;
                border-radius: 6px; padding: 7px; color: #e7eef7;
            }
            QPushButton { background: #14283e; border: 1px solid #34506d;
                          border-radius: 6px; padding: 8px 14px; }
            QPushButton:hover { background: #1b3855; }
            QPushButton:disabled { color: #708198; }
            QProgressBar { border: 1px solid #2a4058; border-radius: 5px;
                           text-align: center; background: #0c1828; }
            QProgressBar::chunk { background: #3f7fb5; border-radius: 4px; }
        """)

        central = QWidget()
        root_layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        title = QLabel(f"💿 {APP_NAME}")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        subtitle = QLabel("Prepare • Validate • Build • Document • Verify legacy CD-ROM images")
        subtitle.setStyleSheet("color:#91a7bf;")
        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter, 1)

        left = QWidget()
        ll = QVBoxLayout(left)

        project = QGroupBox("Project")
        pf = QFormLayout(project)

        self.source_edit = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self.choose_source)
        row = QHBoxLayout()
        row.addWidget(self.source_edit, 1)
        row.addWidget(browse)
        pf.addRow("Source folder", row)

        self.label_edit = QLineEdit("LEGACYCD")
        self.label_edit.setMaxLength(32)
        pf.addRow("Volume label", self.label_edit)

        self.capacity_combo = QComboBox()
        self.capacity_combo.addItems(["650 MB CD-ROM", "700 MB CD-ROM", "Custom"])
        self.capacity_combo.currentTextChanged.connect(self.update_capacity)
        pf.addRow("Target media", self.capacity_combo)

        self.output_edit = QLineEdit()
        out_btn = QPushButton("Choose…")
        out_btn.clicked.connect(self.choose_output)
        orow = QHBoxLayout()
        orow.addWidget(self.output_edit, 1)
        orow.addWidget(out_btn)
        pf.addRow("ISO output", orow)

        ll.addWidget(project)

        opts = QGroupBox("Legacy compatibility")
        ol = QVBoxLayout(opts)
        self.strict_83 = QCheckBox("Use ISO 9660 Level 1 / DOS-style 8.3 filenames")
        self.strict_83.setChecked(True)
        self.strict_83.setToolTip("The v1.0 builder uses safe 8.3 aliases for maximum legacy compatibility.")
        ol.addWidget(self.strict_83)
        self.manifest_check = QCheckBox("Create MANIFEST.TXT beside the ISO")
        self.manifest_check.setChecked(True)
        ol.addWidget(self.manifest_check)
        self.hash_check = QCheckBox("Calculate SHA-256 for the finished ISO")
        self.hash_check.setChecked(True)
        ol.addWidget(self.hash_check)
        ll.addWidget(opts)

        self.analyze_btn = QPushButton("🔍 Analyze Folder")
        self.analyze_btn.clicked.connect(self.analyze)
        self.build_btn = QPushButton("💿 Build ISO")
        self.build_btn.clicked.connect(self.build_iso)
        self.build_btn.setEnabled(False)
        brow = QHBoxLayout()
        brow.addWidget(self.analyze_btn)
        brow.addWidget(self.build_btn)
        ll.addLayout(brow)

        stats = QGroupBox("Analysis")
        sg = QGridLayout(stats)
        self.files_value = QLabel("—")
        self.dirs_value = QLabel("—")
        self.size_value = QLabel("—")
        self.capacity_value = QLabel("—")
        self.compat_value = QLabel("Not analyzed")
        for i, (name, widget) in enumerate([
            ("Files", self.files_value), ("Directories", self.dirs_value),
            ("Data size", self.size_value), ("Capacity", self.capacity_value),
            ("Compatibility", self.compat_value)
        ]):
            sg.addWidget(QLabel(name), i, 0)
            sg.addWidget(widget, i, 1)
        ll.addWidget(stats)
        ll.addStretch()

        right = QTabWidget()
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.manifest_preview = QTextEdit()
        self.manifest_preview.setReadOnly(True)

        right.addTab(self.report, "Analysis Report")
        right.addTab(self.manifest_preview, "Manifest Preview")
        right.addTab(self.log, "Build Log")

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([430, 750])

        self.progress = QProgressBar()
        self.progress.setValue(0)
        root_layout.addWidget(self.progress)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def choose_source(self):
        path = QFileDialog.getExistingDirectory(self, "Select legacy software folder")
        if path:
            self.source_edit.setText(path)
            if not self.output_edit.text():
                p = Path(path)
                self.output_edit.setText(str(p.parent / f"{self.label_edit.text()}.iso"))

    def choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save ISO image", self.output_edit.text() or "legacy.iso",
            "ISO images (*.iso);;All files (*)"
        )
        if path:
            if not path.lower().endswith(".iso"):
                path += ".iso"
            self.output_edit.setText(path)

    def update_capacity(self):
        if self.capacity_combo.currentText() != "Custom" and self.analysis:
            self.update_stats()

    def analyze(self):
        root = Path(self.source_edit.text().strip().strip('"'))
        if not root.is_dir():
            QMessageBox.warning(self, APP_NAME, "Please select a valid source folder.")
            return

        try:
            self.analysis = analyze_folder(root)
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Analysis failed:\n{exc}")
            return

        self.build_entries = self.analysis.files
        self.update_stats()
        self.build_btn.setEnabled(bool(self.analysis.files))
        self.render_report()

        if not self.output_edit.text():
            self.output_edit.setText(str(root.parent / f"{self.label_edit.text()}.iso"))

        self.status.showMessage(f"Analyzed {len(self.analysis.files):,} files.")

    def update_stats(self):
        if not self.analysis:
            return
        a = self.analysis
        self.files_value.setText(f"{len(a.files):,}")
        self.dirs_value.setText(f"{a.directories:,}")
        self.size_value.setText(human_size(a.total_bytes))

        target = CD_CAPACITIES.get(self.capacity_combo.currentText(), 0)
        if target:
            pct = a.total_bytes / target * 100
            self.capacity_value.setText(f"{pct:.1f}% of {human_size(target)}")
            if a.total_bytes > target:
                self.capacity_value.setStyleSheet("color:#ff8b8b;")
            else:
                self.capacity_value.setStyleSheet("color:#9be7a8;")
        else:
            self.capacity_value.setText("Custom")
            self.capacity_value.setStyleSheet("")

        if a.long_names or a.invalid_names or a.duplicate_iso_names:
            self.compat_value.setText("Review warnings")
            self.compat_value.setStyleSheet("color:#ffd27d;")
        else:
            self.compat_value.setText("Ready")
            self.compat_value.setStyleSheet("color:#9be7a8;")

    def render_report(self):
        a = self.analysis
        if not a:
            return
        warnings = []
        if a.long_names:
            warnings.append(f"• {a.long_names:,} filename(s) may require 8.3 aliases.")
        if a.invalid_names:
            warnings.append(f"• {a.invalid_names:,} filename(s) contain characters outside the safe legacy set.")
        if a.duplicate_iso_names:
            warnings.append(f"• {a.duplicate_iso_names:,} possible 8.3 alias collision(s) detected; unique aliases will be generated.")
        if not warnings:
            warnings.append("• No obvious legacy filename issues detected.")

        text = f"""JASS LEGACY CD STUDIO — ANALYSIS
================================

Source
------
{self.source_edit.text()}

Files              : {len(a.files):,}
Directories        : {a.directories:,}
Total data         : {human_size(a.total_bytes)}
Target media       : {self.capacity_combo.currentText()}

Legacy compatibility
--------------------
""" + "\n".join(warnings)

        self.report.setPlainText(text)

        lines = [
            f"JASS Legacy CD Studio v{VERSION}",
            f"Volume: {self.label_edit.text().strip().upper()[:32]}",
            f"Source: {self.source_edit.text()}",
            f"Files: {len(a.files):,}",
            f"Directories: {a.directories:,}",
            f"Data size: {a.total_bytes:,} bytes",
            "",
            "FILE MANIFEST",
            "-------------",
        ]
        for e in a.files:
            lines.append(f"{e.relative}\t{e.size:,}\t{e.iso_name}")
        self.manifest_preview.setPlainText("\n".join(lines))

    def build_iso(self):
        if not self.analysis or not self.analysis.files:
            self.analyze()
            if not self.analysis:
                return

        if pycdlib is None:
            QMessageBox.warning(
                self, APP_NAME,
                "pycdlib is not installed.\n\nInstall it with:\n\npip install pycdlib"
            )
            return

        output = Path(self.output_edit.text().strip().strip('"'))
        if not output:
            QMessageBox.warning(self, APP_NAME, "Choose an ISO output path.")
            return

        label = re.sub(r"[^A-Za-z0-9_]", "_", self.label_edit.text().strip().upper()) or "LEGACYCD"

        target = CD_CAPACITIES.get(self.capacity_combo.currentText(), 0)
        if target and self.analysis.total_bytes > target:
            answer = QMessageBox.question(
                self, APP_NAME,
                f"The source data is {human_size(self.analysis.total_bytes)}, "
                f"which exceeds the selected {human_size(target)} CD capacity.\n\n"
                "Build anyway?"
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.build_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.progress.setValue(0)
        self.log.clear()
        self.log.append(f"Building: {output}")
        self.log.append(f"Volume: {label}")

        self.thread = QThread()
        self.worker = BuildWorker(
            Path(self.source_edit.text().strip().strip('"')),
            output,
            label,
            self.analysis.files
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.message.connect(self.log.append)
        self.worker.finished.connect(self.build_finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def build_finished(self, ok: bool, message: str):
        self.analyze_btn.setEnabled(True)
        self.build_btn.setEnabled(bool(self.analysis and self.analysis.files))
        if not ok:
            QMessageBox.critical(self, APP_NAME, message)
            self.status.showMessage("Build failed.")
            return

        iso_path = Path(message)
        self.log.append(f"\nISO: {iso_path}")
        try:
            size = iso_path.stat().st_size
            self.log.append(f"ISO size: {human_size(size)}")
            if self.hash_check.isChecked():
                sha = hashlib.sha256()
                with iso_path.open("rb") as f:
                    while True:
                        block = f.read(1024 * 1024)
                        if not block:
                            break
                        sha.update(block)
                self.log.append(f"SHA-256: {sha.hexdigest()}")
                self.log.append("Verification: SHA-256 calculated successfully.")
            if self.manifest_check.isChecked() and self.analysis:
                manifest = iso_path.with_name(iso_path.stem + "_MANIFEST.txt")
                lines = [
                    f"{APP_NAME} v{VERSION}",
                    "=" * 60,
                    f"Volume label: {self.label_edit.text().strip().upper()[:32]}",
                    f"Source folder: {self.source_edit.text()}",
                    f"ISO image: {iso_path}",
                    f"Files: {len(self.analysis.files):,}",
                    f"Directories: {self.analysis.directories:,}",
                    f"Source data: {self.analysis.total_bytes:,} bytes",
                    f"ISO size: {size:,} bytes",
                    "",
                    "FILES",
                    "-" * 60,
                ]
                for e in self.analysis.files:
                    lines.append(f"{e.relative}\t{e.size:,}\t{e.iso_name}")
                if self.hash_check.isChecked():
                    lines += ["", "ISO SHA-256", "-" * 60, sha.hexdigest()]
                manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
                self.log.append(f"Manifest: {manifest}")
        except Exception as exc:
            self.log.append(f"Post-build documentation warning: {exc}")

        self.status.showMessage("ISO build completed.")
        QMessageBox.information(
            self, APP_NAME,
            f"ISO created successfully.\n\n{iso_path}"
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

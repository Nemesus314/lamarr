#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Lamarr / Version 1.2.0 / 2024–2026 / Nemesus
# ---------------------------------------------------------------------------
# 20.10.2026 (Neo): Der Name. Hier stand „SubtitleSync / Version 1.1". Das
# Werkzeug hiess im Ordner laengst Lamarr, im Kopf noch nicht — ein Haus, in dem
# jeder Name ein Programm ist, fuehrt den Namen auch im Kopf (Kleinrock, Bismarck,
# Turing …). SubtitleSync bleibt als Untertitel, weil es sagt, was das Ding tut.
# Die Fassung folgt seitdem dem Schema der Plugins (x.y.z):
#   1.0    2024  Projektwerkstatt, vier KI-Instanzen
#   1.1    2026  zweisprachige Oberflaeche, Eingabepruefung
#   1.2.0  18.10.2026 VTT-Parser robust (ohne Stunden, Cue-Settings, Identifier,
#                     keine Division durch Null, keine „60.000") — damals ohne
#                     Nummer ausgeliefert; 20.10.2026 der Name im Kopf.
#   (--version gibt sie aus; eine Quelle, dieser Kopf, siehe __version__.)
#
# DER NAMENSGEBER — bestaetigt von Nemesus am 20.10.2026.
#   Hedy Lamarr (1914–2000), Schauspielerin und Erfinderin. 1942 meldete sie
#   mit George Antheil das Frequenzsprungverfahren an: zwei Sender, die ihre
#   Frequenz synchron wechseln und sich darum nicht verlieren. Genau das tut
#   dieses Werkzeug mit zwei Tonspuren — dieselbe Folge in zwei Geschwindig-
#   keiten, von einem Faktor im Gleichschritt gehalten.
#   Was der Name NICHT bedeutet: kein Funk, kein Spreizspektrum, keine
#   Verschluesselung. Es ist die Synchronitaet, nicht die Technik.
# Built in 2024 in a "Projektwerkstatt" (project workshop): Christian "Nemesus"
# Ermisch together with four AI instances from different houses — an earlier
# Claude, ChatGPT, Gemini, and Grok, who found the last bug. Requisite variety
# in action: the difference between the houses is what closed the gaps.
#
# Updated in 2026 by Claude (Anthropic): bilingual interface (DE/EN), input
# validation (matching block counts), friendlier error messages, cleanup.
# The synchronisation logic itself was left UNCHANGED — it was already right
# for its purpose.
#
# WHAT IT DOES
#   Synchronises the YouTube auto-generated timestamps of two language versions
#   of the SAME video, so the subtitles of one language fit the runtime of the
#   other. It stretches/compresses by a single global factor (the ratio of the
#   two total spoken durations) and anchors the first block, so both versions
#   start at the same point.
#
# IT IS EXACT FOR THIS WORKFLOW, NOT A GENERAL SUBTITLE TOOL.
#   See the README. The two silent preconditions are:
#     1) Same text, same number of blocks in both languages.
#     2) Lead-in/lead-out trimmed: both tracks begin at the first spoken word
#        and end at the last — so only spoken content is measured and stretched.
#   Outside this workflow (independently timed subtitles) the result will drift.
# ---------------------------------------------------------------------------

import os
import re
import sys
import argparse

# 20.10.2026 (Neo): Name und Fassung an EINER Stelle; der Kopf oben zitiert sie.
__title__ = "Lamarr"
__subtitle__ = "SubtitleSync"
__version__ = "1.2.0"

# --- Bilingual user-facing strings -----------------------------------------
MESSAGES = {
    "en": {
        "ask_first":  "Enter the path to the FIRST .vtt file (e.g. German): ",
        "ask_second": "Enter the path to the SECOND .vtt file (e.g. English): ",
        "blocks_counted": "{code}: {n} blocks counted",
        "count_first":  "Blocks in the first file:  {n}",
        "count_second": "Blocks in the second file: {n}",
        "err_not_found": "Could not find the file: {path}\n"
                         "Check the path (drag the file into the terminal to get it right).",
        "err_decode":  "Could not read {path} as UTF-8.\n"
                       "Re-export the subtitles as UTF-8 and try again.",
        "err_timestamp": "Could not read a timestamp in {path}.\n"
                         "Offending line: {line}\n"
                         "Expected format like 00:01:23.456 --> 00:01:25.789",
        "err_mismatch": "STOP — the two files have a DIFFERENT number of blocks "
                        "({a} vs {b}).\n"
                        "This tool needs the SAME number of blocks in both "
                        "languages (same text, same segmentation).\n"
                        "Nothing was written. See the README, section "
                        "'Preconditions'.",
        "err_missing_block": "Internal error: block {name} was expected but not found. "
                             "Nothing was written.",
        "err_no_cues": "STOP — no subtitle blocks (cues) found in {path}.\n"
                       "Nothing was written.",
        "err_zero_duration": "STOP — the total spoken duration in {path} is zero.\n"
                             "Cannot compute a ratio. Nothing was written.",
        "ask_overwrite": "{path} already exists. Overwrite? [y/n] ",
        "aborted": "Aborted. Nothing was written.",
        "out_written": "Done. Adjusted files written:\n  {a}\n  {b}",
        "selftest": "Self-test:",
        "st_orig_first":  "Original total of first file:   {v:.2f} s",
        "st_orig_second": "Original total of second file:  {v:.2f} s",
        "st_adj_first":   "Adjusted total of first file:   {v:.2f} s",
        "st_adj_second":  "Adjusted total of second file:  {v:.2f} s",
    },
    "de": {
        "ask_first":  "Pfad zur ERSTEN .vtt-Datei eingeben (z. B. Deutsch): ",
        "ask_second": "Pfad zur ZWEITEN .vtt-Datei eingeben (z. B. Englisch): ",
        "blocks_counted": "{code}: {n} Blöcke gezählt",
        "count_first":  "Blöcke in der ersten Datei:  {n}",
        "count_second": "Blöcke in der zweiten Datei: {n}",
        "err_not_found": "Datei nicht gefunden: {path}\n"
                         "Prüfe den Pfad (zieh die Datei ins Terminal, dann stimmt er).",
        "err_decode":  "{path} konnte nicht als UTF-8 gelesen werden.\n"
                       "Exportiere die Untertitel als UTF-8 und versuche es erneut.",
        "err_timestamp": "Ein Zeitstempel in {path} konnte nicht gelesen werden.\n"
                         "Betroffene Zeile: {line}\n"
                         "Erwartetes Format: 00:01:23.456 --> 00:01:25.789",
        "err_mismatch": "STOPP — die beiden Dateien haben UNTERSCHIEDLICH viele Blöcke "
                        "({a} vs. {b}).\n"
                        "Dieses Werkzeug braucht in beiden Sprachen die GLEICHE "
                        "Blockzahl (gleicher Text, gleiche Segmentierung).\n"
                        "Es wurde nichts geschrieben. Siehe README, Abschnitt "
                        "'Voraussetzungen'.",
        "err_missing_block": "Interner Fehler: Block {name} wurde erwartet, aber nicht "
                             "gefunden. Es wurde nichts geschrieben.",
        "err_no_cues": "STOPP — in {path} wurden keine Untertitel-Blöcke (Cues) gefunden.\n"
                       "Es wurde nichts geschrieben.",
        "err_zero_duration": "STOPP — die gesprochene Gesamtlänge in {path} ist null.\n"
                             "Kein Verhältnis berechenbar. Es wurde nichts geschrieben.",
        "ask_overwrite": "{path} existiert bereits. Überschreiben? [j/n] ",
        "aborted": "Abgebrochen. Es wurde nichts geschrieben.",
        "out_written": "Fertig. Angepasste Dateien geschrieben:\n  {a}\n  {b}",
        "selftest": "Selbsttest:",
        "st_orig_first":  "Original-Gesamtlänge erste Datei:   {v:.2f} s",
        "st_orig_second": "Original-Gesamtlänge zweite Datei:  {v:.2f} s",
        "st_adj_first":   "Angepasste Gesamtlänge erste Datei: {v:.2f} s",
        "st_adj_second":  "Angepasste Gesamtlänge zweite Datei:{v:.2f} s",
    },
}

# 18.10.2026 (Neo): Ja-Antworten pro Oberflächensprache für die Überschreib-Rückfrage.
YES_ANSWERS = {"en": ("y", "yes"), "de": ("j", "ja", "y", "yes")}


def msg(lang, key, **kw):
    return MESSAGES[lang][key].format(**kw)


def ask_yes_no(prompt, lang):
    # 18.10.2026 (Neo): Rückfrage y/n bzw. j/n; EOF (kein Terminal) zählt als Nein.
    try:
        answer = input(prompt).strip().lower()
    except EOFError:
        return False
    return answer in YES_ANSWERS[lang]


# --- I/O -------------------------------------------------------------------
def read_vtt(file_path, lang):
    path = file_path.strip('"').strip("'")
    try:
        # 18.10.2026 (Neo): utf-8-sig, damit eine BOM nicht vor "WEBVTT" im Kopf hängen bleibt.
        with open(path, "r", encoding="utf-8-sig") as file:
            return file.readlines()
    except FileNotFoundError:
        sys.exit(msg(lang, "err_not_found", path=path))
    except UnicodeDecodeError:
        sys.exit(msg(lang, "err_decode", path=path))


def write_vtt(lines, file_path, header_lines):
    # 18.10.2026 (Neo): Kopfzeilen der Quelldatei schreiben statt festem "WEBVTT/Kind: captions".
    with open(file_path.strip('"').strip("'"), "w", encoding="utf-8") as file:
        for line in header_lines:
            file.write(line + "\n")
        file.write("\n")
        for line in lines:
            file.write(line + "\n")


# --- Timestamp helpers (logic unchanged from 2024) -------------------------
# 18.10.2026 (Neo): HH:MM:SS.mmm oder MM:SS.mmm (VTT erlaubt beides); Komma als Dezimaltrenner toleriert.
TIMESTAMP_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{1,2})[.,](\d{1,3})$")

# 18.10.2026 (Neo): Cue-Zeitzeile per Regex – toleriert Tab/Mehrfach-Leerzeichen um den Pfeil
# und fängt die Cue-Settings hinter der Endzeit (z. B. "align:start position:0%") als Gruppe 3.
CUE_TIMING_RE = re.compile(
    r"^\s*((?:\d+:)?\d{1,2}:\d{1,2}[.,]\d{1,3})\s*-->\s*((?:\d+:)?\d{1,2}:\d{1,2}[.,]\d{1,3})"
    r"(?:\s+(.*?))?\s*$"
)


def parse_timestamp(timestamp):
    m = TIMESTAMP_RE.match(timestamp.strip())
    if not m:
        raise ValueError(f"bad timestamp: {timestamp!r}")
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2))
    seconds = int(m.group(3))
    millis = int(m.group(4).ljust(3, "0"))
    return hours * 3600 + minutes * 60 + seconds + millis / 1000.0


def format_timestamp(seconds):
    # 18.10.2026 (Neo): erst Gesamt-Millisekunden als int runden, dann zerlegen –
    # verhindert "60.000" Sekunden durch Rundung (z. B. bei 59.9995).
    total_ms = int(round(seconds * 1000))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{ms:03}"


def count_and_label_blocks(lines, lang_code, lang):
    block_count = 0
    blocks = []
    block_info = {}
    total_duration = 0.0
    current_block = []
    # 18.10.2026 (Neo): Kopfbereich (WEBVTT, Kind:, Language: ...) sammeln und bewahren.
    header_lines = []
    pending_identifier = None

    for i, line in enumerate(lines):
        text = line.strip()
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        if "-->" in line:
            if current_block:
                blocks.append(current_block)
                current_block = []
            block_count += 1
            block_name = f"{block_count}{lang_code}Q"
            current_block.append(block_name)
            current_block.append(text)

            # 18.10.2026 (Neo): Zerlegen der Zeitzeile jetzt im try-Block – kein Traceback mehr
            # bei Tab/Doppel-Leerzeichen; Settings werden unverändert mitgeführt.
            try:
                m = CUE_TIMING_RE.match(line)
                if not m:
                    raise ValueError(text)
                start, end = m.group(1), m.group(2)
                settings = (m.group(3) or "").strip()
                duration = parse_timestamp(end) - parse_timestamp(start)
            except (ValueError, IndexError):
                sys.exit(msg(lang, "err_timestamp", path=lang_code, line=text))
            total_duration += duration

            block_info[block_name] = {
                "start": start, "end": end, "duration": duration,
                "settings": settings, "identifier": pending_identifier,
            }
            pending_identifier = None
        elif text and "-->" in next_line and not (block_count == 0 and text.startswith("WEBVTT")):
            # 18.10.2026 (Neo): Cue-Identifier (nummerierte VTT): nicht-leere Zeile direkt vor
            # einer Zeitzeile. Gehört zum FOLGENDEN Block, nicht als Text an den vorherigen.
            pending_identifier = text
        elif block_count == 0:
            header_lines.append(text)
        else:
            current_block.append(text)

    if current_block:
        blocks.append(current_block)

    # 18.10.2026 (Neo): Kopf normalisieren – Leerzeilen am Rand weg, erste Zeile muss WEBVTT sein.
    while header_lines and header_lines[0] == "":
        header_lines.pop(0)
    while header_lines and header_lines[-1] == "":
        header_lines.pop()
    if not header_lines or not header_lines[0].startswith("WEBVTT"):
        header_lines.insert(0, "WEBVTT")

    print(msg(lang, "blocks_counted", code=lang_code, n=block_count))
    return header_lines, blocks, block_info, total_duration


def adjust_lengths(block_info, ratio):
    adjusted_block_info = {}
    for block_name, info in block_info.items():
        adjusted_duration = info["duration"] * ratio
        # 18.10.2026 (Neo): dict kopieren, damit settings/identifier erhalten bleiben.
        adjusted = dict(info)
        adjusted["end"] = format_timestamp(parse_timestamp(info["start"]) + adjusted_duration)
        adjusted["duration"] = adjusted_duration
        adjusted_block_info[block_name] = adjusted
    return adjusted_block_info


def create_adjusted_vtt(blocks, adjusted_block_info, lang_code, total_blocks, lang):
    adjusted_lines = []
    previous_end = 0.0

    for block_count in range(1, total_blocks + 1):
        block_name = f"{block_count}{lang_code}Q"
        if block_name not in adjusted_block_info:
            sys.exit(msg(lang, "err_missing_block", name=block_name))
        info = adjusted_block_info[block_name]

        # Anchor the first block at its original start; chain the rest.
        adjusted_start = (
            previous_end
            if previous_end != 0.0
            else parse_timestamp(info["start"])
        )
        adjusted_end = adjusted_start + info["duration"]
        previous_end = adjusted_end

        # 18.10.2026 (Neo): Identifier vor der Zeitzeile, Settings dahinter – beides unverändert.
        if info.get("identifier"):
            adjusted_lines.append(info["identifier"])
        timing = f"{format_timestamp(adjusted_start)} --> {format_timestamp(adjusted_end)}"
        if info.get("settings"):
            timing += " " + info["settings"]
        adjusted_lines.append(timing)

        for block in blocks:
            if block[0] == block_name:
                block_content = block[2:]
                while block_content and block_content[-1] == "":
                    block_content.pop()
                adjusted_lines.extend(block_content)
                break

        if block_count != total_blocks:
            adjusted_lines.append("")

    return adjusted_lines


def calculate_total_duration(block_info):
    return sum(info["duration"] for info in block_info.values())


def main():
    parser = argparse.ArgumentParser(
        prog="subtitle_sync.py",
        description=f"{__title__} ({__subtitle__}) {__version__} — synchronise "
                    "YouTube auto-timestamps of two language versions of the same video."
    )
    # 20.10.2026 (Neo): --version, damit der Name und die Nummer abfragbar sind
    # und nicht nur im Kopf stehen.
    parser.add_argument("--version", action="version",
                        version=f"{__title__} ({__subtitle__}) {__version__}")
    parser.add_argument(
        "--lang", choices=["de", "en"], default="en",
        help="Interface language for prompts and messages (default: en).",
    )
    # 18.10.2026 (Neo): optionale Pfade für nicht-interaktiven Lauf; ohne sie bleibt die Abfrage.
    parser.add_argument("--a", metavar="FILE", help="First .vtt file (skips the prompt).")
    parser.add_argument("--b", metavar="FILE", help="Second .vtt file (skips the prompt).")
    # 18.10.2026 (Neo): --force überschreibt vorhandene adjusted_*.vtt ohne Rückfrage.
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing adjusted_*.vtt files without asking.")
    args = parser.parse_args()
    lang = args.lang

    first_vtt = args.a.strip() if args.a else input(msg(lang, "ask_first")).strip()
    second_vtt = args.b.strip() if args.b else input(msg(lang, "ask_second")).strip()

    first_lines = read_vtt(first_vtt, lang)
    second_lines = read_vtt(second_vtt, lang)

    # Language codes A/B are just internal block labels (order-agnostic).
    first_header, first_blocks, first_info, total_first = count_and_label_blocks(first_lines, "A", lang)
    second_header, second_blocks, second_info, total_second = count_and_label_blocks(second_lines, "B", lang)

    n_first, n_second = len(first_info), len(second_info)
    print(msg(lang, "count_first", n=n_first))
    print(msg(lang, "count_second", n=n_second))

    # 18.10.2026 (Neo): leere Dateien / Null-Gesamtlänge klar abfangen statt ZeroDivisionError.
    if n_first == 0:
        sys.exit(msg(lang, "err_no_cues", path=first_vtt))
    if n_second == 0:
        sys.exit(msg(lang, "err_no_cues", path=second_vtt))

    # SAFETY: equal block count is the precondition for block-to-block mapping.
    if n_first != n_second:
        sys.exit(msg(lang, "err_mismatch", a=n_first, b=n_second))

    if total_first <= 0:
        sys.exit(msg(lang, "err_zero_duration", path=first_vtt))
    if total_second <= 0:
        sys.exit(msg(lang, "err_zero_duration", path=second_vtt))

    first_to_second = total_first / total_second
    second_to_first = total_second / total_first

    adjusted_second_info = adjust_lengths(second_info, first_to_second)
    adjusted_first_info = adjust_lengths(first_info, second_to_first)

    adjusted_second_lines = create_adjusted_vtt(second_blocks, adjusted_second_info, "B", n_second, lang)
    adjusted_first_lines = create_adjusted_vtt(first_blocks, adjusted_first_info, "A", n_first, lang)

    first_folder = os.path.dirname(first_vtt.strip('"').strip("'"))
    second_folder = os.path.dirname(second_vtt.strip('"').strip("'"))
    first_base = os.path.splitext(os.path.basename(first_vtt.strip('"').strip("'")))[0]
    second_base = os.path.splitext(os.path.basename(second_vtt.strip('"').strip("'")))[0]
    out_first = os.path.join(first_folder, f"adjusted_{first_base}.vtt")
    out_second = os.path.join(second_folder, f"adjusted_{second_base}.vtt")

    # 18.10.2026 (Neo): vorhandene Ausgabedateien nur nach Rückfrage überschreiben (außer --force).
    if not args.force:
        for out_path in (out_first, out_second):
            if os.path.exists(out_path):
                if not ask_yes_no(msg(lang, "ask_overwrite", path=out_path), lang):
                    sys.exit(msg(lang, "aborted"))

    write_vtt(adjusted_first_lines, out_first, first_header)
    write_vtt(adjusted_second_lines, out_second, second_header)

    print()
    print(msg(lang, "selftest"))
    print(msg(lang, "st_orig_first", v=total_first))
    print(msg(lang, "st_orig_second", v=total_second))
    print(msg(lang, "st_adj_first", v=calculate_total_duration(adjusted_first_info)))
    print(msg(lang, "st_adj_second", v=calculate_total_duration(adjusted_second_info)))
    print()
    print(msg(lang, "out_written", a=out_first, b=out_second))


if __name__ == "__main__":
    main()

# Lamarr (SubtitleSync) 1.2.0

*Synchronise the YouTube auto-generated timestamps of two language versions of
the **same** video, so the subtitles of one language fit the runtime of the
other.* Until 20 October 2026 this file was titled "SubtitleSync"; the tool now
carries the name of its folder, like every other house here. `--version` prints
name and version.

Built 2024 in a project workshop by Christian "Nemesus" Ermisch with four AI
instances from different houses (an earlier Claude, ChatGPT, Gemini, and Grok —
who found the last bug). Updated 2026 by Claude (Anthropic): bilingual
interface, input validation, friendlier errors. The synchronisation logic is
unchanged — it was right.

---

## English

### What it does
You have one video in two languages (e.g. German and English), each with its
own audio track of a **different length**. YouTube generates timestamps per
language, so the English subtitles do not fit the German video and vice versa.
This tool takes the timestamps of one language and stretches/compresses them by
a single global factor (the ratio of the two total durations) so they fit the
other video. The first block is anchored, so both versions start at the same
point.

### Two preconditions (important — these are the whole trick)
1. **Same text, same number of blocks** in both languages. The tool maps block
   1 ↔ block 1, block 2 ↔ block 2, and so on. If the two files have a different
   number of blocks, it stops and writes nothing (it tells you the counts).
2. **Trim lead-in and lead-out.** Make sure both subtitle tracks **begin at the
   first spoken word and end at the last** — no intro music, no trailing
   silence. Only spoken content should be measured. This is why the single
   global factor is exact for this workflow: same text, evenly different
   speaking speed.

If you ignore precondition 2, the anchor and the factor are computed from dead
time at the edges, and the result drifts.

### How I (Nemesus) use it — an example
The specific tools are mine; swap in your own. What matters is the *shape*:
same text, two audio tracks, YouTube auto-timestamps per language.
1. Write a voice-over in my native language (German); refine it with an AI.
2. Have it translated (e.g. by an AI) until the English version is good.
3. Record the German track myself; remove breaths/pauses; run an audio AI over it.
4. Generate the English track with a cloned voice (e.g. ElevenLabs).
5. German video → German track; English video → English track. Render, upload.
6. Give each channel its text; **YouTube generates the timestamps**.
7. Run this script over the two timestamp files.
8. Open a second subtitle language on each channel and upload the adjusted file.

### Usage
```
python3 subtitle_sync.py            # English interface (default)
python3 subtitle_sync.py --lang de  # German interface
```
It then asks for the two file paths (tip: drag the file into the terminal to
get the path right). It writes `adjusted_<name>.vtt` next to each source file
and prints a self-test comparing original and adjusted total durations.

### Limits (honest)
This is **not** a general subtitle translator. It applies **one global factor**
to all blocks and anchors the first one. That is exact when the two tracks are
the same text spoken at an evenly different speed (e.g. a cloned TTS voice). For
**independently timed** subtitles, where blocks drift against each other, the
result will be off. Use it for the workflow above, not beyond it.

Requirements: Python 3, UTF-8 `.vtt` files. No external packages.

---

## Deutsch

### Was es tut
Du hast ein Video in zwei Sprachen (z. B. Deutsch und Englisch), jede mit einer
eigenen Tonspur **unterschiedlicher Länge**. YouTube erzeugt die Zeitstempel
pro Sprache, also passen die englischen Untertitel nicht aufs deutsche Video
und umgekehrt. Dieses Werkzeug nimmt die Zeitstempel der einen Sprache und
streckt/staucht sie mit einem einzigen globalen Faktor (dem Verhältnis der
beiden Gesamtlängen) auf das andere Video. Der erste Block wird verankert, also
starten beide Fassungen am selben Punkt.

### Zwei Voraussetzungen (wichtig — das ist der ganze Trick)
1. **Gleicher Text, gleiche Blockzahl** in beiden Sprachen. Das Werkzeug ordnet
   Block 1 ↔ Block 1, Block 2 ↔ Block 2 usw. zu. Haben die Dateien
   unterschiedlich viele Blöcke, stoppt es und schreibt nichts (es nennt dir
   die Zahlen).
2. **Vorlauf und Nachlauf abschneiden.** Sorge dafür, dass beide
   Untertitelspuren **beim ersten gesprochenen Wort beginnen und beim letzten
   enden** — keine Intro-Musik, keine Stille am Ende. Nur gesprochener Inhalt
   wird gemessen. Genau deshalb ist der eine globale Faktor für diesen Workflow
   exakt: gleicher Text, gleichmäßig andere Sprechgeschwindigkeit.

Ignorierst du Voraussetzung 2, werden Anker und Faktor aus toter Randzeit
berechnet, und das Ergebnis driftet.

### Wie ich (Nemesus) es nutze — ein Beispiel
Die konkreten Werkzeuge sind meine; nimm deine eigenen. Wichtig ist die *Form*:
gleicher Text, zwei Tonspuren, YouTube-Auto-Zeitstempel pro Sprache.
1. Voice-Over in der Muttersprache (Deutsch) schreiben; mit einer KI verfeinern.
2. Übersetzen lassen (z. B. von einer KI), bis die englische Fassung passt.
3. Deutsche Spur selbst einlesen; Atem/Pausen entfernen; Audio-KI drüberlaufen lassen.
4. Englische Spur mit geklonter Stimme erzeugen (z. B. ElevenLabs).
5. Deutsches Video → deutsche Spur; englisches Video → englische Spur. Rendern, hochladen.
6. Jedem Kanal seinen Text geben; **YouTube erzeugt die Zeitstempel**.
7. Dieses Skript über die zwei Zeitstempel-Dateien laufen lassen.
8. Pro Kanal eine zweite Untertitelsprache anlegen und die angepasste Datei hochladen.

### Bedienung
```
python3 subtitle_sync.py            # englische Oberfläche (Standard)
python3 subtitle_sync.py --lang de  # deutsche Oberfläche
```
Es fragt dann nach den zwei Dateipfaden (Tipp: zieh die Datei ins Terminal,
dann stimmt der Pfad). Es schreibt `adjusted_<name>.vtt` neben jede Quelldatei
und gibt einen Selbsttest aus, der Original- und angepasste Gesamtlänge
vergleicht.

### Grenzen (ehrlich)
Das ist **kein** allgemeiner Untertitel-Übersetzer. Es wendet **einen globalen
Faktor** auf alle Blöcke an und verankert den ersten. Das ist exakt, wenn die
zwei Spuren derselbe Text in gleichmäßig anderer Geschwindigkeit sind (z. B.
eine geklonte TTS-Stimme). Für **unabhängig getimte** Untertitel, deren Blöcke
gegeneinander driften, wird das Ergebnis ungenau. Nutze es für den obigen
Workflow, nicht darüber hinaus.

Voraussetzungen: Python 3, UTF-8-`.vtt`-Dateien. Keine externen Pakete.

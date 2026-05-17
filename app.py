import io
import re
import zipfile
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

import pandas as pd
import streamlit as st


# =========================
# App config
# =========================

st.set_page_config(
    page_title="EndNote to Excel Converter",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0f; color: #e8e6e0; font-family: 'Syne', sans-serif;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 90% 45% at 15% -5%, rgba(255,140,50,0.10) 0%, transparent 60%),
        radial-gradient(ellipse 70% 40% at 85% 105%, rgba(255,80,30,0.07) 0%, transparent 55%),
        #0a0a0f;
}
[data-testid="stHeader"], [data-testid="stToolbar"],
#MainMenu, footer { display: none !important; visibility: hidden !important; }

.block-container { max-width: 1100px; padding: 3rem 2.5rem 5rem; }

/* ── Hero ──────────────────────────────────────── */
.hero { padding: 2.8rem 0 2rem; }
.hero-badge {
    display: inline-block; font-family: 'DM Mono', monospace;
    font-size: 0.68rem; letter-spacing: 0.22em; color: #ff8c32;
    border: 1px solid rgba(255,140,50,0.3); border-radius: 2px;
    padding: 0.28rem 0.9rem; margin-bottom: 1.1rem; text-transform: uppercase;
}
.hero h1 {
    font-size: clamp(2.2rem, 5vw, 3.2rem); font-weight: 800;
    line-height: 1.06; letter-spacing: -0.03em;
    background: linear-gradient(135deg, #fff 40%, #ff8c32 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.8rem;
}
.hero p {
    color: rgba(232,230,224,0.45); font-size: 0.93rem;
    font-family: 'DM Mono', monospace; line-height: 1.8; max-width: 640px;
}
.hero p strong { color: #ff8c32; -webkit-text-fill-color: #ff8c32; }

/* ── Divider ───────────────────────────────────── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,140,50,0.22), transparent);
    margin: 1.8rem 0;
}

/* ── Section label ─────────────────────────────── */
.section-label {
    font-family: 'DM Mono', monospace; font-size: 0.67rem;
    letter-spacing: 0.2em; color: rgba(232,230,224,0.32);
    text-transform: uppercase; margin-bottom: 0.65rem;
}

/* ── File uploader ─────────────────────────────── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 1.2rem 1.5rem !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(255,140,50,0.38) !important;
    box-shadow: 0 0 28px rgba(255,140,50,0.07) !important;
}
[data-testid="stFileUploaderDropzone"] { background: transparent !important; }
[data-testid="stFileUploaderDropzone"] > div,
[data-testid="stFileUploader"] label {
    color: rgba(232,230,224,0.38) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: rgba(232,230,224,0.22) !important;
}

/* ── Status box (HTML) ─────────────────────────── */
.status-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 1.1rem 1.3rem;
}
.status-label {
    color: rgba(232,230,224,0.36); font-size: 0.66rem;
    letter-spacing: 0.16em; text-transform: uppercase;
    font-family: 'DM Mono', monospace; margin-bottom: 0.35rem;
}
.status-value {
    color: #e8e6e0; font-size: 0.88rem; font-family: 'DM Mono', monospace;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.status-value.accent { color: #ff8c32; font-size: 1.25rem; font-weight: 500; }

/* ── Spinner ───────────────────────────────────── */
[data-testid="stSpinner"] > div > div { border-top-color: #ff8c32 !important; }
[data-testid="stSpinner"] p {
    color: rgba(232,230,224,0.42) !important;
    font-family: 'DM Mono', monospace !important; font-size: 0.8rem !important;
}

/* ── Alert boxes ───────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important; border-left-width: 3px !important;
    font-family: 'DM Mono', monospace !important; font-size: 0.82rem !important;
}
.stSuccess { background: rgba(93,222,138,0.07)  !important; border-color: #5dde8a !important; color: #9af0ba !important; }
.stWarning { background: rgba(255,193,50,0.07)  !important; border-color: #ffc132 !important; color: #ffe08a !important; }
.stError   { background: rgba(255,85,85,0.07)   !important; border-color: #ff5555 !important; color: #ffaaaa !important; }
.stInfo    { background: rgba(255,140,50,0.06)  !important; border-color: rgba(255,140,50,0.4) !important; color: #ffc891 !important; }

/* ── Success banner ────────────────────────────── */
.result-banner {
    background: linear-gradient(135deg, rgba(93,222,138,0.08), rgba(93,222,138,0.02));
    border: 1px solid rgba(93,222,138,0.2); border-radius: 12px;
    padding: 1.6rem 1.8rem; text-align: center; margin: 0.8rem 0 1.2rem;
}
.result-banner h3 { font-size: 1.1rem; font-weight: 700; color: #5dde8a; margin-bottom: 0.25rem; }
.result-banner p  { color: rgba(232,230,224,0.42); font-family: 'DM Mono', monospace; font-size: 0.76rem; }
.result-banner-err {
    background: linear-gradient(135deg, rgba(255,85,85,0.08), rgba(255,85,85,0.02));
    border: 1px solid rgba(255,85,85,0.2); border-radius: 12px;
    padding: 1.3rem 1.6rem; margin: 0.8rem 0 1.2rem;
}
.result-banner-err p { color: rgba(255,170,170,0.8); font-family: 'DM Mono', monospace; font-size: 0.82rem; }

/* ── Tabs ──────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    gap: 0 !important; border-bottom: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stTabs"] [role="tab"] {
    background: transparent !important; border: none !important;
    color: rgba(232,230,224,0.36) !important; font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important; font-size: 0.87rem !important;
    padding: 0.6rem 1.25rem !important; transition: color 0.2s !important;
}
[data-testid="stTabs"] [role="tab"]:hover { color: rgba(232,230,224,0.72) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #ff8c32 !important; border-bottom: 2px solid #ff8c32 !important;
}
[data-testid="stTabContent"] {
    background: rgba(255,255,255,0.018) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-top: none !important; border-radius: 0 0 10px 10px !important;
    padding: 1.4rem !important;
}

/* ── DataFrame ─────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important; overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
}

/* ── Expander ──────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(0,0,0,0.22) !important;
    border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'DM Mono', monospace !important; font-size: 0.78rem !important;
    color: rgba(232,230,224,0.36) !important;
}
[data-testid="stExpander"] summary:hover { color: rgba(232,230,224,0.68) !important; }

/* ── Download button ───────────────────────────── */
[data-testid="stDownloadButton"] button {
    width: 100% !important;
    background: rgba(255,140,50,0.10) !important; color: #ff8c32 !important;
    border: 1px solid rgba(255,140,50,0.30) !important; border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 0.92rem !important; padding: 0.75rem 2rem !important;
    transition: background 0.2s, box-shadow 0.2s, transform 0.2s !important;
    margin-top: 1rem !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(255,140,50,0.18) !important;
    box-shadow: 0 0 24px rgba(255,140,50,0.18) !important;
    transform: translateY(-1px) !important;
}

/* ── Scrollbar ─────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,140,50,0.38); }

/* ── Column gap ────────────────────────────────── */
[data-testid="stHorizontalBlock"] { gap: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)


REFERENCE_COLUMNS = [
    "record_number",
    "reference_type",
    "title",
    "authors",
    "year",
    "journal",
    "secondary_title",
    "publisher",
    "place_published",
    "volume",
    "issue",
    "pages",
    "doi",
    "url",
    "abstract",
    "keywords",
    "isbn_issn",
    "notes",
    "source_file"
]


# =========================
# Utility functions
# =========================

def clean_text(value):
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_xml_namespace(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def element_text(element):
    if element is None:
        return ""
    return clean_text(" ".join(element.itertext()))


def find_first_text(record, possible_paths):
    for path in possible_paths:
        found = record.find(path)
        if found is not None:
            txt = element_text(found)
            if txt:
                return txt
    return ""


def find_all_texts(record, possible_paths):
    values = []
    for path in possible_paths:
        for found in record.findall(path):
            txt = element_text(found)
            if txt:
                values.append(txt)
    return values


def dedupe_keep_order(values):
    seen = set()
    out = []
    for v in values:
        v = clean_text(v)
        if not v:
            continue
        key = v.lower()
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def safe_extract_zip(zip_path, extract_dir):
    """
    Extract ZIP safely, avoiding path traversal.
    """
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            member_name = member.filename.replace("\\", "/")
            if member_name.startswith("/") or ".." in Path(member_name).parts:
                continue

            target_path = extract_dir / member_name
            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as src, open(target_path, "wb") as dst:
                dst.write(src.read())

            extracted.append(target_path)

    return extracted


def read_text_file(path):
    data = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "latin-1"]:
        try:
            return data.decode(enc)
        except Exception:
            pass
    return data.decode("latin-1", errors="ignore")


def looks_like_xml(path):
    try:
        txt = read_text_file(path)[:1000].lstrip()
        return txt.startswith("<?xml") or txt.startswith("<")
    except Exception:
        return False


def looks_like_ris_text(text):
    sample = text[:5000]
    return bool(re.search(r"(?m)^TY\s+-\s+", sample)) and bool(re.search(r"(?m)^ER\s+-\s*", sample))


def looks_like_ris(path):
    try:
        return looks_like_ris_text(read_text_file(path))
    except Exception:
        return False


def file_size_text(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


# =========================
# EndNote XML parser
# =========================

def parse_endnote_xml_file(path):
    """
    Parse EndNote XML export.
    This is the most stable route.
    """
    records = []

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return [], f"XML parse error: {e}"

    all_records = []
    for elem in root.iter():
        if strip_xml_namespace(elem.tag).lower() == "record":
            all_records.append(elem)

    for idx, rec in enumerate(all_records, start=1):
        # record number
        rec_num = find_first_text(rec, [
            ".//rec-number",
            ".//record-number"
        ]) or str(idx)

        # reference type
        ref_type = ""
        for elem in rec.iter():
            tag = strip_xml_namespace(elem.tag).lower()
            if tag == "ref-type":
                ref_type = elem.attrib.get("name") or element_text(elem)
                break

        # title
        title = find_first_text(rec, [
            ".//titles/title",
            ".//title",
            ".//primary-title",
        ])

        # authors
        authors = find_all_texts(rec, [
            ".//contributors/authors/author",
            ".//authors/author",
            ".//author",
            ".//contributors/secondary-authors/author",
        ])
        authors = dedupe_keep_order(authors)

        # year
        year = find_first_text(rec, [
            ".//dates/year",
            ".//year",
        ])

        # journal / secondary title
        journal = find_first_text(rec, [
            ".//titles/secondary-title",
            ".//secondary-title",
            ".//periodical/full-title",
            ".//full-title",
        ])

        secondary_title = journal

        publisher = find_first_text(rec, [
            ".//publisher",
            ".//pub-location",
        ])

        place_published = find_first_text(rec, [
            ".//pub-location",
            ".//place-published",
        ])

        volume = find_first_text(rec, [
            ".//volume",
        ])

        issue = find_first_text(rec, [
            ".//number",
            ".//issue",
        ])

        pages = find_first_text(rec, [
            ".//pages",
        ])

        doi = find_first_text(rec, [
            ".//electronic-resource-num",
            ".//doi",
        ])

        url = find_first_text(rec, [
            ".//urls/related-urls/url",
            ".//urls/pdf-urls/url",
            ".//url",
        ])

        abstract = find_first_text(rec, [
            ".//abstract",
        ])

        keywords = find_all_texts(rec, [
            ".//keywords/keyword",
            ".//keyword",
        ])
        keywords = dedupe_keep_order(keywords)

        isbn_issn = find_first_text(rec, [
            ".//isbn",
            ".//issn",
        ])

        notes = find_first_text(rec, [
            ".//notes",
            ".//research-notes",
        ])

        records.append({
            "record_number": rec_num,
            "reference_type": clean_text(ref_type),
            "title": title,
            "authors": "; ".join(authors),
            "year": year,
            "journal": journal,
            "secondary_title": secondary_title,
            "publisher": publisher,
            "place_published": place_published,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "doi": doi,
            "url": url,
            "abstract": abstract,
            "keywords": "; ".join(keywords),
            "isbn_issn": isbn_issn,
            "notes": notes,
            "source_file": str(path.name)
        })

    return records, ""


# =========================
# RIS parser
# =========================

RIS_TAG_MAP = {
    "TY": "reference_type",
    "TI": "title",
    "T1": "title",
    "CT": "title",
    "AU": "authors",
    "A1": "authors",
    "A2": "secondary_authors",
    "PY": "year",
    "Y1": "year",
    "DA": "date",
    "JO": "journal",
    "JF": "journal",
    "JA": "journal",
    "T2": "secondary_title",
    "VL": "volume",
    "IS": "issue",
    "SP": "start_page",
    "EP": "end_page",
    "PG": "pages",
    "DO": "doi",
    "UR": "url",
    "AB": "abstract",
    "N2": "abstract",
    "KW": "keywords",
    "PB": "publisher",
    "CY": "place_published",
    "SN": "isbn_issn",
    "N1": "notes",
}


def parse_ris_text(text, source_file="uploaded.ris"):
    records = []
    current = {}

    def push_current():
        if not current:
            return

        authors = current.get("authors", [])
        keywords = current.get("keywords", [])

        year = ""
        year_values = current.get("year", [])
        if year_values:
            match = re.search(r"\d{4}", year_values[0])
            year = match.group(0) if match else clean_text(year_values[0])

        pages = ""
        if current.get("pages"):
            pages = clean_text(current["pages"][0])
        else:
            sp = clean_text(current.get("start_page", [""])[0]) if current.get("start_page") else ""
            ep = clean_text(current.get("end_page", [""])[0]) if current.get("end_page") else ""
            if sp and ep:
                pages = f"{sp}-{ep}"
            else:
                pages = sp or ep

        row = {
            "record_number": str(len(records) + 1),
            "reference_type": clean_text(current.get("reference_type", [""])[0]) if current.get("reference_type") else "",
            "title": clean_text(current.get("title", [""])[0]) if current.get("title") else "",
            "authors": "; ".join(dedupe_keep_order(authors)),
            "year": year,
            "journal": clean_text(current.get("journal", [""])[0]) if current.get("journal") else "",
            "secondary_title": clean_text(current.get("secondary_title", [""])[0]) if current.get("secondary_title") else "",
            "publisher": clean_text(current.get("publisher", [""])[0]) if current.get("publisher") else "",
            "place_published": clean_text(current.get("place_published", [""])[0]) if current.get("place_published") else "",
            "volume": clean_text(current.get("volume", [""])[0]) if current.get("volume") else "",
            "issue": clean_text(current.get("issue", [""])[0]) if current.get("issue") else "",
            "pages": pages,
            "doi": clean_text(current.get("doi", [""])[0]) if current.get("doi") else "",
            "url": clean_text(current.get("url", [""])[0]) if current.get("url") else "",
            "abstract": clean_text(current.get("abstract", [""])[0]) if current.get("abstract") else "",
            "keywords": "; ".join(dedupe_keep_order(keywords)),
            "isbn_issn": clean_text(current.get("isbn_issn", [""])[0]) if current.get("isbn_issn") else "",
            "notes": clean_text(current.get("notes", [""])[0]) if current.get("notes") else "",
            "source_file": source_file
        }
        records.append(row)

    last_tag = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n\r")

        tag_match = re.match(r"^([A-Z0-9]{2})\s+-\s?(.*)$", line)
        if tag_match:
            tag = tag_match.group(1)
            value = clean_text(tag_match.group(2))

            if tag == "TY":
                current = {}

            if tag == "ER":
                push_current()
                current = {}
                last_tag = None
                continue

            field = RIS_TAG_MAP.get(tag)
            if field:
                current.setdefault(field, []).append(value)
                last_tag = field
            else:
                last_tag = None
        else:
            # Continuation line
            if last_tag and current.get(last_tag):
                current[last_tag][-1] = clean_text(current[last_tag][-1] + " " + line)

    if current:
        push_current()

    return records


def parse_ris_file(path):
    try:
        text = read_text_file(path)
        return parse_ris_text(text, source_file=str(path.name)), ""
    except Exception as e:
        return [], f"RIS parse error: {e}"


# =========================
# SQLite / ENI best-effort inspection
# =========================

def inspect_sqlite_file(path, max_tables=30):
    """
    This does not guarantee EndNote citation extraction.
    It only checks whether .eni/.enl behaves like SQLite.
    """
    info = {
        "file": str(path.name),
        "is_sqlite": False,
        "tables": [],
        "error": ""
    }

    try:
        con = sqlite3.connect(str(path))
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT ?", (max_tables,))
        tables = [r[0] for r in cur.fetchall()]
        info["tables"] = tables
        info["is_sqlite"] = len(tables) > 0
        con.close()
    except Exception as e:
        info["error"] = str(e)

    return info


def try_extract_sqlite_reference_like_tables(path):
    """
    Experimental fallback:
    If a file is SQLite and has tables with title/author/year/doi-like columns,
    extract rows into a unified DataFrame.

    This is best-effort only.
    """
    rows = []

    try:
        con = sqlite3.connect(str(path))
        cur = con.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]

        for table in tables:
            try:
                cur.execute(f"PRAGMA table_info([{table}])")
                columns = [r[1] for r in cur.fetchall()]
                lower_cols = [c.lower() for c in columns]

                interesting = any(
                    token in " ".join(lower_cols)
                    for token in ["title", "author", "year", "doi", "journal", "abstract", "keyword"]
                )

                if not interesting:
                    continue

                cur.execute(f"SELECT * FROM [{table}] LIMIT 5000")
                data = cur.fetchall()

                for row in data:
                    item = dict(zip(columns, row))
                    lower_item = {k.lower(): v for k, v in item.items()}

                    def pick(*names):
                        for name in names:
                            for k, v in lower_item.items():
                                if name in k and v not in [None, ""]:
                                    return clean_text(v)
                        return ""

                    extracted = {
                        "record_number": "",
                        "reference_type": "",
                        "title": pick("title"),
                        "authors": pick("author", "authors", "contributor"),
                        "year": pick("year", "date"),
                        "journal": pick("journal", "secondary", "periodical"),
                        "secondary_title": pick("secondary"),
                        "publisher": pick("publisher"),
                        "place_published": pick("place"),
                        "volume": pick("volume"),
                        "issue": pick("issue", "number"),
                        "pages": pick("pages"),
                        "doi": pick("doi", "electronic"),
                        "url": pick("url"),
                        "abstract": pick("abstract"),
                        "keywords": pick("keyword"),
                        "isbn_issn": pick("isbn", "issn"),
                        "notes": pick("note"),
                        "source_file": f"{path.name} :: table {table}"
                    }

                    if any(extracted.get(c, "") for c in ["title", "authors", "doi", "journal"]):
                        rows.append(extracted)

            except Exception:
                continue

        con.close()
    except Exception:
        pass

    for i, row in enumerate(rows, start=1):
        row["record_number"] = str(i)

    return rows


# =========================
# Raw binary text fallback
# =========================

def extract_possible_dois_from_binary(path):
    try:
        data = path.read_bytes()
        text = data.decode("latin-1", errors="ignore")
        dois = re.findall(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, flags=re.I)
        return dedupe_keep_order(dois)
    except Exception:
        return []


# =========================
# Main processing
# =========================

def process_uploaded_file(uploaded_file):
    diagnostics = []
    file_structure_rows = []
    all_records = []

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        uploaded_path = tmpdir / uploaded_file.name
        uploaded_path.write_bytes(uploaded_file.getbuffer())

        suffix = uploaded_path.suffix.lower()

        workdir = tmpdir / "work"
        workdir.mkdir(parents=True, exist_ok=True)

        # Step 1: extract or copy
        candidate_files = []

        if suffix in [".enlx", ".zip"] or zipfile.is_zipfile(uploaded_path):
            try:
                extracted = safe_extract_zip(uploaded_path, workdir)
                candidate_files = extracted
                diagnostics.append({
                    "level": "info",
                    "message": f"Đã giải nén {len(extracted)} file từ {uploaded_file.name}."
                })
            except Exception as e:
                diagnostics.append({
                    "level": "error",
                    "message": f"Không giải nén được file: {e}"
                })
                candidate_files = [uploaded_path]
        else:
            copied = workdir / uploaded_path.name
            copied.write_bytes(uploaded_path.read_bytes())
            candidate_files = [copied]
            diagnostics.append({
                "level": "info",
                "message": "File không phải ZIP/ENLX nén. Sẽ thử đọc trực tiếp."
            })

        # Step 2: file structure
        for p in sorted(workdir.rglob("*")):
            if p.is_file():
                rel = str(p.relative_to(workdir)).replace("\\", "/")
                file_structure_rows.append({
                    "path": rel,
                    "extension": p.suffix.lower(),
                    "size_bytes": p.stat().st_size,
                    "size": file_size_text(p.stat().st_size)
                })

        all_paths = [p for p in workdir.rglob("*") if p.is_file()]
        rel_paths = [str(p.relative_to(workdir)).replace("\\", "/") for p in all_paths]

        has_enl = any(p.suffix.lower() == ".enl" for p in all_paths)
        has_xml = any(p.suffix.lower() == ".xml" for p in all_paths)
        has_ris = any(p.suffix.lower() in [".ris", ".txt"] and looks_like_ris(p) for p in all_paths)
        has_sdb = any("/sdb/" in f"/{r.lower()}" or r.lower().startswith("sdb/") for r in rel_paths)
        has_pdf_folder = any("/pdf/" in f"/{r.lower()}" or r.lower().startswith("pdf/") for r in rel_paths)
        eni_files = [p for p in all_paths if p.suffix.lower() == ".eni"]
        pdf_files = [p for p in all_paths if p.suffix.lower() == ".pdf"]

        if has_enl:
            diagnostics.append({
                "level": "info",
                "message": "Có file .enl. Tuy nhiên .enl là định dạng proprietary/binary, Python thường không đọc citation trực tiếp ổn định nếu không có export XML/RIS."
            })

        if has_sdb or eni_files:
            diagnostics.append({
                "level": "warning",
                "message": "Phát hiện cấu trúc nội bộ EndNote như sdb/ hoặc .eni. Đây có thể là dữ liệu EndNote, nhưng không phải format export citation chuẩn."
            })

        if has_pdf_folder or pdf_files:
            diagnostics.append({
                "level": "info",
                "message": f"Phát hiện {len(pdf_files)} file PDF đính kèm. PDF không đảm bảo chứa đủ metadata citation như author/year/journal/DOI."
            })

        # Step 3: parse XML files
        xml_candidates = [p for p in all_paths if p.suffix.lower() == ".xml" or looks_like_xml(p)]
        for p in xml_candidates:
            records, err = parse_endnote_xml_file(p)
            if records:
                all_records.extend(records)
                diagnostics.append({
                    "level": "success",
                    "message": f"Đọc được {len(records)} references từ XML: {p.name}"
                })
            elif err:
                diagnostics.append({
                    "level": "debug",
                    "message": f"Không parse được XML {p.name}: {err}"
                })

        # Step 4: parse RIS files
        ris_candidates = [
            p for p in all_paths
            if p.suffix.lower() in [".ris", ".txt", ".enw"] or looks_like_ris(p)
        ]

        for p in ris_candidates:
            records, err = parse_ris_file(p)
            if records:
                all_records.extend(records)
                diagnostics.append({
                    "level": "success",
                    "message": f"Đọc được {len(records)} references từ RIS/Text export: {p.name}"
                })
            elif err:
                diagnostics.append({
                    "level": "debug",
                    "message": f"Không parse được RIS {p.name}: {err}"
                })

        # Step 5: inspect ENI / ENL as SQLite
        sqlite_infos = []
        sqlite_candidates = eni_files + [p for p in all_paths if p.suffix.lower() == ".enl"]

        for p in sqlite_candidates:
            info = inspect_sqlite_file(p)
            sqlite_infos.append(info)

            if info["is_sqlite"]:
                diagnostics.append({
                    "level": "info",
                    "message": f"{p.name} có vẻ là SQLite. Tables: {', '.join(info['tables'][:10])}"
                })

                sqlite_rows = try_extract_sqlite_reference_like_tables(p)
                if sqlite_rows:
                    all_records.extend(sqlite_rows)
                    diagnostics.append({
                        "level": "success",
                        "message": f"Thử nghiệm đọc được {len(sqlite_rows)} dòng giống citation từ SQLite file: {p.name}"
                    })
            else:
                if p.suffix.lower() == ".eni":
                    diagnostics.append({
                        "level": "debug",
                        "message": f"{p.name} không đọc được như SQLite."
                    })

        # Step 6: if no records, DOI fallback
        if not all_records:
            doi_rows = []
            for p in all_paths:
                if p.suffix.lower() in [".enl", ".eni", ".txt", ".ris", ".xml"]:
                    dois = extract_possible_dois_from_binary(p)
                    for doi in dois:
                        doi_rows.append({
                            "record_number": str(len(doi_rows) + 1),
                            "reference_type": "",
                            "title": "",
                            "authors": "",
                            "year": "",
                            "journal": "",
                            "secondary_title": "",
                            "publisher": "",
                            "place_published": "",
                            "volume": "",
                            "issue": "",
                            "pages": "",
                            "doi": doi,
                            "url": "",
                            "abstract": "",
                            "keywords": "",
                            "isbn_issn": "",
                            "notes": "Fallback: DOI found in raw binary/text. Other citation fields unavailable.",
                            "source_file": p.name
                        })

            if doi_rows:
                all_records.extend(doi_rows)
                diagnostics.append({
                    "level": "warning",
                    "message": f"Không đọc được citation đầy đủ, nhưng tìm thấy {len(doi_rows)} DOI trong dữ liệu thô."
                })

        # Step 7: final diagnostics
        if not all_records:
            diagnostics.append({
                "level": "error",
                "message": (
                    "Không trích được references đầy đủ. Khả năng cao file chỉ chứa EndNote library nội bộ "
                    "(.enl/.Data/sdb/.eni) chứ không chứa EndNote XML/RIS export. "
                    "Cách chắc chắn nhất: mở bằng EndNote → File → Export → chọn XML hoặc RIS → upload file XML/RIS đó vào app này."
                )
            })

        # Step 8: normalize DataFrame
        refs_df = pd.DataFrame(all_records)
        if refs_df.empty:
            refs_df = pd.DataFrame(columns=REFERENCE_COLUMNS)
        else:
            for col in REFERENCE_COLUMNS:
                if col not in refs_df.columns:
                    refs_df[col] = ""
            refs_df = refs_df[REFERENCE_COLUMNS]
            refs_df = refs_df.drop_duplicates()

        structure_df = pd.DataFrame(file_structure_rows)
        if structure_df.empty:
            structure_df = pd.DataFrame(columns=["path", "extension", "size_bytes", "size"])

        diagnostics_df = pd.DataFrame(diagnostics)
        if diagnostics_df.empty:
            diagnostics_df = pd.DataFrame(columns=["level", "message"])

        return refs_df, structure_df, diagnostics_df


def make_excel_bytes(refs_df, structure_df, diagnostics_df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        refs_df.to_excel(writer, index=False, sheet_name="References")
        structure_df.to_excel(writer, index=False, sheet_name="File_Structure")
        diagnostics_df.to_excel(writer, index=False, sheet_name="Diagnostics")

        # Basic formatting
        workbook = writer.book
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "A2"

            for col_cells in ws.columns:
                max_len = 12
                col_letter = col_cells[0].column_letter
                for cell in col_cells[:200]:
                    try:
                        value = str(cell.value) if cell.value is not None else ""
                        max_len = max(max_len, min(len(value), 60))
                    except Exception:
                        pass
                ws.column_dimensions[col_letter].width = max_len + 2

    output.seek(0)
    return output.getvalue()


# =========================
# Streamlit UI
# =========================

st.markdown("""
<div class="hero">
    <div class="hero-badge">📚 Citation Toolkit</div>
    <h1>EndNote → Excel<br>Converter</h1>
    <p>
        Upload file <strong>.enlx</strong>, <strong>.enl</strong>, <strong>.zip</strong>,
        <strong>.xml</strong>, <strong>.ris</strong> hoặc <strong>.txt</strong> export từ EndNote.<br>
        Nếu file chỉ chứa cấu trúc nội bộ <strong>sdb/</strong>, <strong>.eni</strong>, <strong>PDF/</strong>
        mà không có XML/RIS export, app có thể không đọc được đầy đủ citation.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-label">— Chọn file để bắt đầu</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Kéo thả hoặc click để chọn file EndNote",
    type=["enlx", "enl", "zip", "xml", "ris", "txt", "enw"],
    label_visibility="collapsed"
)

if uploaded_file:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="status-box">
            <div class="status-label">Tên file</div>
            <div class="status-value">{uploaded_file.name}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="status-box">
            <div class="status-label">Kích thước</div>
            <div class="status-value accent">{file_size_text(uploaded_file.size)}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="status-box">
            <div class="status-label">Thời điểm</div>
            <div class="status-value">{datetime.now().strftime("%H:%M:%S")}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("Đang phân tích và trích xuất citation…"):
        refs_df, structure_df, diagnostics_df = process_uploaded_file(uploaded_file)
        excel_bytes = make_excel_bytes(refs_df, structure_df, diagnostics_df)

    found_count = len(refs_df)
    if found_count > 0:
        st.markdown(f"""<div class="result-banner">
            <div style="font-size:1.8rem;margin-bottom:.3rem">✅</div>
            <h3>Hoàn thành!</h3>
            <p>Trích được <strong style="color:#5dde8a">{found_count}</strong> dòng reference/citation</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="result-banner-err">
            <p>❌ &nbsp;Chưa trích được citation đầy đủ từ file này.</p>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-label">— Xem dữ liệu</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📄  References", "🧪  Diagnostics", "🗂️  Cấu trúc file"])

    with tab1:
        st.dataframe(refs_df, use_container_width=True, height=440)

    with tab2:
        for _, row in diagnostics_df.iterrows():
            level = row.get("level", "info")
            msg = row.get("message", "")
            if level == "success":
                st.success(msg)
            elif level == "warning":
                st.warning(msg)
            elif level == "error":
                st.error(msg)
            elif level == "debug":
                with st.expander("🔍 Debug detail"):
                    st.code(msg, language=None)
            else:
                st.info(msg)
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(diagnostics_df, use_container_width=True)

    with tab3:
        st.dataframe(structure_df, use_container_width=True, height=420)

    st.download_button(
        label="⬇️  Tải xuống file Excel",
        data=excel_bytes,
        file_name=f"endnote_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

else:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 Upload file EndNote ở trên để bắt đầu trích xuất citation.")
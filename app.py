"""
EndNote ENLX → ENL Converter
Hỗ trợ 2 cấu trúc ENLX:
  - Chuẩn mới: chứa TenFile.enl trực tiếp
  - Chuẩn cũ:  chứa sdb/pdb.eni + sdb/sdb.eni + PDF/
    → pdb.eni được đổi tên thành TenFile.enl
    → PDF/ được đổi tên thành TenFile.Data/
"""

import streamlit as st
import zipfile
import os
import shutil
import tempfile
import io
from pathlib import Path

# ── Cấu hình trang ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EndNote ENLX → ENL Converter",
    page_icon="📚",
    layout="centered",
)

# ── CSS tùy chỉnh ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .stApp {
        background: #0d1117;
        color: #e6edf3;
    }

    /* Header */
    .hero {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        border-bottom: 1px solid #21262d;
        margin-bottom: 2rem;
    }
    .hero h1 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
        color: #58a6ff;
        letter-spacing: -0.5px;
        margin: 0 0 0.4rem;
    }
    .hero p {
        color: #8b949e;
        font-size: 0.9rem;
        margin: 0;
    }

    /* Info box */
    .info-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #58a6ff;
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-bottom: 1.5rem;
        font-size: 0.875rem;
        color: #8b949e;
        line-height: 1.6;
    }
    .info-box strong { color: #e6edf3; }
    .info-box code {
        background: #21262d;
        padding: 1px 5px;
        border-radius: 3px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.82rem;
        color: #79c0ff;
    }

    /* Upload zone */
    [data-testid="stFileUploader"] {
        border: 2px dashed #30363d !important;
        border-radius: 10px !important;
        background: #161b22 !important;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #58a6ff !important;
    }

    /* Success/Error boxes */
    .result-ok {
        background: #0d2818;
        border: 1px solid #2ea043;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        margin: 1rem 0;
    }
    .result-ok h4 { color: #3fb950; margin: 0 0 0.6rem; font-size: 1rem; }

    .result-err {
        background: #2d0f0f;
        border: 1px solid #da3633;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        margin: 1rem 0;
    }
    .result-err h4 { color: #f85149; margin: 0 0 0.6rem; font-size: 1rem; }

    /* File list */
    .file-item {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        color: #8b949e;
        padding: 2px 0;
    }
    .file-item .highlight { color: #79c0ff; }

    /* Button */
    .stDownloadButton > button {
        background: #238636 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.2rem !important;
        width: 100% !important;
        font-size: 0.95rem !important;
        transition: background 0.2s !important;
    }
    .stDownloadButton > button:hover {
        background: #2ea043 !important;
    }

    /* Divider */
    hr { border-color: #21262d !important; }

    /* Metric */
    [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace !important;
        color: #58a6ff !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>📚 ENLX → ENL Converter</h1>
    <p>Giải nén thư viện EndNote từ <code>.enlx</code> sang <code>.enl</code> + thư mục dữ liệu</p>
</div>
""", unsafe_allow_html=True)

# ── Giải thích kỹ thuật ────────────────────────────────────────────────────────
st.markdown("""
<div class="info-box">
    <strong>🔍 Công cụ hỗ trợ 2 kiểu cấu trúc ENLX:</strong><br><br>
    <strong>Cấu trúc mới</strong> (EndNote X7+): chứa sẵn <code>ThuVien.enl</code> + <code>ThuVien.Data/</code><br>
    <strong>Cấu trúc cũ</strong> (EndNote ≤X4): chứa <code>sdb/pdb.eni</code> + <code>PDF/</code><br>
    &nbsp;&nbsp;→ Tool sẽ tự đổi tên <code>pdb.eni</code> thành <code>ThuVien.enl</code><br>
    &nbsp;&nbsp;→ Tool sẽ tự đổi tên <code>PDF/</code> thành <code>ThuVien.Data/</code><br><br>
    Kết quả: file <code>.zip</code> → giải nén → double-click <code>.enl</code> là mở được EndNote ngay.
</div>
""", unsafe_allow_html=True)

# ── Upload ─────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Chọn file EndNote (.enlx)",
    type=["enlx"],
    help="Chỉ hỗ trợ định dạng .enlx của EndNote X7 trở lên",
)

def detect_structure(all_names):
    """
    Phát hiện cấu trúc bên trong ENLX:
      - 'new': có file .enl trực tiếp
      - 'old': có sdb/pdb.eni (cấu trúc cũ)
      - 'unknown': không nhận dạng được
    """
    enl_files = [n for n in all_names if n.lower().endswith(".enl") and "/" not in n]
    if enl_files:
        return "new", enl_files[0]

    pdb_files = [n for n in all_names if n.lower().endswith("pdb.eni")]
    if pdb_files:
        return "old", pdb_files[0]

    return "unknown", None


def build_output_zip(zf, all_names, structure, detail, base_name):
    """
    Tạo ZIP output với cấu trúc chuẩn:
      base_name.enl
      base_name.Data/  (nếu có PDF)
    """
    output_buf = io.BytesIO()
    with zipfile.ZipFile(output_buf, "w", zipfile.ZIP_DEFLATED) as out_zip:

        if structure == "new":
            # Copy nguyên, chỉ đảm bảo tên enl đúng
            for item in all_names:
                data = zf.read(item)
                if item == detail:
                    out_zip.writestr(f"{base_name}.enl", data)
                elif item.lower().startswith(Path(detail).stem.lower() + ".data/") or \
                     item.lower().startswith("pdf/"):
                    # Đổi thư mục .Data nếu cần
                    new_path = f"{base_name}.Data/" + item.split("/", 1)[-1]
                    if not item.endswith("/"):
                        out_zip.writestr(new_path, data)
                else:
                    if not item.endswith("/"):
                        out_zip.writestr(item, data)

        elif structure == "old":
            # pdb.eni → base_name.enl
            # PDF/    → base_name.Data/
            for item in all_names:
                if item.endswith("/"):
                    continue  # bỏ qua directory entry
                data = zf.read(item)

                if item.lower() == detail.lower():
                    # File database chính → đổi thành .enl
                    out_zip.writestr(f"{base_name}.enl", data)
                elif item.lower().startswith("pdf/"):
                    # Thư mục PDF → đổi thành base_name.Data/
                    sub = item[len("pdf/"):]
                    if sub:
                        out_zip.writestr(f"{base_name}.Data/{sub}", data)
                elif item.lower().startswith("sdb/"):
                    # Các file sdb khác (sdb.eni...) → bỏ qua, không cần thiết
                    pass
                else:
                    out_zip.writestr(item, data)

    return output_buf.getvalue()


if uploaded is not None:
    st.markdown("---")

    raw_bytes = uploaded.read()
    # Lấy tên file gốc làm base_name mặc định
    original_stem = Path(uploaded.name).stem

    col1, col2, col3 = st.columns(3)
    col1.metric("Kích thước gốc", f"{len(raw_bytes) / 1024:.1f} KB")

    if not zipfile.is_zipfile(io.BytesIO(raw_bytes)):
        st.markdown("""
        <div class="result-err">
            <h4>❌ File không hợp lệ</h4>
            File này không phải định dạng ENLX chuẩn (không phải ZIP).<br>
            Hãy kiểm tra lại — có thể file đã bị hỏng.
        </div>
        """, unsafe_allow_html=True)
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                all_names = zf.namelist()
                structure, detail = detect_structure(all_names)

                col2.metric("Files bên trong", len(all_names))

                # ── Hiển thị cấu trúc file ──────────────────────────────
                with st.expander("📂 Xem cấu trúc file gốc"):
                    for name in sorted(all_names):
                        is_key = detail and (name == detail or name.lower().endswith(".enl"))
                        color = "highlight" if is_key else ""
                        st.markdown(
                            f'<div class="file-item"><span class="{color}">{name}</span></div>',
                            unsafe_allow_html=True
                        )

                if structure == "unknown":
                    st.markdown("""
                    <div class="result-err">
                        <h4>⚠️ Không nhận dạng được cấu trúc</h4>
                        File không chứa <code>.enl</code> hay <code>sdb/pdb.eni</code>.<br>
                        Đây có thể không phải file EndNote hợp lệ.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    label_map = {"new": "Chuẩn mới (có .enl)", "old": "Chuẩn cũ (sdb/pdb.eni)"}
                    col3.metric("Loại cấu trúc", label_map[structure])

                    st.markdown(f"""
                    <div class="result-ok">
                        <h4>✅ Nhận dạng thành công — {label_map[structure]}</h4>
                        File chính: <code style="color:#3fb950">{detail}</code><br>
                        Sẽ xuất ra: <code style="color:#3fb950">{original_stem}.enl</code>
                        {"+ <code style='color:#3fb950'>" + original_stem + ".Data/</code>" if any("pdf/" in n.lower() or ".data/" in n.lower() for n in all_names) else ""}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("---")

                    # ── Nhập tên file output ────────────────────────────
                    custom_name = st.text_input(
                        "Tên thư viện EndNote (không cần đuôi .enl)",
                        value=original_stem,
                        placeholder="VD: NghienCuu_2024",
                        help="Tên này sẽ được dùng cho file .enl và thư mục .Data"
                    )
                    base_name = custom_name.strip() if custom_name.strip() else original_stem

                    # ── Build ZIP ───────────────────────────────────────
                    output_zip_bytes = build_output_zip(zf, all_names, structure, detail, base_name)
                    output_filename = f"{base_name}.zip"

                    st.info(
                        f"💡 Sau khi tải về: **giải nén** `{output_filename}` "
                        f"→ double-click `{base_name}.enl` là EndNote mở ngay.",
                        icon="📋"
                    )

                    st.download_button(
                        label=f"⬇️  Tải về  {output_filename}",
                        data=output_zip_bytes,
                        file_name=output_filename,
                        mime="application/zip",
                        use_container_width=True,
                    )

        except Exception as e:
            st.markdown(f"""
            <div class="result-err">
                <h4>❌ Lỗi khi xử lý file</h4>
                {str(e)}
            </div>
            """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#484f58; font-size:0.78rem;">'
    'File được xử lý hoàn toàn trên bộ nhớ — không lưu trữ dữ liệu của bạn'
    '</p>',
    unsafe_allow_html=True
)
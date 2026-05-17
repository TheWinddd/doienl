"""
EndNote ENLX → ENL Converter
Giải nén file .enlx (thực chất là ZIP) để lấy ra .enl + thư mục .Data
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
    <strong>🔍 Tại sao không chỉ đổi tên?</strong><br>
    File <code>.enlx</code> thực chất là một <strong>file ZIP</strong> bên trong chứa:<br>
    &nbsp;&nbsp;• <code>TenThuVien.enl</code> — thư viện tài liệu tham khảo<br>
    &nbsp;&nbsp;• <code>TenThuVien.Data/</code> — thư mục PDF, hình ảnh đính kèm<br><br>
    Công cụ này sẽ <strong>giải nén đúng cách</strong> và đóng gói lại thành file <code>.zip</code>
    để bạn tải về, đảm bảo EndNote mở được bình thường.
</div>
""", unsafe_allow_html=True)

# ── Upload ─────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Chọn file EndNote (.enlx)",
    type=["enlx"],
    help="Chỉ hỗ trợ định dạng .enlx của EndNote X7 trở lên",
)

if uploaded is not None:
    st.markdown("---")

    # Kiểm tra xem có phải ZIP hợp lệ không
    raw_bytes = uploaded.read()

    col1, col2, col3 = st.columns(3)
    col1.metric("Kích thước gốc", f"{len(raw_bytes) / 1024:.1f} KB")

    if not zipfile.is_zipfile(io.BytesIO(raw_bytes)):
        st.markdown("""
        <div class="result-err">
            <h4>❌ File không hợp lệ</h4>
            File này không phải định dạng ENLX chuẩn (không phải ZIP).<br>
            Hãy kiểm tra lại — có thể file đã bị hỏng hoặc chỉ là file ENL đổi tên.
        </div>
        """, unsafe_allow_html=True)
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                all_names = zf.namelist()

                # Tìm file .enl bên trong
                enl_files = [n for n in all_names if n.lower().endswith(".enl") and not n.startswith("__")]

                col2.metric("Files bên trong", len(all_names))

                if not enl_files:
                    st.markdown("""
                    <div class="result-err">
                        <h4>⚠️ Không tìm thấy file .enl</h4>
                        File ZIP này không chứa thư viện EndNote (.enl).<br>
                        Cấu trúc bên trong có thể bị lỗi.
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("Xem cấu trúc file"):
                        for name in all_names[:50]:
                            st.code(name)
                else:
                    enl_name = enl_files[0]
                    base_name = Path(enl_name).stem  # tên không có đuôi

                    col3.metric("Thư viện ENL", base_name)

                    # Hiển thị nội dung
                    st.markdown(f"""
                    <div class="result-ok">
                        <h4>✅ Phân tích thành công</h4>
                        Tìm thấy thư viện: <code style="color:#3fb950">{enl_name}</code>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("📂 Xem tất cả files bên trong"):
                        for name in sorted(all_names):
                            is_enl = name.lower().endswith(".enl")
                            color = "highlight" if is_enl else ""
                            st.markdown(
                                f'<div class="file-item"><span class="{color}">{name}</span></div>',
                                unsafe_allow_html=True
                            )

                    st.markdown("---")

                    # ── Tạo file ZIP output ─────────────────────────────────
                    output_buf = io.BytesIO()
                    with zipfile.ZipFile(output_buf, "w", zipfile.ZIP_DEFLATED) as out_zip:
                        for item in all_names:
                            data = zf.read(item)
                            out_zip.writestr(item, data)
                    output_zip_bytes = output_buf.getvalue()

                    # Tên file tải về
                    output_filename = f"{base_name}_converted.zip"

                    st.info(
                        f"💡 Sau khi tải về: **giải nén** file `{output_filename}` "
                        f"→ bạn sẽ thấy `{base_name}.enl` và thư mục `{base_name}.Data/` "
                        f"(nếu có). Mở `{base_name}.enl` bằng EndNote là xong.",
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
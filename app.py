"""RAG Chunking Strategies — Streamlit Dashboard"""

import streamlit as st
from pathlib import Path

from config import (
    ENTERPRISE_DOCS_DIR, COMPLEX_DOCS_DIR,
    MAX_CHUNK_TOKENS, CHUNK_OVERLAP_RATIO, SEMANTIC_SIM_THRESHOLD,
    APPROX_CHARS_PER_TOKEN,
)
from src.chunkers.fixed import fixed_chunk
from src.chunkers.header import header_chunk
from src.chunkers.semantic import semantic_chunk
from src.analysis import analyze_chunks
from src.retrieval import retrieve

st.set_page_config(page_title="Chunking Strategies Comparison", page_icon="scissors", layout="wide")

STRATEGY_COLORS = {"fixed_no_overlap": "#e74c3c", "fixed_overlap": "#e67e22", "header": "#2ecc71", "semantic": "#3498db"}


def _load_docs() -> dict[str, str]:
    docs = {}
    for folder in [ENTERPRISE_DOCS_DIR, COMPLEX_DOCS_DIR]:
        if folder.exists():
            for f in sorted(folder.glob("*.md")):
                label = f"{folder.name}/{f.name}"
                docs[label] = f.read_text(encoding="utf-8")
    return docs


def _run_chunking(content: str, source: str, max_chars: int, overlap_ratio: float, sim_threshold: float):
    import config
    config.MAX_CHUNK_CHARS = max_chars
    config.OVERLAP_CHARS = int(max_chars * overlap_ratio)
    config.MAX_CHUNK_TOKENS = max_chars // APPROX_CHARS_PER_TOKEN

    from src.chunkers import fixed as fixed_mod, header as header_mod
    fixed_mod.MAX_CHUNK_CHARS = max_chars
    fixed_mod.OVERLAP_CHARS = int(max_chars * overlap_ratio)
    header_mod.MAX_CHUNK_CHARS = max_chars
    header_mod.OVERLAP_CHARS = int(max_chars * overlap_ratio)

    fixed_no = fixed_chunk(content, source, overlap=False)
    fixed_ov = fixed_chunk(content, source, overlap=True)
    header_ch = header_chunk(content, source)
    semantic_ch = semantic_chunk(content, source, threshold=sim_threshold)

    return {
        "Fixed (no overlap)": fixed_no,
        "Fixed (with overlap)": fixed_ov,
        "Header/Section": header_ch,
        "Semantic": semantic_ch,
    }


def _render_sidebar():
    with st.sidebar:
        st.header("Settings")
        max_tokens = st.slider("Max chunk size (tokens)", 128, 1024, MAX_CHUNK_TOKENS, step=64)
        overlap = st.slider("Overlap ratio", 0.0, 0.5, CHUNK_OVERLAP_RATIO, step=0.05)
        sim_thresh = st.slider("Semantic similarity threshold", 0.5, 0.95, SEMANTIC_SIM_THRESHOLD, step=0.05)

        st.divider()
        st.caption("Built by Nguyen Minh Tri")
        st.caption("Senior AI Engineer")

    max_chars = max_tokens * APPROX_CHARS_PER_TOKEN
    return max_chars, overlap, sim_thresh


def _render_chunk_analysis(all_chunks: dict):
    st.subheader("Chunk Analysis")

    cols = st.columns(len(all_chunks))
    for col, (name, chunks) in zip(cols, all_chunks.items()):
        stats = analyze_chunks(chunks)
        with col:
            st.markdown(f"**{name}**")
            st.metric("Chunks", stats.chunk_count)
            st.metric("Avg Length", f"{stats.avg_length:.0f} chars")
            st.metric("Avg Tokens", f"{stats.avg_tokens:.0f}")
            st.metric("Min / Max", f"{stats.min_length} / {stats.max_length}")
            st.metric("Boundary Quality", f"{stats.boundary_quality:.0%}")

            with st.expander(f"Sample chunks ({min(3, len(chunks))})"):
                for i, c in enumerate(chunks[:3]):
                    st.markdown(f"**Chunk {i + 1}** ({len(c.text)} chars)")
                    st.code(c.text[:500] + ("..." if len(c.text) > 500 else ""), language="markdown")


def _render_retrieval_compare(all_chunks: dict):
    st.subheader("Retrieval Comparison")

    sample_queries = [
        "What is the maternity leave policy?",
        "What is the response format for the /users endpoint?",
        "What was discussed about the Q4 hiring plan?",
        "What is the SLA for SEV1 incidents?",
        "What was Q2 2025 revenue?",
    ]

    query = st.text_input("Enter a query:", value=sample_queries[0])
    st.caption("Sample queries: " + " | ".join(f'"{q}"' for q in sample_queries))

    if not query:
        return

    if st.button("Run Retrieval", type="primary"):
        cols = st.columns(len(all_chunks))
        for col, (name, chunks) in zip(cols, all_chunks.items()):
            with col:
                st.markdown(f"**{name}**")
                if not chunks:
                    st.warning("No chunks")
                    continue

                with st.spinner(f"Searching {name}..."):
                    results = retrieve(chunks, query, top_k=5)

                for rank, (chunk, score) in enumerate(results, 1):
                    st.markdown(f"**#{rank}** (score: {score:.4f})")
                    st.code(chunk.text[:300] + ("..." if len(chunk.text) > 300 else ""), language="markdown")
                    st.divider()


def _render_visual_compare(all_chunks: dict):
    st.subheader("Visual Comparison")

    names = list(all_chunks.keys())
    stats_list = [analyze_chunks(chunks) for chunks in all_chunks.values()]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Chunk Count by Strategy**")
        chart_data = {name: stats.chunk_count for name, stats in zip(names, stats_list)}
        st.bar_chart(chart_data)

    with col2:
        st.markdown("**Average Chunk Length (chars)**")
        chart_data = {name: stats.avg_length for name, stats in zip(names, stats_list)}
        st.bar_chart(chart_data)

    st.markdown("**Chunk Length Distribution**")
    dist_cols = st.columns(len(all_chunks))
    for col, (name, chunks) in zip(dist_cols, all_chunks.items()):
        with col:
            st.markdown(f"**{name}**")
            if chunks:
                lengths = [len(c.text) for c in chunks]
                st.bar_chart(lengths)
                st.caption(f"Each bar = 1 chunk, height = length in chars")

    st.markdown("**Boundary Quality Comparison**")
    bq_data = {name: stats.boundary_quality for name, stats in zip(names, stats_list)}
    st.bar_chart(bq_data)


def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                padding: 24px 32px; border-radius: 12px; margin-bottom: 24px;">
        <h1 style="color: white; margin: 0 0 4px 0;">RAG Chunking Strategies</h1>
        <p style="color: #b8d4e8; font-size: 14px; margin: 0;">
            Compare Fixed vs Header vs Semantic chunking — side-by-side analysis & retrieval impact
        </p>
    </div>
    """, unsafe_allow_html=True)

    max_chars, overlap, sim_thresh = _render_sidebar()

    docs = _load_docs()
    if not docs:
        st.error("No documents found in data/ directory.")
        return

    selected_doc = st.selectbox("Select a document:", list(docs.keys()))
    content = docs[selected_doc]

    st.caption(f"Document length: {len(content):,} chars (~{len(content) // APPROX_CHARS_PER_TOKEN:,} tokens)")

    with st.spinner("Chunking..."):
        all_chunks = _run_chunking(content, selected_doc, max_chars, overlap, sim_thresh)

    tab1, tab2, tab3 = st.tabs(["Chunk Analysis", "Retrieval Compare", "Visual Compare"])

    with tab1:
        _render_chunk_analysis(all_chunks)

    with tab2:
        _render_retrieval_compare(all_chunks)

    with tab3:
        _render_visual_compare(all_chunks)


if __name__ == "__main__":
    main()

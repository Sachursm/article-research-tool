import streamlit as st
import uuid

st.set_page_config(page_title="Article Research Tool", layout="wide")

try:
    from rag import scrape_urls, process_data, generate_answer, VECTORSTORE_DIR, extract_pdf, extract_txt
except Exception as e:
    st.error(f"RAG import failed: {e}")
    st.stop()

# Session State Init
defaults = {
    "session_id": str(uuid.uuid4()),
    "url_count": 0,
    "urls_processed": False,
    "processing": False,
    "logs": [],
    "urls_to_process": [],
    "uploaded_pdfs": [],
    "uploaded_txts": [],
    "answer": None,
    "sources": None,
    "llm": None,           # ✅ persist LLM
    "vector_store": None,  # ✅ persist vector store
    "docs": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("📰 Article Research Tool")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Your Selections")
    st.caption("Add URLs, text files, or PDF documents to use as context.")

    # URLs section
    with st.expander(f"🌐 Selected URLs ({len(st.session_state.urls_to_process)})", expanded=True):
        if st.session_state.urls_to_process:
            for url in st.session_state.urls_to_process:
                st.text(url)
        else:
            st.caption("No URLs added yet.")

    # TXT section
    with st.expander(f"📝 Selected Text Files ({len(st.session_state.uploaded_txts)})", expanded=True):
        if st.session_state.uploaded_txts:
            for file in st.session_state.uploaded_txts:
                st.text(file.name)
        else:
            st.caption("No text files added yet.")

    # PDF section
    with st.expander(f"📄 Selected PDF Files ({len(st.session_state.uploaded_pdfs)})", expanded=True):
        if st.session_state.uploaded_pdfs:
            for file in st.session_state.uploaded_pdfs:
                st.text(file.name)
        else:
            st.caption("No PDF files added yet.")

    st.divider()

    if st.button("🗑️ Remove Data"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.urls_processed = False
        st.session_state.processing = False
        st.session_state.logs = []
        st.session_state.urls_to_process = []       # ← just clear the list
        st.session_state.uploaded_pdfs = []
        st.session_state.uploaded_txts = []
        st.session_state.answer = None
        st.session_state.sources = None
        st.session_state.llm = None
        if st.session_state.vector_store is not None:
            st.session_state.vector_store.delete_collection()
        st.session_state.vector_store = None
        st.session_state.docs = None
        st.rerun()
with col2:

    if st.session_state.processing:
        
        bar = st.progress(0)
        with st.status("⚙️ Processing....", expanded=True) as status:
            try:
                # Step 1 — scrape URLs
                step1 = st.empty()
                step1.write("📥 Loading URLs...")
                document = scrape_urls(st.session_state.urls_to_process)
                step1.write("✅ Loading URLs... Done!")
                bar.progress(30)

                # Step 2 — process uploaded files
                step2 = st.empty()
                step2.write("📄 Processing uploaded files...")
                if st.session_state.uploaded_pdfs:
                    pdf_docs = extract_pdf(st.session_state.uploaded_pdfs)
                    document.extend(pdf_docs)
                if st.session_state.uploaded_txts:
                    txt_docs = extract_txt(st.session_state.uploaded_txts)
                    document.extend(txt_docs)
                step2.write("✅ Files processed... Done!")
                bar.progress(50)

                # Step 3 — chunk and embed
                step3 = st.empty()
                step3.write("✂️ Chunking & Embedding...")
                llm, vector_store, docs = process_data(document, st.session_state.session_id)
                bar.progress(75)
                step3.write("✅ Chunking & Embedding... Done!")

                # Step 4 — save to memory
                step4 = st.empty()
                step4.write("⏳ Saving to memory...")
                st.session_state.llm = llm
                st.session_state.vector_store = vector_store
                st.session_state.docs = docs
                bar.progress(100)
                step4.write("✅ Saving to memory... Done!")
                status.update(label="✅ Complete!", state="complete")

            except Exception as e:
                st.error(f"Processing failed: {e}")
                st.session_state.processing = False
                st.stop()

            st.session_state.processing = False
            st.session_state.urls_processed = True
            st.rerun()

    elif st.session_state.urls_processed:
        st.success("✅ Data processed! Ask your question below.")
        st.subheader("Ask a Question")

        question = st.text_input("Enter your question", key="question_box")

        if st.button("Ask"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Generating answer..."):
                    # ✅ Pass components from session state
                    try:
                        answer, sources = generate_answer(
                            question,
                            st.session_state.llm,
                            st.session_state.vector_store,
                            st.session_state.docs
                        )

                        st.session_state.answer = answer
                        st.session_state.sources = sources

                    except Exception as e:
                        st.error(f"Answer generation failed: {e}")
                    

        # Replace your sources section with this:
        if st.session_state.answer:
            st.subheader("Answer")
            st.markdown(st.session_state.answer)

            st.subheader("Sources")
            sources = st.session_state.sources
            if sources and sources.strip():
                source_list = [s.strip() for s in sources.split(",") if s.strip()]
                for i, source in enumerate(source_list, 1):
                    # Check if it's a URL or a filename
                    if source.startswith("http"):
                        st.markdown(f"{i}. [{source}]({source})")
                    else:
                        st.markdown(f"{i}. 📄 {source}")  # just show filename, no link
            else:
                st.info("No sources found.")

    else:
        st.info("ℹ️ Add multiple Article URLs, YouTube URLs, text files (.txt), and PDF documents.")

        # ── URL Section ──────────────────────────────
        st.subheader("🌐 Article or YouTube URLs")

        # Input for new URL
        new_url = st.text_input("Enter URL", placeholder="https://...", key="new_url_input")

        if st.button("➕ Add URL"):
            if new_url.strip():
                if new_url not in st.session_state.urls_to_process:
                    st.session_state.urls_to_process.append(new_url)
                    st.rerun()
                else:
                    st.warning("URL already added.")
            else:
                st.warning("Please enter a URL first.")

        # Show added URLs with remove button
        if st.session_state.urls_to_process:
            for i, url in enumerate(st.session_state.urls_to_process):
                col_url, col_del = st.columns([10, 1])
                with col_url:
                    st.text(url)
                with col_del:
                    if st.button("🗑️", key=f"del_url_{i}"):
                        st.session_state.urls_to_process.pop(i)
                        st.rerun()
        else:
            st.caption("No URLs added yet.")

        # ── TXT Section ──────────────────────────────
        st.subheader("📝 Text Files (.txt)")
        txt_files = st.file_uploader(
            "Upload .txt files",
            type=["txt"],
            accept_multiple_files=True,
            key="txt_uploader"
        )
        if txt_files:
            st.session_state.uploaded_txts = txt_files

        st.divider()

        # ── PDF Section ──────────────────────────────
        st.subheader("📄 PDF Documents")
        pdf_files = st.file_uploader(
            "Upload .pdf files",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        if pdf_files:
            st.session_state.uploaded_pdfs = pdf_files

        st.divider()

        # ── Process Button ────────────────────────────

        if st.button("▶ Process Data"):
            if not st.session_state.urls_to_process and not st.session_state.uploaded_txts and not st.session_state.uploaded_pdfs:
                st.error("Please add at least one URL or upload a file.")
            else:
                st.session_state.processing = True
                st.session_state.urls_processed = False
                st.session_state.answer = None
                st.session_state.sources = None
                st.session_state.llm = None
                st.session_state.vector_store = None
                st.session_state.docs = None
                st.rerun()
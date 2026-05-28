import streamlit as st

st.set_page_config(page_title="Article Research Tool", layout="wide")

try:
    from rag import scrape_urls, process_data, generate_answer
except Exception as e:
    st.error(f"RAG import failed: {e}")
    st.stop()

# Session State Init
defaults = {
    "urls_processed": False,
    "processing": False,
    "logs": [],
    "urls_to_process": [],
    "url1": "",
    "url2": "",
    "url3": "",
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
    st.subheader("Article URLs")

    # Track number of URL fields
    if "url_count" not in st.session_state:
        st.session_state.url_count = 3

    # Render URL inputs dynamically
    for i in range(1, st.session_state.url_count + 1):
        key = f"url{i}"
        if key not in st.session_state:
            st.session_state[key] = ""
        st.text_input(f"URL {i}", key=key)

    # Add URL button
    if st.button("➕ Add URL"):
        st.session_state.url_count += 1
        st.rerun()

    st.divider()

    # Collect all non-empty URLs
    urls = list(set(
        st.session_state[f"url{i}"]
        for i in range(1, st.session_state.url_count + 1)
        if st.session_state.get(f"url{i}", "").strip()
    ))

    if st.button("Process URLs"):
        if not urls:
            st.error("Please enter at least one URL.")
        else:
            st.session_state.processing = True
            st.session_state.urls_processed = False
            st.session_state.logs = []
            st.session_state.urls_to_process = urls
            st.session_state.answer = None
            st.session_state.sources = None
            st.session_state.llm = None
            st.session_state.vector_store = None
            st.session_state.docs = None
            st.rerun()

    if st.button("Remove URLs"):
        # Clear all dynamic URL fields
        for i in range(1, st.session_state.url_count + 1):
            key = f"url{i}"
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.url_count = 3  # reset back to 3
        st.session_state.urls_processed = False
        st.session_state.processing = False
        st.session_state.logs = []
        st.session_state.urls_to_process = []
        st.session_state.answer = None
        st.session_state.sources = None
        st.session_state.llm = None
        st.session_state.vector_store = None
        st.session_state.docs = None
        st.rerun()
        
with col2:

    if st.session_state.processing:
        st.subheader("⚙️ Processing Logs")

        steps = [
            "🔧 Initializing components...",
            "📥 Loading data...",
            "✂️ Splitting text...",
            "🗄️ Adding docs to vector DB...",
        ]

        log_box = st.empty()

        with st.spinner("Processing URLs, please wait..."):
            for step in steps:
                st.session_state.logs.append(step)
                log_box.markdown("\n\n".join(st.session_state.logs))

            # ✅ Capture returned components into session state
            try:
                document = scrape_urls(st.session_state.urls_to_process)
                llm, vector_store, docs = process_data(document)
                st.session_state.llm = llm
                st.session_state.vector_store = vector_store
                st.session_state.docs = docs

            except Exception as e:
                st.error(f"Processing failed: {e}")
                st.session_state.processing = False
                st.stop()
        st.session_state.processing = False
        st.session_state.urls_processed = True
        st.rerun()

    elif st.session_state.urls_processed:
        st.success("✅ URLs processed! Ask your question below.")
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
                    

        if st.session_state.answer:
            st.subheader("Answer")
            st.markdown(st.session_state.answer)

            st.subheader("Sources")
            sources = st.session_state.sources
            if sources and sources.strip():
                source_list = [s.strip() for s in sources.split(",") if s.strip()]
                for i, url in enumerate(source_list, 1):
                    st.markdown(f"{i}. [{url}]({url})")
            else:
                st.info("No sources found.")

    else:
        st.info("👈 Enter URLs on the left and click **Process URLs** to begin.")

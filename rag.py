from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from uuid import uuid4
from langchain_core.documents import Document
from playwright.async_api import async_playwright
import asyncio
import pypdf
import re
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube

load_dotenv()

# Constants
CHUNK_SIZE = 500
COLLECTION_NAME = "article_research_collection"
VECTORSTORE_DIR = Path(__file__).parent / "resources" / "vectorstore"
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"

#custom prompt for answer generation
CUSTOM_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful research assistant analyzing content from articles and videos.
Use ONLY the information from the context below to answer.
If the answer is not present, say you don't know.

Structure your response exactly like this:

**Answer**
[Direct one line answer]

**Explanation**
[Detailed explanation from the context]

**Evidence**
[Exact quote from the context supporting the answer]

Context:
=======
{context}

Question: {question}
"""
)

#specialized prompt for summarization tasks
SUMMARY_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""
You are a helpful article research assistant.
Look carefully through ALL the context provided.
If the question asks for a full form or abbreviation, look carefully for the expanded term in the context.
Provide a clear and structured summary
of the article below.

Include:
1. Main topic
2. Key points
3. Important insights
4. Final takeaway

Article:
{context}

Summary:
"""
)

SUMMARY_KEYWORDS = [
    "summary",
    "summarize",
    "overview",
    "main points",
    "key points",
]



def get_llm():
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


#embeddings created separately
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

def get_vector_store(embeddings, session_id):  # receives embeddings and session_id as parameters
    return Chroma(collection_name = f"{COLLECTION_NAME}_{session_id}",
                  persist_directory = str(VECTORSTORE_DIR),
                  embedding_function=embeddings)

def generate_summary(docs, llm):
    context = "\n\n".join(
        doc.page_content
        for doc in docs[:15]
    )
    formatted_prompt = SUMMARY_PROMPT.format(context=context)
    response = llm.invoke(formatted_prompt)
    return response.content

async def scrape_with_playwright(url: str) -> Document:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",              # required in Docker
                "--disable-dev-shm-usage",   # prevents crashes on low memory
                "--disable-gpu",             # no GPU in HF CPU container
                "--single-process"           # lighter on 2 vCPU
            ]
        )
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        content = await page.inner_text("body")
        await browser.close()
        return Document(page_content=content, metadata={"source": url})

def find_youtube_url(url: str) -> str:
    if re.search(r"(youtube\.com|youtu\.be)", url):
        return url

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def get_video_title(url: str) -> str:
    try:
        yt = YouTube(url)
        return yt.title
    except Exception:
        return url 

def get_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        return " ".join([t.text for t in transcript])
    except Exception as e:
        raise ValueError(f"Could not get transcript: {e}")

def scrape_urls(urls: list) -> list:
    result = []
    for url in urls:
        if find_youtube_url(url):
            title = get_video_title(url)
            video_id = extract_video_id(url)
            transcript = get_transcript(video_id)
            result.append(Document(
                page_content=transcript,
                metadata={"source": url, "title": title}
            ))
        else:
            loader = WebBaseLoader(
                web_paths=[url],
                header_template={"User-Agent": "Mozilla/5.0"}
            )
            data = loader.load()
            if len(data[0].page_content) < 500:
                doc = asyncio.run(scrape_with_playwright(url))
                result.append(doc)
            else:
                doc = Document(
                    page_content=data[0].page_content,
                    metadata=data[0].metadata
                )
                result.append(doc)
    return result

def extract_pdf(files: list)-> list:
    result = []
    for file in files:
        reader = pypdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        result.append(Document(page_content=text, 
                              metadata={"source": file.name}))
    return result

def extract_txt(files: list) -> list:
    result = []
    for file in files:
        text = file.read().decode("utf-8")
        result.append(Document(page_content=text, 
                              metadata={"source": file.name}))
    return result

def process_data(document: list, session_id: str):
    """
    Scrape web pages, split into chunks, store in Chroma DB.
    Returns the initialized (llm, vector_store) tuple for session storage.
    """
    print("Initializing components...")
    llm = get_llm()
    embeddings = get_embeddings()
    vector_store = get_vector_store(embeddings, session_id)

    try:
        vector_store.reset_collection()
    except Exception:
        pass

    print("Splitting text...")
    all_docs = []

    for doc in document:
        # YouTube transcript → smaller chunks for precise retrieval
        if doc.metadata.get("title"):
            splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", ". ", " "],
                chunk_size=300,     # ← smaller for videos
                chunk_overlap=50,
            )
        else:
            # Articles, PDFs, TXT → normal chunks
            splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", ". ", " "],
                chunk_size=CHUNK_SIZE,
                chunk_overlap=100,
            )
        chunks = splitter.split_documents([doc])
        all_docs.extend(chunks)

    print("Adding docs to vector DB...")
    uuids = [str(uuid4()) for _ in all_docs]
    vector_store.add_documents(all_docs, ids=uuids)

    print(f"Stored {len(all_docs)} chunks")
    return llm, vector_store, all_docs


def generate_answer(query, llm, vector_store, docs):
    """
    Generate answer or summary from article.
    """

    if vector_store is None:
        raise RuntimeError("Vector database is not initialized.")

    if llm is None:
        raise RuntimeError("LLM is not initialized.")

    # Detect summary requests
    is_summary = any(
        word in query.lower()
        for word in SUMMARY_KEYWORDS
    )

    # SUMMARY FLOW
    if is_summary:

        summary = generate_summary(
            docs,
            llm
        )

        return summary, "Summary generated from full article"

    # NORMAL RAG QA FLOW
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 8, "fetch_k": 20}
        ),
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": CUSTOM_PROMPT}
    )

    result = chain.invoke({"query": query})

    answer = result["result"]

    source_docs = result.get("source_documents", [])

    sources = ", ".join(
        set(
            doc.metadata.get("source", "")
            for doc in source_docs
            if doc.metadata.get("source")
        )
    )

    return answer, sources




if __name__ == "__main__":
    pass
---
title: Article Research Tool
emoji: 📰
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8501
pinned: false
---


# 📰 Article Research Tool

> A Retrieval-Augmented Generation (RAG) web application that ingests real-estate news articles from URLs and enables grounded question-answering using Groq's Llama-3.3-70B and a local Chroma vector database — all through a clean Streamlit interface.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?style=flat-square&logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-Framework-green?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-Llama--3.3--70B-orange?style=flat-square)
![ChromaDB](https://img.shields.io/badge/Chroma-VectorDB-purple?style=flat-square)

---

## ✨ Features

- 📄 **URL Ingestion** — Load real-estate news articles directly from URLs
- 🔎 **Semantic Search** — Retrieve relevant context using Chroma vector database
- 🧠 **Grounded Answers** — Context-aware responses powered by Groq Llama-3.3-70B
- 📚 **Source Citations** — Every answer includes source references
- 🖥️ **Interactive UI** — Clean and responsive Streamlit interface
- 💾 **Persistent Vector Store** — Local Chroma DB persists across sessions
- 🚫 **No Paid Embedding APIs** — Uses local Sentence-Transformers MiniLM for embeddings

---

## 🧱 Architecture

```
URLs Provided by User
        │
        ▼
  Web Article Loader
        │
        ▼
  Recursive Text Splitter
        │
        ▼
  Sentence-Transformer Embeddings (MiniLM)
        │
        ▼
  Chroma Vector Database  ◄────────────────────┐
        │                                       │
        ▼                                       │
  User Question ──► Semantic Retriever ─────────┘
                          │
                          ▼
                   Prompt Template
                          │
                          ▼
               Groq LLM (Llama-3.3-70B)
                          │
                          ▼
              Answer + Source Citations
```
## 🏗️ System Architecture

### 🔵 Ingestion Pipeline

<p align="center">
  <img src="https://raw.githubusercontent.com/Sachursm/RealEstate-Research-Tool-RAG-Groq-Chroma-/4ce9117d7d44d49dddb579b054e8f662d2844c0c/digram/rag_architecture.jpg" width="500">
</p>

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Groq — Llama-3.3-70B |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) |
| **Vector Database** | ChromaDB (local, persistent) |
| **RAG Framework** | LangChain |
| **UI** | Streamlit |
| **Language** | Python 3.10+ |

---

## 📂 Project Structure

```
RAG_based_Real_estate_webapplication/
│
├── app.py                  # Streamlit UI & session management
├── RAG.py                  # RAG pipeline, retriever & QA chain
├── resources/
│   └── vectorstore/        # Persistent Chroma DB (gitignored)
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Sachursm/RAG_based_Real_estate_webapplication.git
cd RAG_based_Real_estate_webapplication
```

### 2. Create & Activate a Virtual Environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Your Groq API Key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Get your free API key at [console.groq.com](https://console.groq.com)

### 5. Run the App

```bash
streamlit run app.py
```

Open your browser at: **http://localhost:8501**

---

## 📸 Screenshots

### 🖥️ Front UI
![Front UI](https://github.com/Sachursm/RealEstate-Research-Tool-RAG-Groq-Chroma-/blob/4ce9117d7d44d49dddb579b054e8f662d2844c0c/images/font_ui.png)

### ⚙️ Processing UI
![Processing UI](https://github.com/Sachursm/RealEstate-Research-Tool-RAG-Groq-Chroma-/blob/4ce9117d7d44d49dddb579b054e8f662d2844c0c/images/processing_ui.png)

### ✅ Output UI
![Output UI](https://github.com/Sachursm/RealEstate-Research-Tool-RAG-Groq-Chroma-/blob/4ce9117d7d44d49dddb579b054e8f662d2844c0c/images/output_ui.png)

---

## 📖 How to Use

1. **Enter URLs** — Paste one or more real-estate news article URLs into the sidebar
2. **Process URLs** — Click the "Process URLs" button to ingest and embed the articles
3. **Ask Questions** — Type your question in the main input field
4. **Get Answers** — Receive grounded answers with source citations from the ingested articles

---
## 🔗 Reference Article

### Understanding the Repo Rate and Its Impact on Home Loans

![Repo Rate Concept](https://www.pnbhousing.com/blog/wp-content/uploads/2023/08/repo-rate-impact-home-loan.jpg)

Source: https://www.pnbhousing.com/blog/understanding-the-repo-rate-and-its-impact-on-home-loans

---

## ❓ Basic Understanding Questions

1. What is the repo rate set by the Reserve Bank of India and why is it important?  
2. How does a change in repo rate affect home loan interest rates?  
3. What is the difference between fixed-rate and floating-rate home loans?  
4. Why don’t home loan rates change immediately after RBI changes the repo rate?  

---

---

## 📌 Key Implementation Details

- **Recursive Text Chunking** — Splits articles intelligently to preserve semantic context
- **Custom RAG Prompt** — Engineered to minimize hallucination and enforce source grounding
- **Persistent Chroma Store** — Vector embeddings survive app restarts
- **Streamlit Session State** — Manages ingestion pipeline state cleanly across reruns
- **Local Embeddings** — MiniLM runs fully on-device, no embedding API costs

---

## 🔮 Roadmap

- [ ] Multi-article conversational memory
- [ ] PDF & document upload support
- [ ] Reranking layer for higher retrieval accuracy
- [ ] Deployment to Streamlit Cloud
- [ ] Support for additional LLM providers

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Sachu Retna SM**

[![GitHub](https://img.shields.io/badge/GitHub-Sachursm-181717?style=flat-square&logo=github)](https://github.com/Sachursm)

---

<p align="center">Built with ❤️ using LangChain, Groq, ChromaDB & Streamlit</p>

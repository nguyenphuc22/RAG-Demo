# Vietnamese News RAG Chatbot

A sophisticated Retrieval-Augmented Generation (RAG) chatbot system that processes and answers queries about Vietnamese news articles using state-of-the-art language models and vector search capabilities.

## 🌟 Features

- **Multi-Source News Crawling**: Supports multiple Vietnamese news sources:
  - VnExpress
  - Tuổi Trẻ
  - Thanh Niên
  - Dân Trí
  - VTV
  - More sources planned

- **Advanced Search Capabilities**:
  - Hybrid search combining vector and keyword-based approaches
  - Semantic reranking for improved result relevance
  - Context-aware query processing
  - BM25 text search integration

- **Smart Question Handling**:
  - Dynamic question suggestion system
  - Conversation history awareness
  - Automated question generation for testing

- **Robust Evaluation System**:
  - Multiple evaluation metrics:
    - PhoBERT-based semantic similarity
    - BERT-Base cosine similarity
    - XLM-RoBERTa NLI scoring
    - BART-Large-MNLI verification
  - Automated test case generation
  - Performance analytics dashboard

## 🛠 Technical Architecture

### Core Components:
1. **Web Crawlers**:
   - Abstract crawler interface for standardization
   - Source-specific implementations
   - Robust error handling and rate limiting

2. **Vector Search Engine**:
   - MongoDB vector database integration
   - Semantic embedding using PhoBERT
   - Hybrid search implementation

3. **LLM Integration**:
   - Google's Gemini model integration
   - Custom prompt engineering
   - Context management system

4. **Evaluation Framework**:
   - Multiple model comparison system
   - Automated testing pipeline
   - Performance metrics tracking

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- MongoDB
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git https://github.com/nguyenphuc22/RAG-Demo.git
cd RAG-Demo
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

1. Set up MongoDB:
   - Create a MongoDB cluster
   - Configure connection string
   - Set up appropriate collections

2. Configure API Keys:
   - Obtain a Gemini API key
   - Set up environment variables

### Running the Application

1. Start the Streamlit application:
```bash
streamlit run ChatBot.py
```

2. Access the web interface:
   - Open your browser
   - Navigate to `http://localhost:8501`
   - Configure API keys and MongoDB connection in the sidebar

## 💡 Usage

1. **Initial Setup**:
   - Enter your Gemini API key
   - Configure MongoDB connection string
   - Select desired news source
   - Set maximum articles to crawl

2. **Crawling Data**:
   - Click "Crawl New Articles" to fetch fresh content
   - Monitor progress in the sidebar

3. **Chatting**:
   - Use the chat interface to ask questions
   - Click suggested questions in the sidebar
   - View article sources in responses

4. **Evaluation**:
   - Access evaluation tools through the sidebar
   - Configure test parameters
   - View detailed performance metrics

## 🙏 Acknowledgments

- Thanks to all contributors who have helped shape this project
- Special thanks to the teams behind:
  - PhoBERT
  - Gemini
  - Streamlit
  - MongoDB
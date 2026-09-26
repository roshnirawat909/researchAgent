# Research Agent

A Streamlit app that lets a user ask a research question, generates a plan, searches the web, reads sources, and creates a cited report.

## Features

- Research question input
- Research plan generation
- Search query generation
- Web search with DuckDuckGo
- Source reading and content extraction
- Final Markdown report with source citations
- Downloadable report

## Setup

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Copy the sample environment file and add your research key:
   ```bash
   copy .env.example .env
   ```
   Then open `.env` and replace the placeholder value.
4. Start the app with one click on Windows:
   - Double-click [run_app.bat](run_app.bat)
   - Or run this in the terminal:
     ```bash
     python -m streamlit run front.py
     ```

## Required environment variable

- `research_key`

## Notes

- The project uses Python, Streamlit, OpenAI, DuckDuckGo Search, BeautifulSoup, and `python-dotenv`.
- It is intended for research assistance and should be used with realistic expectations about source quality and AI-generated summaries.

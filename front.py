import os
import re
import json
import requests
import streamlit as st
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
from duckduckgo_search import DDGS


# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔎",
    layout="wide"
)


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()

RESEARCH_KEY = os.getenv("research_key") or os.getenv("research_kley") or os.getenv("OPENAI_API_KEY")
client = None
MODEL_NAME = "gpt-4o-mini"

if not RESEARCH_KEY:
    st.warning("research_key was not found in your .env file. Add it there or enter it below.")
    RESEARCH_KEY = st.text_input("Research Key", type="password")

if RESEARCH_KEY:
    if RESEARCH_KEY.startswith("gsk_"):
        MODEL_NAME = "llama-3.3-70b-versatile"
        client = OpenAI(
            api_key=RESEARCH_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
    else:
        client = OpenAI(api_key=RESEARCH_KEY)
else:
    st.info("The app is ready, but research features are disabled until a valid API key is provided.")
    st.stop()

st.title("🔎 AI Research Agent")
st.write(
    "Ask a question and the agent will plan the research, search the web, "
    "read sources, summarize findings, and generate a cited report."
)
st.divider()


# --------------------------------------------------
# Helper function: Call LLM
# --------------------------------------------------
def ask_llm(prompt, temperature=0.3):
    if client is None:
        return "OpenAI API key is missing. Please add a valid key to continue."

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful AI research assistant. "
                        "Use only the provided information. "
                        "Do not invent facts, sources, dates, or citations."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        if not response or not getattr(response, "choices", None):
            return "The model returned no usable output. Please try again."

        content = response.choices[0].message.content
        return content or "No content was returned by the model."

    except Exception as exc:
        return f"The AI model request failed: {exc}"


# --------------------------------------------------
# Helper function: Create research plan
# --------------------------------------------------
def create_research_plan(question):
    prompt = f"""
Create a short and practical research plan for this user question:

Question: {question}

Return exactly 3 to 5 research steps.
Each step should be concise and useful for a web research agent.

Format:
1. ...
2. ...
3. ...
"""

    return ask_llm(prompt)


# --------------------------------------------------
# Helper function: Generate search queries
# --------------------------------------------------
def generate_search_queries(question):
    prompt = f"""
Generate 4 focused web search queries for this research question:

Question: {question}

Rules:
- Queries should be concise.
- Include current or latest information where relevant.
- Cover different aspects of the question.
- Return only one query per line.
- Do not add numbering or explanations.
"""

    result = ask_llm(prompt)

    queries = [
        line.strip("-• ").strip()
        for line in result.split("\n")
        if line.strip()
    ]

    return queries[:4]


# --------------------------------------------------
# Helper function: Search the web
# --------------------------------------------------
def search_web(queries, max_results=5):
    search_results = []

    with DDGS() as ddgs:
        for query in queries:
            try:
                results = ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=max_results
                )

                for item in results:
                    title = item.get("title", "Untitled Source")
                    url = item.get("href", "")
                    snippet = item.get("body", "")

                    if url:
                        search_results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })

            except Exception:
                continue

    # Remove duplicate URLs
    unique_results = []
    seen_urls = set()

    for result in search_results:
        if result["url"] not in seen_urls:
            unique_results.append(result)
            seen_urls.add(result["url"])

    return unique_results[:10]


# --------------------------------------------------
# Helper function: Read a web page
# --------------------------------------------------
def read_webpage(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True)

        text = re.sub(r"\s+", " ", text)

        return text[:6000]

    except Exception:
        return ""


# --------------------------------------------------
# Helper function: Read selected sources
# --------------------------------------------------
def collect_source_content(search_results, max_sources=5):
    sources = []

    for index, result in enumerate(search_results[:max_sources], start=1):
        content = read_webpage(result["url"])

        if len(content) < 200:
            content = result["snippet"]

        sources.append({
            "id": index,
            "title": result["title"],
            "url": result["url"],
            "content": content
        })

    return sources


# --------------------------------------------------
# Helper function: Create final research report
# --------------------------------------------------
def create_final_report(question, sources):
    source_text = ""

    for source in sources:
        source_text += f"""
SOURCE [{source["id"]}]
Title: {source["title"]}
URL: {source["url"]}
Content:
{source["content"]}

----------------------------------------
"""

    prompt = f"""
Write a detailed research report based only on the sources below.

Research question:
{question}

Sources:
{source_text}

Requirements:
- Start with a short direct answer.
- Use Markdown headings.
- Include a section named "Key Findings".
- Explain important developments clearly.
- Include a section named "Limitations and Considerations".
- Do not make claims unsupported by the sources.
- Cite factual statements using source IDs like [1], [2], [3].
- Do not invent citations.
- Finish with a concise conclusion.
"""

    return ask_llm(prompt, temperature=0.2)


# --------------------------------------------------
# Input section
# --------------------------------------------------
question = st.text_area(
    "Enter your research question",
    placeholder="Example: Research the latest developments in RAG.",
    height=130
)

col1, col2 = st.columns(2)

with col1:
    number_of_sources = st.selectbox(
        "Number of sources to read",
        [3, 4, 5],
        index=2
    )

with col2:
    show_workflow = st.checkbox(
        "Show agent workflow",
        value=True
    )


# --------------------------------------------------
# Research button
# --------------------------------------------------
st.divider()

if st.button("🚀 Start Research", use_container_width=True):

    if not question.strip():
        st.warning("Please enter a research question first.")

    else:
        if client is None:
            st.warning("A valid OpenAI API key is required before starting research.")
            st.stop()

        st.session_state["report"] = None
        st.session_state["sources"] = []
        st.session_state["plan"] = []
        st.session_state["queries"] = []

        # --------------------------------------------------
        # Step 1: Planner
        # --------------------------------------------------
        with st.status("🧠 Creating research plan...", expanded=True) as status:

            plan = create_research_plan(question)

            st.session_state["plan"] = plan

            st.write("✅ Research plan created.")

            # --------------------------------------------------
            # Step 2: Generate search queries
            # --------------------------------------------------
            st.write("🔍 Generating search queries...")

            queries = generate_search_queries(question)

            st.session_state["queries"] = queries

            for query in queries:
                st.write(f"- {query}")

            # --------------------------------------------------
            # Step 3: Web search
            # --------------------------------------------------
            st.write("🌐 Searching the web...")

            search_results = search_web(
                queries,
                max_results=4
            )

            if not search_results:
                status.update(
                    label="❌ No web results found.",
                    state="error"
                )
                st.warning("The search did not return usable results. Try a different or more specific question.")
                st.stop()

            st.write(f"✅ Found {len(search_results)} possible sources.")

            # --------------------------------------------------
            # Step 4: Read sources
            # --------------------------------------------------
            st.write("📖 Reading sources...")

            sources = collect_source_content(
                search_results,
                max_sources=number_of_sources
            )

            st.session_state["sources"] = sources

            st.write(f"✅ Read {len(sources)} sources.")

            # --------------------------------------------------
            # Step 5: Summarize and cite
            # --------------------------------------------------
            st.write("✍️ Writing cited research report...")

            report = create_final_report(
                question,
                sources
            )

            st.session_state["report"] = report

            status.update(
                label="✅ Research completed successfully!",
                state="complete",
                expanded=False
            )


# --------------------------------------------------
# Show workflow
# --------------------------------------------------
if show_workflow and st.session_state.get("plan"):

    st.divider()
    st.subheader("🧠 Agent Workflow")

    workflow_col1, workflow_col2 = st.columns(2)

    with workflow_col1:
        st.markdown("### Research Plan")
        st.write(st.session_state["plan"])

    with workflow_col2:
        st.markdown("### Search Queries")

        for query in st.session_state["queries"]:
            st.write(f"- {query}")


# --------------------------------------------------
# Show final report
# --------------------------------------------------
if st.session_state.get("report"):

    st.divider()
    st.subheader("📄 Final Research Report")

    st.markdown(st.session_state["report"])

    # --------------------------------------------------
    # Download report
    # --------------------------------------------------
    st.download_button(
        label="⬇️ Download Research Report",
        data=st.session_state["report"],
        file_name="research_report.md",
        mime="text/markdown",
        use_container_width=True
    )


# --------------------------------------------------
# Show sources
# --------------------------------------------------
if st.session_state.get("sources"):

    st.divider()
    st.subheader("📚 Sources Used")

    for source in st.session_state["sources"]:
        with st.expander(f'[{source["id"]}] {source["title"]}'):
            st.markdown(f'**URL:** [{source["url"]}]({source["url"]})')
            st.write(source["content"][:1200] + "...")
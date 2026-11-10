from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from deep.researcher.nodes import ResearchOutput, AnalysisOutput, CritiqueOutput, FactCheckOutput

load_dotenv()

llm = ChatOpenAI(
    model="meta-llama/llama-3.3-70b-instruct",
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
    max_retries=0,
    default_headers={
        "HTTP-Referer": "https://localhost:3000",
        "X-Title": "Deep-Researcher",
    },
)

llm_researcher   = llm.with_structured_output(ResearchOutput,  method="function_calling")
llm_analyst      = llm.with_structured_output(AnalysisOutput,  method="function_calling")
llm_critic       = llm.with_structured_output(CritiqueOutput,  method="function_calling")
llm_factchecker  = llm.with_structured_output(FactCheckOutput, method="function_calling")

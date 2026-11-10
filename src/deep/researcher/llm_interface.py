from langchain_openai import ChatOpenAI
import deep.researcher.prompts as prompts
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model="meta-llama/llama-3.1-8b-instruct",
    openai_api_key=(os.getenv("OPENROUTER_API_KEY")),
    openai_api_base="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer":"https://localhost:3000",
        "X-Title" : "Multi-Stage-Debugger",
    }
)

llm_Researcher = llm.with_structured_output(prompts.RESEARCHER_PROMPT)
llm_Editor = llm.with_structured_output(prompts.EDITOR_PROMPT)
llm_Evaluator = llm.with_structured_output(prompts.EVALUATOR_PROMPT)
llm_FactChecker = llm.with_structured_output(prompts.FACT_CHECKER_PROMPT)
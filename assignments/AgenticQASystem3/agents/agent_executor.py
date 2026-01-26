from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from assignments.prompts.system_prompt import SYSTEM_PROMPT
from assignments.AgenticQASystem3.tools.vector_search import vector_search
from assignments.AgenticQASystem3.tools.calculator import calculator
from assignments.AgenticQASystem3.tools.Web_search import web_search
from assignments.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    api_key=settings.GOOGLE_API_KEY,
    )

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),  
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")  
    ]
)


tools = [vector_search, calculator, web_search]

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  
    handle_parsing_errors=True  
)

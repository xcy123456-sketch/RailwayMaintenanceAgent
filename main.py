from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
# from langchain.messages import 
import dotenv
import os

os.environ["DASHSCOPE_API_KEY"] = dotenv.get_key(dotenv.find_dotenv(), "DASHSCOPE_API_KEY")

@tool
def get_weather(city:str) -> str:
    ''' Dummy implementation for weather retrieval
    Args:
        city (str): The city to get the weather for.

    '''
    return f"The current weather in {city} is sunny with a temperature of 25°C."

# 3. 初始化百炼模型 (推荐使用 OpenAI 兼容模式)
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
)

agent = create_agent(llm, tools=[get_weather])

# Run the agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

for i in result['messages']:
    print(i.content)

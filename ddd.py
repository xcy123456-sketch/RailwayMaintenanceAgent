from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional
from agent_lib import qianwen_llm

# Step 1: Create prompt template
prompt = ChatPromptTemplate.from_template(
    "Analyze this text and extract the sentiment.\n\nText: {text}"
)

# Step 2: Define output schema
class Sentiment(BaseModel):
    """Extracted sentiment from text."""
    sentiment: str = Field(description="Positive, negative, or neutral")
    confidence: Optional[float] = Field(description="Confidence score 0-1")

# Step 3: Bind schema to LLM after prompt
llm = qianwen_llm
structured_llm = prompt | llm.with_structured_output(Sentiment)

# Step 4: Invoke - always returns Pydantic model
result = structured_llm.invoke({"text": "烦死了!"})
print(result.sentiment)
# Sentiment(sentiment='positive', confidence=0.95)
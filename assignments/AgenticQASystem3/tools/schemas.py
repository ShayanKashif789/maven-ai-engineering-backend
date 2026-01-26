from pydantic import BaseModel, Field

class VectorSearchInput(BaseModel):
    query: str = Field(
        description="The natural language search query to look up in the internal database."
    )
    k: int = Field(
        default=5, 
        description="The number of relevant document chunks to retrieve."
    )
class CalculatorInput(BaseModel):
    expression: str = Field(
        description="A pure mathematical expression to evaluate, e.g., 'sum([1.2, 2.4]) * 0.15'"
    )    
class WebSearchInput(BaseModel):
    query: str = Field(
        description="The specific search query to look up on the internet for real-time information."
    )
    num_results: int = Field(
        default=5, 
        ge=1, 
        le=10, 
        description="The number of search results to return. Keep this low to save context space."
    )    
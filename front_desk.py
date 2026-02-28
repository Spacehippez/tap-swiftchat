# tap_swiftchat/front_desk.py
import frappe
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional, List

# 1. Define the Understanding Object Schema (Pydantic)
class EmotionalState(BaseModel):
    frustration: float = Field(description="0.0 to 1.0 score of anger/frustration")
    confusion: float = Field(description="0.0 to 1.0 score of confusion")

class UnderstandingObject(BaseModel):
    intent: str = Field(description="One of: concept_help, practice_request, emotional_distress, greeting, off_topic, answer")
    topic: Optional[str] = Field(description="Main subject topic if detected (e.g. fractions)")
    primary_language: str = Field(description="Detected language code (hi, en, mr, mix)")
    normalized_text: str = Field(description="Translation/Correction of input to clean English")
    emotional_state: EmotionalState

class FrontDeskAgent:
    """
    LangChain-powered Input Understanding Agent.
    """
    
    def __init__(self):
        # Initialize Local Llama 3.2
        self.llm = ChatOllama(
            base_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.1,  # Low temp for classification
            format="json"
        )
        
        # Define Parser
        self.parser = JsonOutputParser(pydantic_object=UnderstandingObject)
        
        # Define Prompt
        self.prompt = PromptTemplate(
            template="""You are an AI Front Desk for an Indian EdTech platform.
            Analyze the student's messy input (Hinglish/Regional).
            
            Format instructions:
            {format_instructions}
            
            Student Input: "{query}"
            
            Output JSON:""",
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Compile Chain
        self.chain = self.prompt | self.llm | self.parser

    def process(self, text: str):
        """
        Run the LangChain pipeline.
        """
        try:
            # 1. Heuristic Check (Optimization)
            if len(text) < 3 and text.isdigit():
                return {
                    "intent": "answer",
                    "normalized_text": text,
                    "confidence": 1.0
                }

            # 2. Invoke Chain
            result = self.chain.invoke({"query": text})
            return result
            
        except Exception as e:
            frappe.log_error(f"FrontDesk LangChain Error: {str(e)}")
            return {"error": "AI_FAILURE", "raw_input": text}

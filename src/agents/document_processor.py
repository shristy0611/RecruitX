from typing import Dict, List, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.tool import ToolCollection
from app.schema import Message
from ..tools.document_parser_tool import DocumentParserTool
from ..tools.entity_extractor_tool import EntityExtractorTool

class DocumentProcessorAgent(ToolCallAgent):
    """Agent for processing documents and extracting entities."""
    
    name: str = "document_processor"
    description: str = "Process documents and extract entities using Gemini and FLAIR"
    
    # Configure available tools
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            DocumentParserTool(),
            EntityExtractorTool()
        )
    )
    
    # System prompt for document processing
    system_prompt: str = """You are a document processing agent that:
    1. Parses documents (PDF, DOCX) to extract text and metadata
    2. Extracts key entities using Gemini and FLAIR
    3. Validates and deduplicates extracted information
    
    Follow these guidelines:
    - Always verify document format before processing
    - Extract both text content and metadata when available
    - Use both Gemini and FLAIR for robust entity extraction
    - Deduplicate entities while preserving the highest confidence values
    - Handle errors gracefully and provide clear error messages
    """
    
    async def process_document(self, file_path: str) -> Dict:
        """Process a document and extract entities."""
        # Parse document
        parse_result = await self.available_tools.execute(
            name="document_parser",
            tool_input={
                "file_path": file_path,
                "extract_metadata": True
            }
        )
        
        if parse_result.error:
            return {"error": parse_result.error}
            
        # Extract entities
        entity_result = await self.available_tools.execute(
            name="entity_extractor",
            tool_input={
                "text": parse_result.output["text"],
                "use_flair_validation": True
            }
        )
        
        if entity_result.error:
            return {
                "document": parse_result.output,
                "error": f"Entity extraction failed: {entity_result.error}"
            }
            
        return {
            "document": parse_result.output,
            "entities": entity_result.output
        }
    
    async def run(self, request: Optional[str] = None) -> str:
        """Run the agent with an optional initial request."""
        if not request:
            return "No document path provided"
            
        # Add request to memory
        self.update_memory("user", f"Process document: {request}")
        
        # Process document
        result = await self.process_document(request)
        
        # Format response
        if "error" in result:
            response = f"Error processing document: {result['error']}"
        else:
            doc_info = result["document"]
            entities = result["entities"]
            
            response = f"""
            Document processed successfully:
            - Type: {doc_info['file_type']}
            - Length: {len(doc_info['text'])} characters
            
            Extracted Entities:
            """
            
            # Group entities by type
            entity_groups = {}
            for entity in entities:
                etype = entity["type"]
                if etype not in entity_groups:
                    entity_groups[etype] = []
                entity_groups[etype].append(entity)
            
            # Add entity summary
            for etype, group in entity_groups.items():
                response += f"\n{etype}:"
                for entity in sorted(group, key=lambda x: x["confidence"], reverse=True)[:5]:
                    response += f"\n- {entity['value']} (confidence: {entity['confidence']:.2f})"
        
        # Add response to memory
        self.update_memory("assistant", response)
        
        return response
    
    async def step(self) -> str:
        """Execute a single step - not used in this agent as we process in run()."""
        return "Document processing complete" 
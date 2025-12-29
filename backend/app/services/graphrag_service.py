"""
GraphRAG service for knowledge graph management.
"""

import os
import shutil
import asyncio
import textwrap
import traceback
from pathlib import Path
from typing import Optional, List, Tuple
from uuid import UUID

from app.config import get_settings

settings = get_settings()


class GraphRAGService:
    """
    Service for managing GraphRAG knowledge graphs.
    
    Each conversation gets its own GraphRAG directory:
        {graphrag_data_dir}/{conversation_id}/
    """

    def __init__(self):
        self.base_dir = Path(settings.graphrag_data_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # Directory Helpers
    def get_conversation_dir(self, conversation_id: UUID) -> Path:
        """Get conversation-specific directory."""
        conv_dir = self.base_dir / str(conversation_id)
        conv_dir.mkdir(parents=True, exist_ok=True)
        return conv_dir

    def get_input_dir(self, conversation_id: UUID) -> Path:
        """Get input directory for documents."""
        input_dir = self.get_conversation_dir(conversation_id) / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        return input_dir

    def get_output_dir(self, conversation_id: UUID) -> Path:
        """Get output directory for GraphRAG artifacts."""
        output_dir = self.get_conversation_dir(conversation_id) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_cache_dir(self, conversation_id: UUID) -> Path:
        """Get cache directory."""
        cache_dir = self.get_conversation_dir(conversation_id) / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

   
    # Document Handling
   
    async def save_document(self, conversation_id: UUID, filename: str, content: str) -> Path:
        """
        Save a document to the input directory with proper formatting.
        
        Args:
            conversation_id: Conversation UUID
            filename: Original filename
            content: Document content
            
        Returns:
            Path to saved file
        """
        input_dir = self.get_input_dir(conversation_id)

        # Ensure .txt extension
        if not filename.endswith(".txt"):
            filename = Path(filename).stem + ".txt"

        # Clean and format content
        content = content.strip()
        
        # Warn about very short content
        if len(content) < 100:
            print(f"Warning: Document '{filename}' has only {len(content)} characters (minimum ~100 recommended)")
        
        # Ensure proper paragraph structure for GraphRAG
        if "\n\n" not in content and len(content) > 200:
            # Add paragraph breaks at sentence boundaries
            content = content.replace(". ", ".\n\n")
        
        # Ensure content ends with newline
        if not content.endswith("\n"):
            content += "\n"

        file_path = input_dir / filename
        file_path.write_text(content, encoding="utf-8")
        
        print(f"📄 Saved document: {filename} ({len(content)} characters)")
        return file_path

    def list_documents(self, conversation_id: UUID) -> List[Tuple[str, int]]:
        """
        List all documents in the input directory.
        
        Returns:
            List of (filename, size_in_chars) tuples
        """
        input_dir = self.get_input_dir(conversation_id)
        documents = []
        
        for txt_file in input_dir.glob("*.txt"):
            content = txt_file.read_text(encoding="utf-8")
            documents.append((txt_file.name, len(content)))
        
        return documents

    def debug_input_files(self, conversation_id: UUID):
        """Debug helper to inspect input files."""
        input_dir = self.get_input_dir(conversation_id)
        
        print(f"\n{'='*70}")
        print(f"DEBUG: Input files for conversation {conversation_id}")
        print(f"{'='*70}")
        
        txt_files = list(input_dir.glob("*.txt"))
        if not txt_files:
            print("No .txt files found in input directory")
            return
        
        for txt_file in txt_files:
            print(f"\nFile: {txt_file.name}")
            print(f"{'-'*70}")
            try:
                content = txt_file.read_text(encoding="utf-8")
                print(f"Size: {len(content)} characters")
                print(f"Lines: {content.count(chr(10))} newlines")
                print(f"Paragraphs (\\n\\n): {content.count(chr(10) + chr(10))}")
                print(f"\nFirst 300 characters:")
                print(content[:300])
                if len(content) > 300:
                    print("\n[... content truncated ...]")
            except Exception as e:
                print(f"Error reading file: {e}")
        
        print(f"\n{'='*70}\n")

   
    # Indexing
   
    async def build_index(self, conversation_id: UUID, debug: bool = False) -> bool:
        """
        Build GraphRAG index from all txt files.
        
        Args:
            conversation_id: Conversation UUID
            debug: Enable debug output
            
        Returns:
            True if successful, False otherwise
        """
        conv_dir = self.get_conversation_dir(conversation_id)
        input_dir = self.get_input_dir(conversation_id)
        self.get_output_dir(conversation_id)
        self.get_cache_dir(conversation_id)

        # Validate input files
        txt_files = list(input_dir.glob("*.txt"))
        if not txt_files:
            print(" No documents to index")
            return False
        
        # Validate file contents
        total_chars = 0
        print(f"\n Validating {len(txt_files)} input file(s):")
        for txt_file in txt_files:
            try:
                content = txt_file.read_text(encoding="utf-8")
                file_chars = len(content)
                total_chars += file_chars
                print(f"  • {txt_file.name}: {file_chars:,} characters")
            except Exception as e:
                print(f"Error reading {txt_file.name}: {e}")
                return False
        
        print(f"Total: {total_chars:,} characters across {len(txt_files)} file(s)")
        
        # Check minimum content threshold
        if total_chars < 50:
            print(" Insufficient content for indexing (minimum ~50 characters required)")
            return False
        
        if total_chars < 200:
            print("Warning: Low content volume may produce limited results")
        
        # Debug mode
        if debug:
            self.debug_input_files(conversation_id)

        # Check API key
        if not settings.openai_api_key:
            print(" ERROR: OPENAI_API_KEY not set")
            return False

        # Write settings.yaml
        settings_path = conv_dir / "settings.yaml"
        yaml_content = self._create_settings_yaml(conversation_id)
        settings_path.write_text(yaml_content, encoding="utf-8")
        print(f"Generated settings.yaml at {settings_path}")

        # Environment for subprocess
        env = os.environ.copy()
        env["GRAPHRAG_API_KEY"] = settings.openai_api_key
        env["OPENAI_API_KEY"] = settings.openai_api_key

        if getattr(settings, "openai_base_url", None):
            env["OPENAI_BASE_URL"] = settings.openai_base_url
            print(f"Using custom OpenAI base URL: {settings.openai_base_url}")

        print(f"\Starting GraphRAG indexing...")
        print(f"   Root: {conv_dir}")
        print(f"   Model: {settings.openai_model}")
        print(f"   Embedding: {settings.openai_embedding_model}")

        try:
            process = await asyncio.create_subprocess_exec(
                "graphrag", "index",
                "--root", str(conv_dir),
                "--verbose",  
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await process.communicate()

            stdout_text = stdout.decode()
            stderr_text = stderr.decode()

            if process.returncode != 0:
                print("\n GraphRAG indexing failed")
                print(f"Return code: {process.returncode}")
                
                if stderr_text:
                    print(f"\n STDERR:\n{stderr_text}")
                
                if stdout_text:
                    print(f"\nSTDOUT:\n{stdout_text}")
                
                # Check for common issues
                if "Empty DataFrame" in stdout_text:
                    print("\n Troubleshooting tip: 'Empty DataFrame' usually means:")
                    print("   • Content is too short or poorly formatted")
                    print("   • Try documents with at least 200-300 characters")
                    print("   • Ensure proper paragraph breaks (double newlines)")
                    
                if "create_base_text_units" in stdout_text:
                    print("\nText chunking failed. Try:")
                    print("   • Reducing chunk size in settings")
                    print("   • Adding more content to your documents")
                    print("   • Ensuring UTF-8 encoding")
                
                return False

            print("\nGraphRAG indexing completed successfully")
            
            # Show output summary
            output_dir = self.get_output_dir(conversation_id)
            artifacts_dir = output_dir
            if artifacts_dir.exists():
                parquet_files = list(artifacts_dir.glob("*.parquet"))
                print(f"Generated {len(parquet_files)} artifact files")
            
            return True

        except FileNotFoundError:
            print("\n ERROR: 'graphrag' CLI not found in PATH")
            print("Install with: pip install graphrag")
            print("   Or add to requirements.txt: graphrag>=0.3.0")
            return False

        except Exception as e:
            print(f"\n GraphRAG indexing exception: {e}")
            if debug:
                traceback.print_exc()
            return False

   
    # Querying
   
    async def query(
        self, 
        conversation_id: UUID, 
        query: str, 
        method: str = "local",
        debug: bool = False
    ) -> Optional[str]:
        """
        Query the GraphRAG knowledge graph.
        
        Args:
            conversation_id: Conversation UUID
            query: Query string
            method: 'local' or 'global' search
            debug: Enable debug output
            
        Returns:
            Query response or None if failed
        """
        conv_dir = self.get_conversation_dir(conversation_id)
        output_dir = self.get_output_dir(conversation_id)

        # Check if index exists
        artifacts_dir = output_dir 
        if not artifacts_dir.exists():
            print(" No GraphRAG index found. Please build index first.")
            return None

        # Validate method
        if method not in ["local", "global"]:
            print(f" Invalid method '{method}'. Using 'local'.")
            method = "local"

        if not settings.openai_api_key:
            print(" ERROR: OPENAI_API_KEY not set")
            return None

        env = os.environ.copy()
        env["GRAPHRAG_API_KEY"] = settings.openai_api_key
        env["OPENAI_API_KEY"] = settings.openai_api_key

        if getattr(settings, "openai_base_url", None):
            env["OPENAI_BASE_URL"] = settings.openai_base_url

        print(f"\nQuerying GraphRAG ({method} search)...")
        print(f"   Query: {query[:100]}{'...' if len(query) > 100 else ''}")

        try:
            process = await asyncio.create_subprocess_exec(
                "graphrag", "query",
                "--config", str(conv_dir / "settings.yaml"),
                "--root", str(conv_dir),
                "--method", method,
                "--query", query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await process.communicate()

            stdout_text = stdout.decode().strip()
            stderr_text = stderr.decode().strip()

            if process.returncode != 0:
                print(" GraphRAG query error:")
                if stderr_text:
                    print(f"STDERR: {stderr_text}")
                if stdout_text:
                    print(f"STDOUT: {stdout_text}")
                return None

            if debug:
                print(f"\nRaw response length: {len(stdout_text)} characters")

            if not stdout_text:
                print(" Query returned empty response")
                return None

            print("Query completed successfully")
            return stdout_text

        except FileNotFoundError:
            print(" ERROR: 'graphrag' CLI not found in PATH")
            return None

        except Exception as e:
            print(f" GraphRAG query exception: {e}")
            if debug:
                traceback.print_exc()
            return None

   
    # Fallback Simple Search
   
    async def simple_search(self, conversation_id: UUID, query: str, max_results: int = 3) -> Optional[str]:
        """
        Simple keyword-based search fallback when GraphRAG index is unavailable.
        
        Args:
            conversation_id: Conversation UUID
            query: Search query
            max_results: Maximum number of chunks to return
            
        Returns:
            Concatenated relevant text chunks or None
        """
        input_dir = self.get_input_dir(conversation_id)
        txt_files = list(input_dir.glob("*.txt"))

        if not txt_files:
            return None

        query_words = set(query.lower().split())
        relevant = []

        for file_path in txt_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                paragraphs = content.split("\n\n")

                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if len(paragraph) < 50:  # Skip very short paragraphs
                        continue
                    
                    words = set(paragraph.lower().split())
                    overlap = len(words & query_words)

                    if overlap >= 1:
                        # Store (overlap_count, paragraph, filename)
                        relevant.append((overlap, paragraph[:800], file_path.name))
            
            except Exception as e:
                print(f" Error reading {file_path.name}: {e}")
                continue

        if not relevant:
            return None

        # Sort by relevance (overlap count)
        relevant.sort(key=lambda x: x[0], reverse=True)
        
        # Take top results
        top_chunks = []
        for overlap, chunk, filename in relevant[:max_results]:
            top_chunks.append(f"[From: {filename}]\n{chunk}")

        result = "\n\n---\n\n".join(top_chunks)
        print(f"Simple search found {len(top_chunks)} relevant chunks")
        
        return result

   
    # Status Helpers
   
    def has_index(self, conversation_id: UUID) -> bool:
        """Check if GraphRAG index exists for conversation."""
        artifacts_dir = self.get_output_dir(conversation_id) 
        return artifacts_dir.exists() and len(list(artifacts_dir.glob("*.parquet"))) > 0

    def has_documents(self, conversation_id: UUID) -> bool:
        """Check if conversation has any documents."""
        return len(list(self.get_input_dir(conversation_id).glob("*.txt"))) > 0

    def get_index_stats(self, conversation_id: UUID) -> dict:
        """Get statistics about the index."""
        stats = {
            "has_index": self.has_index(conversation_id),
            "has_documents": self.has_documents(conversation_id),
            "document_count": 0,
            "total_characters": 0,
            "artifact_count": 0
        }
        
        # Document stats
        input_dir = self.get_input_dir(conversation_id)
        for txt_file in input_dir.glob("*.txt"):
            stats["document_count"] += 1
            try:
                content = txt_file.read_text(encoding="utf-8")
                stats["total_characters"] += len(content)
            except:
                pass
        
        # Artifact stats
        artifacts_dir = self.get_output_dir(conversation_id) 
        if artifacts_dir.exists():
            stats["artifact_count"] = len(list(artifacts_dir.glob("*.parquet")))
        
        return stats

    def delete_conversation_data(self, conversation_id: UUID) -> bool:
        """Delete all data for a conversation."""
        conv_dir = self.get_conversation_dir(conversation_id)
        if conv_dir.exists():
            try:
                shutil.rmtree(conv_dir)
                print(f"Deleted data for conversation {conversation_id}")
                return True
            except Exception as e:
                print(f" Error deleting conversation data: {e}")
                return False
        return False

   
    # YAML Generator
   
    def _create_settings_yaml(self, conversation_id: UUID) -> str:
        """
        Generate properly formatted settings.yaml for GraphRAG.
        Optimized for better text chunking and entity extraction.
        """
        return textwrap.dedent(f"""
        encoding_model: cl100k_base
        skip_workflows: []

        llm:
          api_key: ${{GRAPHRAG_API_KEY}}
          type: openai_chat
          model: {settings.openai_model}
          max_tokens: 4000
          temperature: 0.0
          request_timeout: 180.0

        embeddings:
          async_mode: threaded
          llm:
            api_key: ${{GRAPHRAG_API_KEY}}
            type: openai_embedding
            model: {settings.openai_embedding_model}
            request_timeout: 180.0

        input:
          type: file
          file_type: text
          base_dir: "input"
          encoding: utf-8

        storage:
          type: file
          base_dir: "output"

        cache:
          type: file
          base_dir: "cache"

        chunks:
          size: 300
          overlap: 50
          group_by_columns: [id]

        entity_extraction:
          max_gleanings: 1
          entity_types: [organization, person, location, event, concept, technology, law, regulation]

        claim_extraction:
          enabled: false

        community_reports:
          max_length: 1500

        local_search:
          text_unit_prop: 0.5
          community_prop: 0.25
          conversation_history_max_turns: 5
          top_k_entities: 10
          top_k_relationships: 10
          max_tokens: 8000

        global_search:
          max_tokens: 8000
          data_max_tokens: 8000
          map_max_tokens: 4000
          reduce_max_tokens: 4000
        """).strip()


# Singleton instance
graphrag_service = GraphRAGService()
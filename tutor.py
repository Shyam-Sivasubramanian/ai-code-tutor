#!/usr/bin/env python3
"""
AI Code Tutor with RAG (Retrieval Augmented Generation)
--------------------------------------------------------
A Socratic teaching assistant that can reference your own documents.

Features:
- Socratic teaching method
- RAG: indexes your docs for context-aware responses
- Code snippet management

Usage: python tutor.py

Place documents in the 'docs/' folder to enable RAG.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# ============================================================================
# RAG CONFIGURATION
# ============================================================================
DOCS_FOLDER = Path("docs")  # Place your reference documents here
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 50  # Overlap between chunks
TOP_K_RESULTS = 3  # Number of relevant chunks to retrieve

# ============================================================================
# SYSTEM PROMPT - Enforces Socratic Teaching Behavior
# ============================================================================
SYSTEM_PROMPT = """You are a patient, encouraging AI code tutor who strictly follows the Socratic teaching method. Your goal is to help students LEARN, not just get answers.

## Core Principles:

### 1. Socratic Questioning
- ALWAYS respond with guiding questions that lead the student to discover the answer themselves
- Ask "what," "why," and "how" questions to stimulate critical thinking
- Never give direct answers unless the student has demonstrated genuine effort AND explicitly asks

### 2. Progressive Hints
- Start with vague, conceptual hints
- Only become more specific after the student has tried and struggled
- Use a 3-tier hint system:
  * Tier 1: Conceptual direction ("Think about how you would do this manually...")
  * Tier 2: More specific guidance ("What data structure could hold multiple values?")
  * Tier 3: Near-solution hint (only after multiple attempts)

### 3. No Code Dumps
- NEVER provide complete code solutions unless:
  * The student has shown their attempt first
  * The student has tried to fix issues themselves
  * The student EXPLICITLY asks for the full solution after demonstrating effort
- Even then, prefer showing small corrections rather than rewriting everything

### 4. Error Guidance
- When a student shares code with errors, DON'T fix it directly
- Ask questions like:
  * "What do you think this error message is telling you?"
  * "What value does this variable have at this point?"
  * "Can you trace through your code step by step?"
- Guide them to debug their own code

### 5. Encouraging Tone
- Celebrate small wins: "Great thinking!" "You're on the right track!"
- Normalize mistakes: "That's a common stumbling block" "Good learning opportunity"
- Build confidence: "You've got the right idea, let's refine it"

### 6. Using Reference Materials
- When provided with context from reference documents, use it to inform your guidance
- Still maintain the Socratic method - don't just quote the documents
- Reference the materials to point students in the right direction

## Response Format:
- Keep responses concise and focused
- Use markdown for code snippets when needed
- End responses with a question or clear next step for the student

Remember: Your success is measured by how much the STUDENT learns and figures out themselves, not by how quickly you provide answers."""


# ============================================================================
# SIMPLE RAG IMPLEMENTATION (No external vector DB required)
# ============================================================================
class SimpleRAG:
    """
    A simple RAG implementation using OpenAI embeddings.
    Stores everything in memory - no external database needed.
    """

    def __init__(self, client: OpenAI):
        self.client = client
        self.documents: List[dict] = []  # List of {text, embedding, source}
        self.is_indexed = False

    def chunk_text(self, text: str, source: str) -> List[dict]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end]
            if chunk.strip():  # Only add non-empty chunks
                chunks.append({
                    "text": chunk.strip(),
                    "source": source
                })
            start = end - CHUNK_OVERLAP
        return chunks

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text using OpenAI."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[!] Embedding error: {e}")
            return []

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def index_documents(self, docs_path: Path) -> int:
        """Index all documents in the given folder."""
        if not docs_path.exists():
            docs_path.mkdir(parents=True)
            print(f"\n[+] Created '{docs_path}' folder. Add your documents there!")
            return 0

        # Supported file types
        extensions = [".txt", ".md", ".py", ".js", ".java", ".cpp", ".c", ".html", ".css"]
        files = [f for f in docs_path.rglob("*") if f.suffix.lower() in extensions]

        if not files:
            print(f"\n[!] No documents found in '{docs_path}'")
            print(f"    Supported types: {', '.join(extensions)}")
            return 0

        print(f"\n[*] Indexing {len(files)} document(s)...")
        self.documents = []

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                chunks = self.chunk_text(content, str(file_path))

                for chunk in chunks:
                    embedding = self.get_embedding(chunk["text"])
                    if embedding:
                        self.documents.append({
                            "text": chunk["text"],
                            "source": chunk["source"],
                            "embedding": embedding
                        })
                print(f"    [OK] {file_path.name} ({len(chunks)} chunks)")
            except Exception as e:
                print(f"    [!] Error reading {file_path.name}: {e}")

        self.is_indexed = len(self.documents) > 0
        return len(self.documents)

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[dict]:
        """Search for relevant documents."""
        if not self.documents:
            return []

        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []

        # Calculate similarities
        results = []
        for doc in self.documents:
            similarity = self.cosine_similarity(query_embedding, doc["embedding"])
            results.append({
                "text": doc["text"],
                "source": doc["source"],
                "similarity": similarity
            })

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def get_context(self, query: str) -> str:
        """Get relevant context for a query."""
        if not self.is_indexed:
            return ""

        results = self.search(query)
        if not results:
            return ""

        context_parts = ["## Relevant Reference Material:\n"]
        for i, result in enumerate(results, 1):
            source_name = Path(result["source"]).name
            context_parts.append(f"### From {source_name}:\n{result['text']}\n")

        return "\n".join(context_parts)


# ============================================================================
# MAIN TUTOR CLASS
# ============================================================================
class CodeTutor:
    """Main tutor class with RAG support."""

    def __init__(self):
        """Initialize the tutor."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n[ERROR] OPENAI_API_KEY not found!")
            print("Please create a .env file with your API key:")
            print("  OPENAI_API_KEY=your-api-key-here")
            sys.exit(1)

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.conversation_history = []
        self.current_code = ""
        self.temp_file = Path(tempfile.gettempdir()) / "tutor_code.py"

        # Initialize RAG
        self.rag = SimpleRAG(self.client)

        # Initialize with system prompt
        self.conversation_history.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })

    def send_message(self, user_message: str, use_rag: bool = True) -> str:
        """Send a message with optional RAG context."""
        # Get RAG context if available
        context = ""
        if use_rag and self.rag.is_indexed:
            context = self.rag.get_context(user_message)

        # Build the full message
        if context:
            full_message = f"{context}\n\n## Student's Question:\n{user_message}"
        else:
            full_message = user_message

        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": full_message
        })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1000
            )

            assistant_message = response.choices[0].message.content

            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            self.conversation_history.pop()
            return error_msg

    def save_code(self, code: str):
        """Save code to memory and temp file."""
        self.current_code = code
        self.temp_file.write_text(code)
        print(f"\n[SAVED] Code saved to: {self.temp_file}")

    def load_code(self) -> str:
        """Load code from temp file."""
        if self.temp_file.exists():
            self.current_code = self.temp_file.read_text()
            return self.current_code
        return ""

    def edit_code(self):
        """Open the code file in the default editor."""
        if self.current_code:
            self.temp_file.write_text(self.current_code)
        else:
            self.temp_file.write_text("# Write your code here\n")

        editors = ["code", "notepad", "nano", "vim"]
        editor = os.getenv("EDITOR", None)
        if editor:
            editors.insert(0, editor)

        for ed in editors:
            try:
                subprocess.run([ed, str(self.temp_file)])
                self.current_code = self.temp_file.read_text()
                print("\n[OK] Code updated from editor")
                return
            except FileNotFoundError:
                continue

        print("\n[!] No editor found. Use /paste to enter code directly.")

    def show_code(self):
        """Display the current code snippet."""
        if self.current_code:
            print("\n" + "=" * 50)
            print("CURRENT CODE:")
            print("=" * 50)
            for i, line in enumerate(self.current_code.split("\n"), 1):
                print(f"{i:3} | {line}")
            print("=" * 50)
        else:
            print("\n[!] No code stored yet. Use /paste or /edit to add code.")

    def paste_code(self):
        """Allow user to paste multi-line code."""
        print("\nPaste your code below (type END on a new line when done):")
        print("-" * 50)

        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            except EOFError:
                break

        self.current_code = "\n".join(lines)
        self.save_code(self.current_code)
        print("[OK] Code saved!")

    def clear_history(self):
        """Clear conversation history but keep system prompt."""
        self.conversation_history = [self.conversation_history[0]]
        self.current_code = ""
        print("\n[OK] Conversation cleared. Starting fresh!")

    def share_code_with_tutor(self):
        """Share the current code with the tutor."""
        if not self.current_code:
            print("\n[!] No code to share. Use /paste or /edit first.")
            return None

        message = f"Here's my current code:\n\n```python\n{self.current_code}\n```\n\nCan you help me understand if I'm on the right track?"
        return self.send_message(message)

    def index_docs(self):
        """Index documents for RAG."""
        count = self.rag.index_documents(DOCS_FOLDER)
        if count > 0:
            print(f"\n[OK] Indexed {count} chunks from documents!")
            print("    The tutor will now reference these when answering.")
        else:
            print(f"\n[!] No documents indexed.")
            print(f"    Add .txt, .md, .py files to the '{DOCS_FOLDER}' folder.")

    def search_docs(self, query: str):
        """Search indexed documents."""
        if not self.rag.is_indexed:
            print("\n[!] No documents indexed. Run /index first.")
            return

        results = self.rag.search(query)
        if not results:
            print("\n[!] No relevant documents found.")
            return

        print(f"\n[*] Top {len(results)} results for '{query}':\n")
        for i, result in enumerate(results, 1):
            source = Path(result["source"]).name
            similarity = result["similarity"]
            text_preview = result["text"][:150] + "..." if len(result["text"]) > 150 else result["text"]
            print(f"{i}. [{source}] (similarity: {similarity:.2f})")
            print(f"   {text_preview}\n")

    def print_help(self):
        """Display help information."""
        rag_status = "ON" if self.rag.is_indexed else "OFF"
        help_text = f"""
+------------------------------------------------------------------+
|               AI Code Tutor with RAG - Commands                   |
+------------------------------------------------------------------+
|  CHAT COMMANDS:                                                   |
|    /paste    - Paste a multi-line code snippet                    |
|    /show     - Display your current code                          |
|    /edit     - Open code in external editor                       |
|    /share    - Share current code with the tutor                  |
|    /clear    - Clear conversation history                         |
+------------------------------------------------------------------+
|  RAG COMMANDS (Reference Your Own Documents):                     |
|    /index    - Index documents in the 'docs/' folder              |
|    /search   - Search indexed documents (e.g., /search loops)     |
|    /rag      - Toggle RAG on/off                                  |
+------------------------------------------------------------------+
|  OTHER:                                                           |
|    /help     - Show this help message                             |
|    /quit     - Exit the tutor                                     |
+------------------------------------------------------------------+
|  RAG Status: {rag_status:4}                                                |
|  Put .txt, .md, .py files in 'docs/' folder, then run /index      |
+------------------------------------------------------------------+
"""
        print(help_text)

    def run(self):
        """Main conversation loop."""
        print("\n" + "=" * 60)
        print("  AI CODE TUTOR with RAG")
        print("=" * 60)
        print("I'll help you learn through guided discovery.")
        print("Put your reference docs in 'docs/' and run /index")
        print("\nType /help for commands, or just start chatting!")
        print("=" * 60)

        # Auto-index if docs folder has files
        if DOCS_FOLDER.exists() and any(DOCS_FOLDER.iterdir()):
            print("\n[*] Found documents in 'docs/' folder. Indexing...")
            self.index_docs()

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    parts = user_input.split(maxsplit=1)
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""

                    if command in ["/quit", "/exit", "/q"]:
                        print("\nHappy coding! Every expert was once a beginner!")
                        break
                    elif command == "/help":
                        self.print_help()
                    elif command == "/paste":
                        self.paste_code()
                    elif command == "/show":
                        self.show_code()
                    elif command == "/edit":
                        self.edit_code()
                    elif command == "/share":
                        response = self.share_code_with_tutor()
                        if response:
                            print(f"\nTutor: {response}")
                    elif command == "/clear":
                        self.clear_history()
                    elif command == "/index":
                        self.index_docs()
                    elif command == "/search":
                        if args:
                            self.search_docs(args)
                        else:
                            print("\n[!] Usage: /search <query>")
                    elif command == "/rag":
                        if self.rag.is_indexed:
                            self.rag.is_indexed = not self.rag.is_indexed
                            status = "ON" if self.rag.is_indexed else "OFF"
                            print(f"\n[OK] RAG is now {status}")
                        else:
                            print("\n[!] No documents indexed. Run /index first.")
                    else:
                        print(f"\n[?] Unknown command: {command}. Type /help for commands.")
                    continue

                # Send message to tutor
                print("\nThinking...")
                response = self.send_message(user_input)
                print(f"\nTutor: {response}")

            except KeyboardInterrupt:
                print("\n\nGoodbye! Keep learning and coding!")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")


def main():
    """Entry point."""
    tutor = CodeTutor()
    tutor.run()


if __name__ == "__main__":
    main()

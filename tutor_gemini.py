#!/usr/bin/env python3
"""
AI Code Tutor (Gemini Version) - FREE to use!
----------------------------------------------
Uses Google's Gemini API (free tier: 15 req/min, 1500/day)

Usage: python tutor_gemini.py
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

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

## Response Format:
- Keep responses concise and focused
- Use markdown for code snippets when needed
- End responses with a question or clear next step for the student

Remember: Your success is measured by how much the STUDENT learns and figures out themselves, not by how quickly you provide answers."""


class CodeTutor:
    """Main tutor class using Google Gemini."""

    def __init__(self):
        """Initialize the tutor with Gemini API."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("\n[ERROR] GOOGLE_API_KEY not found!")
            print("Please create a .env file with your API key:")
            print("  GOOGLE_API_KEY=your-api-key-here")
            print("\nGet your FREE key at: https://aistudio.google.com/apikey")
            sys.exit(1)

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )

        # Start chat session (maintains history automatically)
        self.chat = self.model.start_chat(history=[])
        self.current_code = ""
        self.temp_file = Path(tempfile.gettempdir()) / "tutor_code.py"

    def send_message(self, user_message: str) -> str:
        """Send a message and get a response."""
        try:
            response = self.chat.send_message(user_message)
            return response.text
        except Exception as e:
            return f"API Error: {str(e)}"

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
        """Clear conversation history."""
        self.chat = self.model.start_chat(history=[])
        self.current_code = ""
        print("\n[OK] Conversation cleared. Starting fresh!")

    def share_code_with_tutor(self):
        """Share the current code with the tutor."""
        if not self.current_code:
            print("\n[!] No code to share. Use /paste or /edit first.")
            return None

        message = f"Here's my current code:\n\n```python\n{self.current_code}\n```\n\nCan you help me understand if I'm on the right track?"
        return self.send_message(message)

    def print_help(self):
        """Display help information."""
        help_text = """
+----------------------------------------------------------------+
|                 AI Code Tutor - Commands                       |
+----------------------------------------------------------------+
|  /paste    - Paste a multi-line code snippet                   |
|  /show     - Display your current code                         |
|  /edit     - Open code in external editor                      |
|  /share    - Share current code with the tutor                 |
|  /clear    - Clear conversation history                        |
|  /help     - Show this help message                            |
|  /quit     - Exit the tutor                                    |
+----------------------------------------------------------------+
|  Just type your question to chat with the tutor!               |
+----------------------------------------------------------------+
"""
        print(help_text)

    def run(self):
        """Main conversation loop."""
        print("\n" + "=" * 60)
        print("  AI CODE TUTOR (Powered by Gemini - FREE!)")
        print("=" * 60)
        print("I'll help you learn programming through guided discovery.")
        print("I ask questions to help you think through problems yourself.")
        print("\nType /help for commands, or just start chatting!")
        print("=" * 60 + "\n")

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    command = user_input.lower().split()[0]

                    if command in ["/quit", "/exit", "/q"]:
                        print("\nHappy coding! Remember: every expert was once a beginner!")
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

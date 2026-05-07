# AI Code Tutor

A Socratic AI coding assistant that runs in your terminal. Instead of giving direct answers, it guides you to discover solutions through thoughtful questions and progressive hints.

## Features

- **Socratic Teaching Method** - Guides with questions, not answers
- **Progressive Hints** - Starts vague, becomes specific as you try
- **Code Management** - Paste, edit, and share code snippets
- **Conversation Memory** - Maintains full context throughout the session
- **Encouraging Feedback** - Celebrates wins and normalizes mistakes

## Quick Start

### 1. Install Dependencies

```bash
cd ai-code-tutor
pip install -r requirements.txt
```

Or install manually:
```bash
pip install openai python-dotenv
```

### 2. Set Up Your API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# On Mac/Linux:
nano .env
# On Windows:
notepad .env
```

Your `.env` file should contain:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Run the Tutor

```bash
python tutor.py
```

## Commands

| Command   | Description                                    |
|-----------|------------------------------------------------|
| `/paste`  | Paste multi-line code (end with `END`)         |
| `/show`   | Display your current code                      |
| `/edit`   | Open code in VS Code, nano, or vim             |
| `/share`  | Share your code with the tutor for feedback    |
| `/clear`  | Clear conversation and start fresh             |
| `/help`   | Show available commands                        |
| `/quit`   | Exit the tutor                                 |

## Example Session

```
🧑 You: I need to write a function that finds the largest number in a list

🤖 Tutor: Great problem to work on! Let's think through this step by step.
   If you had a list of numbers written on paper, how would you find the
   largest one? What would be your approach?

🧑 You: I would look at each number and remember the biggest one I've seen

🤖 Tutor: Exactly! You've just described the algorithm. Now, in Python:
   - What would you use to "look at each number"?
   - How would you "remember" the biggest one you've seen?

🧑 You: A for loop to look at each, and a variable to remember?

🤖 Tutor: Perfect! Now write that out. What should the initial value of
   your "remember" variable be? Show me your first attempt!
```

## Tutor Behavior

The tutor follows these principles:

1. **Never dumps solutions** - You must show effort first
2. **Asks guiding questions** - Helps you think critically
3. **Gives progressive hints** - From vague to specific
4. **Error guidance** - Helps you debug, doesn't fix for you
5. **Encouraging tone** - Learning is celebrated

## Configuration

Edit `.env` to customize:

```env
# Use a different model
OPENAI_MODEL=gpt-4o

# Set your preferred editor for /edit command
EDITOR=code
```

## Tips for Best Results

1. **Show your attempts** - The tutor helps more when you try first
2. **Share your code** - Use `/paste` then `/share` for feedback
3. **Ask "why"** - The tutor excels at explaining concepts
4. **Be specific** - "Why does line 5 error?" works better than "it's broken"

## Troubleshooting

**"OPENAI_API_KEY not found"**
- Make sure you created a `.env` file (not just `.env.example`)
- Verify the key is correct with no extra spaces

**"API Error: Rate limit"**
- Wait a moment and try again
- Consider using `gpt-4o-mini` model (default) for lower costs

**Editor not opening**
- Set `EDITOR=code` in `.env` for VS Code
- Or use `/paste` to enter code directly

## License

MIT - Feel free to modify and share!

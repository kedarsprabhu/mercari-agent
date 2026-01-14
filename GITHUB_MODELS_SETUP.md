# GitHub Models Setup Guide (FREE GPT-4o)

This guide shows you how to use the Mercari AI Agent with **GitHub Models for FREE**.

## Why GitHub Models?

- **100% Free** - No credit card required
- **GPT-4o Access** - Same model as paid OpenAI
- **Easy Setup** - Just need a GitHub account
- **Good for Testing** - Perfect for development and testing

## Step-by-Step Setup

### 1. Get Your GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "Mercari AI Agent"
4. **No special permissions needed** - just create the token
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the `openai` library which works with GitHub Models.

### 3. Set Your GitHub Token

#### On Windows (PowerShell):
```powershell
$env:GITHUB_TOKEN="github_pat_YOUR_TOKEN_HERE"
```

#### On Windows (CMD):
```cmd
set GITHUB_TOKEN=github_pat_YOUR_TOKEN_HERE
```

#### On macOS/Linux:
```bash
export GITHUB_TOKEN="github_pat_YOUR_TOKEN_HERE"
```

#### Or use .env file:
```bash
echo "GITHUB_TOKEN=github_pat_YOUR_TOKEN_HERE" > .env
```

### 4. Run the OpenAI Version

```bash
python agent_openai.py
```

That's it! The agent will automatically detect your GitHub token and use GitHub Models.

## Example Usage

```
You: I'm looking for a Nintendo Switch under 30000 yen

[Agent is thinking...]

Agent: I'll help you find a Nintendo Switch under ¥30,000. Let me search Mercari Japan for you...
```

## Available Models on GitHub Models

When creating the agent, you can choose:
- `gpt-4o` (default, recommended)
- `gpt-4o-mini` (faster, cheaper)
- `gpt-3.5-turbo` (basic)

Example:
```python
from agent_openai import MercariAgentOpenAI

agent = MercariAgentOpenAI(
    api_key="github_pat_YOUR_TOKEN",
    base_url="https://models.inference.ai.azure.com",
    model="gpt-4o"
)
```

## Troubleshooting

### "API key must be provided"
Make sure your GITHUB_TOKEN is set:
```bash
echo $GITHUB_TOKEN  # On Linux/Mac
echo %GITHUB_TOKEN%  # On Windows CMD
```

### Rate Limits
GitHub Models has rate limits for free tier:
- 15 requests per minute
- 150 requests per day
- This is usually enough for testing!

If you hit the limit, wait a minute and try again.

### "Invalid authentication"
- Make sure you copied the full token (starts with `github_pat_`)
- Token must have been created recently
- Try generating a new token

## Comparing with OpenAI

### GitHub Models (FREE)
- ✅ Free forever
- ✅ No credit card
- ✅ GPT-4o access
- ⚠️ Rate limited
- ⚠️ For development/testing

### OpenAI (PAID)
- ✅ Higher rate limits
- ✅ Production ready
- ✅ All models
- ❌ Requires payment
- ❌ Credit card needed

## Switching Between GitHub Models and OpenAI

The code automatically detects which one to use:

**For GitHub Models:**
```bash
export GITHUB_TOKEN="github_pat_xxxxx"
python agent_openai.py
```

**For OpenAI:**
```bash
export OPENAI_API_KEY="sk-xxxxx"
python agent_openai.py
```

## Architecture Differences

Both versions use the **same core code**:
- ✅ Same scraping logic (`mercari_scraper.py`)
- ✅ Same analysis logic (in tools files)
- ✅ Same recommendations

Only difference:
This project uses the OpenAI API, which works seamlessly with GitHub Models.
- `agent_openai.py` uses OpenAI API (including GitHub Models)

## Web Playground (No Code!)

You can also test on GitHub's website:
1. Go to https://github.com/marketplace/models
2. Click on GPT-4o
3. Try the web playground
4. Test function calling directly in the browser

## Next Steps

Once you have it working:
1. Try different search queries
2. Experiment with the recommendations
3. Modify the tools to add features
4. When ready for production, switch to paid OpenAI

## Resources

- GitHub Models: https://github.com/marketplace/models
- Token Settings: https://github.com/settings/tokens
- OpenAI API Docs: https://platform.openai.com/docs

---

**Happy Shopping!** 🛍️

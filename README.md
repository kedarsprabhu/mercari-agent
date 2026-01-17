# Mercari Japan AI Shopping Agent

An intelligent AI agent that helps users find and purchase products on Mercari Japan using natural language requests.

## Overview

This agent uses OpenAI's GPT-4o with function calling to:
- Parse natural language queries for product requirements and preferences
- Execute smart searches on Mercari Japan with filters
- Scrape and analyze product data (names, prices, conditions, URLs)
- Recommend top 3 products with clear reasoning
- Engage in conversational interactions with follow-ups

### Architecture

![Architecture Diagram](mercari_agent_flow.png)

**Components:** `agent.py` (orchestration), `tools.py` (search & analysis), `mercari_scraper.py` (Selenium scraper)

**Flow:** User Input → GPT-4o Agent → Tools → Selenium Scraper → Analysis → Recommendations

### Why GPT-4o?
- Free testing via GitHub Models
- Excellent function-calling capabilities
- Strong Japanese language understanding
- Well-documented API

## Setup

### Prerequisites
- Python 3.10+
- GitHub Token (FREE) from https://github.com/settings/tokens OR OpenAI API Key

### Installation

```bash
# 1. Navigate to project
cd mercari-ai-agent

# 2. Create virtual environment
python -m venv venv
venv\\Scripts\\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API key
$env:GITHUB_TOKEN="github_pat_your-token-here"  # Windows (GitHub Models - Recommended)
# export GITHUB_TOKEN="github_pat_your-token-here"  # macOS/Linux

# OR for OpenAI:
# $env:OPENAI_API_KEY="sk-your-key-here"
```

See `GITHUB_MODELS_SETUP.md` for detailed GitHub Models setup.

## Usage

### Interactive Mode

```bash
python agent.py
```

**Example:**
```
You: I'm looking for a Nintendo Switch in good condition under 30000 yen

Agent: Here are my top 3 recommendations:

1. Nintendo Switch 本体 グレー - ¥24,800
   Condition: 目立った傷や汚れなし
   Why: Great value below average price, good condition

2. Nintendo Switch Lite - ¥18,500
   Condition: 新品、未使用
   Why: Excellent condition (new), affordable

...
```

### Programmatic Usage

```python
from agent import MercariAgentOpenAI

agent = MercariAgentOpenAI(
    api_key="your-github-token",
    base_url="https://models.inference.ai.azure.com",
    model="gpt-4o"
)

# Non-streaming
response = agent.chat("Find me a MacBook Pro under 100000 yen")

# Streaming
for chunk in agent.chat_stream("Show excellent condition only"):
    print(chunk, end="", flush=True)

agent.reset_conversation()
```

## Design Choices

### Tool-Calling Architecture
Uses OpenAI's function calling API for dynamic tool invocation (`search_mercari`, `analyze_products`, `get_product_details`). More flexible than hardcoded workflows.

### Selenium + BeautifulSoup
Mercari uses JavaScript rendering, requiring browser automation. Includes anti-bot measures and headless mode.

### Modular Architecture
Separated concerns (scraping, tools, agent logic) for easier testing, maintenance, and updates.

### Intelligent Analysis
Multi-criteria scoring (price, condition, completeness) with flexible priorities (`price`, `condition`, `balanced`). Each recommendation includes specific reasoning.

### Conversation Management
Stateful conversations maintain context across turns with reset capability for natural interactions.

## Simple Improvement Steps

- Add Japanese translation for English queries
- Potential scraper delay reduction
- Implement retry logic and results caching
- Add price history tracking and alerts
- Support multi-platform searching
- Add user preference learning
- Write comprehensive tests
- Also we could add user language input selection and provide entire response in that language

## Troubleshooting

**"API key must be provided"**: Ensure `OPENAI_API_KEY` or `GITHUB_TOKEN` is set correctly

**No products found**: Check Mercari HTML structure in `mercari_scraper.py`, try Japanese keywords

**Slow performance**: Increase scraper delay, reduce `max_results`, verify Chrome/ChromeDriver installation

**ChromeDriver issues**: Uses `webdriver-manager` for auto-download; ensure Chrome is installed

## Notes

- **Rate limiting**: Default 2-second delay between requests (configurable: `MercariScraper(delay=X)`)
- **Error handling**: Gracefully handles API errors, scraping failures, malformed data
- **Token usage**: Maintains conversation history; long conversations may need pruning
- **Detailed product info**: Use `get_product_details` tool to fetch complete information (condition, description, seller, shipping) for specific products. This visits the product page and takes a few seconds per item

## License

Created for the Mercari Japan AI Shopper Challenge.

**Acknowledgments:** OpenAI GPT-4o (GitHub Models), Selenium, BeautifulSoup4, Mercari Japan

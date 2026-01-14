# Mercari Japan AI Shopping Agent

An intelligent AI agent that helps users find and purchase products on Mercari Japan using natural language requests.

## Overview

This agent uses OpenAI's GPT-4.1 with function calling to:
- Parse natural language queries for product requirements and preferences
- Execute smart searches on Mercari Japan with filters
- Scrape and analyze product data (names, prices, conditions, URLs)
- Recommend top 3 products with clear reasoning
- Engage in conversational interactions with follow-ups

### Architecture

![Architecture Diagram](mercari_agent_flow.png)

**Components:** `agent.py` (orchestration), `tools.py` (search & analysis), `mercari_scraper.py` (Selenium scraper)

**Flow:** User Input → GPT-4.1 Agent → Tools → Selenium Scraper → Analysis → Recommendations

### Why GPT-4.1?
- Free testing via GitHub Models (no credit card)
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
    model="gpt-4.1"
)

# Non-streaming
response = agent.chat("Find me a MacBook Pro under 100000 yen")

# Streaming
for chunk in agent.chat_stream("Show excellent condition only"):
    print(chunk, end="", flush=True)

agent.reset_conversation()
```

### Advanced Usage

```python
from mercari_scraper import MercariScraper

scraper = MercariScraper(delay=3.0, headless=False)
products = scraper.search_products(
    keyword="iPhone 14",
    max_results=30,
    min_price=50000,
    max_price=100000,
    sort="price_asc"
)
```

## Design Choices

### Tool-Calling Architecture
Uses OpenAI's function calling API for dynamic tool invocation (`search_mercari`, `analyze_products`). More flexible than hardcoded workflows.

### Selenium + BeautifulSoup
Mercari uses JavaScript rendering, requiring browser automation. Includes anti-bot measures and headless mode.

### Modular Architecture
Separated concerns (scraping, tools, agent logic) for easier testing, maintenance, and updates.

### Intelligent Analysis
Multi-criteria scoring (price, condition, completeness) with flexible priorities (`price`, `condition`, `balanced`). Each recommendation includes specific reasoning.

### Conversation Management
Stateful conversations maintain context across turns with reset capability for natural interactions.

## Improvements

### Short-term
- Extract seller ratings and descriptions
- Add retry logic and caching
- Japanese translation for English queries
- Synonym expansion and category filtering
- Price history tracking
- Image display and comparison tables

### Long-term
- Multi-platform support (other Japanese marketplaces)
- User preference learning and personalization
- Automated bidding and price alerts
- Proxy rotation and comprehensive testing
- Unit/integration tests and performance benchmarks

## Troubleshooting

**"API key must be provided"**: Ensure `OPENAI_API_KEY` or `GITHUB_TOKEN` is set correctly

**No products found**: Check Mercari HTML structure in `mercari_scraper.py`, try Japanese keywords

**Slow performance**: Increase scraper delay, reduce `max_results`, verify Chrome/ChromeDriver installation

**ChromeDriver issues**: Uses `webdriver-manager` for auto-download; ensure Chrome is installed

## Notes

- **Rate limiting**: Default 2-second delay between requests (configurable: `MercariScraper(delay=X)`)
- **Error handling**: Gracefully handles API errors, scraping failures, malformed data
- **Token usage**: Maintains conversation history; long conversations may need pruning
- **Condition information**: Shows "See details" because Mercari's search page doesn't display condition data. Click product URLs to see actual condition (新品, 未使用, etc.). Fetching condition for all products would require visiting each detail page (~20x slower)

## License

Created for the Mercari Japan AI Shopper Challenge.

**Acknowledgments:** OpenAI GPT-4.1 (GitHub Models), Selenium, BeautifulSoup4, Mercari Japan

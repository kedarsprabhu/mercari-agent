"""
Tool Definitions for the Mercari AI Agent (OpenAI Version)

This module defines the tools that the AI agent can use to interact with Mercari.
Tools are defined in the format required by OpenAI's function calling API.
"""

from typing import List, Dict, Any, Optional
from mercari_scraper import MercariScraper


# Initialize the scraper
scraper = MercariScraper()


# Tool definitions for OpenAI API (function calling format)
TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "search_mercari",
            "description": "Search for products on Mercari Japan using keywords and optional filters. Returns a list of up to 20 products with their details including name, price, condition, and URL. Use this tool when the user wants to find items on Mercari.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The search keyword or product name in Japanese or English. Examples: 'iPhone 13', 'Nintendo Switch', 'ソニー ヘッドホン'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 20, max: 50)",
                        "default": 20
                    },
                    "min_price": {
                        "type": "integer",
                        "description": "Minimum price in Japanese Yen (JPY). Example: 5000 for ¥5,000"
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "Maximum price in Japanese Yen (JPY). Example: 50000 for ¥50,000"
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'created_time' for newest first, 'price_asc' for cheapest first, 'price_desc' for most expensive first",
                        "enum": ["created_time", "price_asc", "price_desc"],
                        "default": "created_time"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_products",
            "description": "Analyze a list of products and select the top 3 recommendations. IMPORTANT: You must pass the 'products' array from the search_mercari results into this function's 'products' parameter. Use this after searching to rank and recommend items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "products": {
                        "type": "array",
                        "description": "The array of products returned from search_mercari. You MUST pass the 'products' array from the previous search result here.",
                        "items": {
                            "type": "object"
                        }
                    },
                    "user_preferences": {
                        "type": "object",
                        "description": "User preferences for ranking products",
                        "properties": {
                            "priority": {
                                "type": "string",
                                "description": "What to prioritize: 'price' (cheapest), 'condition' (best condition), 'balanced' (best value)",
                                "enum": ["price", "condition", "balanced"],
                                "default": "balanced"
                            },
                            "max_budget": {
                                "type": "integer",
                                "description": "Maximum budget in JPY"
                            }
                        }
                    }
                },
                "required": ["products"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Fetch complete details for a specific product by visiting its page. This provides more information than the search results, including full description, condition details, shipping info, seller information, and more. Use this when you need detailed information about a specific product. Note: This takes extra time as it loads the full product page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_url": {
                        "type": "string",
                        "description": "The full Mercari product URL (e.g., 'https://jp.mercari.com/item/m12345678901')"
                    }
                },
                "required": ["product_url"]
            }
        }
    }
]


def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool based on its name and input parameters.
    
    Args:
        tool_name: Name of the tool to execute
        tool_input: Dictionary of input parameters for the tool
    
    Returns:
        Dictionary containing the tool execution results
    """
    if tool_name == "search_mercari":
        return search_mercari(**tool_input)
    elif tool_name == "analyze_products":
        return analyze_products(**tool_input)
    elif tool_name == "get_product_details":
        return get_product_details(**tool_input)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def search_mercari(
    keyword: str,
    max_results: int = 20,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    sort: str = "created_time"
) -> Dict[str, Any]:
    """
    Search for products on Mercari Japan.
    
    Args:
        keyword: Search keyword
        max_results: Maximum number of results (default: 20)
        min_price: Minimum price in JPY
        max_price: Maximum price in JPY
        sort: Sort order
    
    Returns:
        Dictionary containing search results
    """
    try:
        products = scraper.search_products(
            keyword=keyword,
            max_results=min(max_results, 50),  # Cap at 50
            min_price=min_price,
            max_price=max_price,
            sort=sort
        )
        
        return {
            "success": True,
            "keyword": keyword,
            "total_results": len(products),
            "products": products
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


def get_product_details(product_url: str) -> Dict[str, Any]:
    """
    Fetch complete details for a specific product by visiting its page.
    
    Args:
        product_url: Full URL to the Mercari product page
    
    Returns:
        Dictionary containing complete product details
    """
    try:
        product = scraper.get_product_details(product_url)
        
        if product:
            return {
                "success": True,
                "product": product
            }
        else:
            return {
                "success": False,
                "error": "Failed to extract product details",
                "product": None
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "product": None
        }


def _score_condition(condition: str) -> tuple[int, str]:
    """
    Score a product's condition and return the score with a reason.
    
    Args:
        condition: Product condition string (lowercase)
    
    Returns:
        Tuple of (score, reason_string)
    """
    condition_lower = condition.lower()
    
    if '新品' in condition_lower or 'new' in condition_lower:
        return (100, "Excellent condition (new)")
    elif '未使用' in condition_lower or 'unused' in condition_lower:
        return (85, "Very good condition (unused)")
    elif '目立った傷' in condition_lower or 'good' in condition_lower:
        return (70, "Good condition")
    else:
        return (50, "Acceptable condition")


def analyze_products(
    products: List[Dict],
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze products and return top 3 recommendations.
    
    Args:
        products: List of product dictionaries
        user_preferences: User preferences for ranking
    
    Returns:
        Dictionary containing top 3 recommendations with reasoning
    """
    if not products:
        return {
            "success": False,
            "error": "No products to analyze",
            "recommendations": []
        }
    
    # Default preferences
    if user_preferences is None:
        user_preferences = {}
    
    priority = user_preferences.get('priority', 'balanced')
    max_budget = user_preferences.get('max_budget')
    
    # Filter out sold items
    available_products = [p for p in products if not p.get('is_sold', False)]
    
    if not available_products:
        available_products = products  # Fallback to all if none available
    
    # Filter by budget if specified
    if max_budget:
        available_products = [p for p in available_products if p.get('price', 0) <= max_budget]
    
    if not available_products:
        return {
            "success": False,
            "error": "No products match the budget criteria",
            "recommendations": []
        }
    
    # Pre-calculate average price for balanced mode (avoids O(n²) complexity)
    avg_price = None
    if priority == 'balanced' and available_products:
        avg_price = sum(p.get('price', 0) for p in available_products) / len(available_products)
    
    # Score and sort products based on priority
    scored_products = []
    
    for product in available_products:
        score = 0
        reasons = []
        
        price = product.get('price', 0)
        condition = product.get('condition', 'Not specified').lower()
        
        # Scoring logic based on priority
        if priority == 'price':
            # Lower price is better
            if price > 0:
                score = 100000 / price  # Inverse of price
                reasons.append(f"Affordable price at ¥{price:,}")
        
        elif priority == 'condition':
            # Better condition is better - use helper function
            condition_score, reason = _score_condition(condition)
            score = condition_score
            reasons.append(reason)
        
        else:  # balanced
            # Balance between price and condition
            condition_score, condition_reason = _score_condition(condition)
            reasons.append(condition_reason)
            
            # Price score (relative to average)
            if price > 0 and avg_price and avg_price > 0:
                price_ratio = price / avg_price
                if price_ratio < 0.8:
                    price_score = 100
                    reasons.append("Great value - below average price")
                elif price_ratio < 1.2:
                    price_score = 70
                    reasons.append("Fair price")
                else:
                    price_score = 50
            else:
                price_score = 50
            
            score = (condition_score * 0.5) + (price_score * 0.5)
        
        # Bonus for having all information
        if product.get('name') and product.get('price') and product.get('url'):
            score += 5
            reasons.append("Complete product information available")
        
        scored_products.append({
            'product': product,
            'score': score,
            'reasons': reasons
        })
    
    # Sort by score (descending)
    scored_products.sort(key=lambda x: x['score'], reverse=True)
    
    # Get top 3
    top_3 = scored_products[:3]
    
    recommendations = []
    for i, item in enumerate(top_3, 1):
        product = item['product']
        recommendations.append({
            'rank': i,
            'product': product,
            'score': item['score'],
            'reasons': item['reasons'],
            'recommendation_summary': f"Ranked #{i} - {product.get('name', 'Unknown')} at {product.get('price_display', 'N/A')}"
        })
    
    return {
        "success": True,
        "total_analyzed": len(available_products),
        "priority": priority,
        "recommendations": recommendations
    }

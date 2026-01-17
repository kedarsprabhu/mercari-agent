"""
Mercari Japan Web Scraper Module (Selenium Version)

This module handles all web scraping functionality for Mercari Japan using Selenium
to handle dynamic content and anti-bot measures.
"""

import time
import urllib.parse
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class MercariScraper:
    """
    A web scraper for Mercari Japan using Selenium.
    """
    
    BASE_URL = "https://jp.mercari.com"
    SEARCH_URL = f"{BASE_URL}/search"
    
    def __init__(self, delay: float = 2.0, headless: bool = True):
        """
        Initialize the scraper.
        
        Args:
            delay: Delay in seconds (default: 2.0)
            headless: Whether to run in headless mode (default: True)
        """
        self.delay = delay
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Initialize the Chrome driver if not already done."""
        if self.driver:
            return

        print("[Scraper] Initializing Chrome Driver...")
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options
            )
            # stealth tweaks
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("[Scraper] Driver initialized successfully.")
        except Exception as e:
            print(f"[Scraper] Error initializing driver: {e}")
            raise e

    def _close_driver(self):
        """Close the driver if it exists."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def search_products(
        self,
        keyword: str,
        max_results: int = 20,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        condition: Optional[str] = None,
        sort: str = "created_time"
    ) -> List[Dict]:
        """
        Search for products on Mercari Japan.
        """
        self._setup_driver()
        
        params = {
            'keyword': keyword,
            'sort': sort
        }
        
        if min_price:
            params['price_min'] = str(min_price)
        if max_price:
            params['price_max'] = str(max_price)
        if condition:
            params['item_condition_id'] = self._map_condition(condition)
        
        query_string = urllib.parse.urlencode(params)
        url = f"{self.SEARCH_URL}?{query_string}"
        
        print(f"[Scraper] Navigating to: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for items to load
            print("[Scraper] Waiting for items to load...")
            wait = WebDriverWait(self.driver, 15)
            # Wait for at least one item or a "no results" indicator. We try to wait for the item grid
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-testid='item-cell'], mer-item-thumbnail")))
            
            # Scroll down a bit to trigger lazy loading if needed
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(self.delay)
            
            # Use BeautifulSoup for parsing as it's faster for bulk static HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            products = self._extract_products(soup, max_results)
            print(f"[Scraper] Found {len(products)} products.")
            return products
            
        except Exception as e:
            print(f"[Scraper] Error during search: {e}")
            # Optional warning: if timeout, maybe we got blocked or selector changed
            if "Time-out" in str(e) or "Timeout" in str(e):
                print("[Scraper] Timeout waiting for results. Mercari might be blocking or slow.")
            return []
        
        # We don't close the driver here to keep it alive for next request, but in a long lived app we might want to manage lifecycle better.
    
    def _extract_products(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """
        Extract product information from the search results HTML.
        """
        products = []
        
        # Mercari structure (Subject to change, hence multiple selectors)
        product_items = (
            soup.find_all('li', {'data-testid': 'item-cell'}) or
            soup.find_all('div', class_=lambda x: x and 'ItemThumbnail' in x) or
            soup.find_all('mer-item-thumbnail') 
        )
        
        for item in product_items[:max_results]:
            try:
                product = self._extract_product_info(item)
                if product:
                    products.append(product)
            except Exception as e:
                continue
        
        return products
    
    def _extract_product_info(self, item) -> Optional[Dict]:
        product = {}
        
        # URL & ID
        link = item.find('a', href=lambda x: x and '/item/' in str(x))
        if not link:
            link = item if item.name == 'a' else None
        
        if link and link.get('href'):
            href = link['href']
            product['url'] = self.BASE_URL + href if not href.startswith('http') else href
            product['id'] = href.split('/item/')[-1].split('?')[0] if '/item/' in href else 'unknown'
        else:
            return None
        
        # Name
        title_elem = (
            item.find('span', {'data-testid': 'thumbnail-title'}) or
            item.find('h3') or
            item.find(lambda tag: tag.name == "span" and "itemName" in str(tag.get('class', '')))
        )
        if title_elem:
             # Look for "alt" attribute in image if title text is missing or weird
             img = item.find('img')
             if img and img.get('alt') and len(title_elem.get_text(strip=True)) < 3:
                  product['name'] = img.get('alt')
             else:
                  product['name'] = title_elem.get_text(strip=True)
        else:
             # Fallback to image alt
             img = item.find('img')
             product['name'] = img.get('alt') if img else 'Unknown Product'

        # Price
        price_elem = (
            item.find('span', {'data-testid': 'thumbnail-price'}) or
            item.find('span', class_=lambda x: x and 'price' in str(x).lower()) or
            item.find('mer-price')
        )
        
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            if not price_text and price_elem.has_attr('value'): # mer-price might have value attr
                price_text = price_elem['value']
                
            price_clean = ''.join(filter(str.isdigit, price_text))
            product['price'] = int(price_clean) if price_clean else 0
            product['price_display'] = f"¥{product['price']:,}"
        else:
            product['price'] = 0
            product['price_display'] = 'N/A'
            
        # Condition (Mercari uses aria-label or specific localized strings)
        # For now, we often can't see condition on the thumbnail in new design
        product['condition'] = 'See details' # Default as it's often hidden in grid
        
        # Sold status
        # Look for "sold" overlay
        sold_indicator = (
            item.find('div', {'aria-label': '売り切れ'}) or
            item.find('div', class_='sold') or 
            item.find(string='SOLD')
        )
        product['is_sold'] = bool(sold_indicator)
        
        return product
    
    def _map_condition(self, condition: str) -> str:
        condition_map = {
            'new': '1',
            'like_new': '2',
            'good': '3',
            'acceptable': '4',
            'poor': '5'
        }
        return condition_map.get(condition.lower(), '')

    def get_product_details(self, product_url: str) -> Optional[Dict]:
        """
        Scrape detailed information from a single product page.
        
        Args:
            product_url: Full URL to the Mercari product page
            
        Returns:
            Dictionary containing complete product details or None if failed
        """
        self._setup_driver()
        
        print(f"[Scraper] Fetching product details from: {product_url}")
        
        try:
            self.driver.get(product_url)
            
            # Wait for main content to load
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mer-heading, h1, [data-testid='item-name']")))
            
            # Additional wait for dynamic content
            time.sleep(self.delay)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            product = {
                'url': product_url,
                'id': product_url.split('/item/')[-1].split('?')[0] if '/item/' in product_url else 'unknown'
            }
            
            # Product Name/Title
            name_elem = (
                soup.find('mer-heading', {'data-testid': 'item-name'}) or
                soup.find('h1') or
                soup.find('mer-heading')
            )
            product['name'] = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            # Price
            price_elem = (
                soup.find('mer-price', {'data-testid': 'price'}) or
                soup.find('span', {'data-testid': 'price'}) or
                soup.find('mer-price')
            )
            if price_elem:
                price_text = price_elem.get('value') or price_elem.get_text(strip=True)
                price_clean = ''.join(filter(str.isdigit, str(price_text)))
                product['price'] = int(price_clean) if price_clean else 0
                product['price_display'] = f"¥{product['price']:,}"
            else:
                product['price'] = 0
                product['price_display'] = 'N/A'
            
            # Condition - Look for the item condition section
            condition_elem = (
                soup.find('span', {'data-testid': 'item-condition'}) or
                soup.find('mer-text', string=lambda x: x and ('新品' in str(x) or '中古' in str(x) or '未使用' in str(x))) or
                soup.find(string=lambda x: x and '商品の状態' in str(x))
            )
            if condition_elem:
                # Try to get the actual condition value
                parent = condition_elem.parent if hasattr(condition_elem, 'parent') else None
                if parent:
                    next_elem = parent.find_next_sibling() or parent.find_next()
                    if next_elem:
                        product['condition'] = next_elem.get_text(strip=True)
                    else:
                        product['condition'] = condition_elem.get_text(strip=True) if hasattr(condition_elem, 'get_text') else str(condition_elem)
                else:
                    product['condition'] = str(condition_elem)
            else:
                # Try alternative: look for condition in table rows
                rows = soup.find_all('mer-display-row') or soup.find_all('tr')
                for row in rows:
                    text = row.get_text(strip=True)
                    if '状態' in text or 'condition' in text.lower():
                        product['condition'] = text.replace('商品の状態', '').strip()
                        break
                else:
                    product['condition'] = 'Not specified'
            
            # Description
            desc_elem = (
                soup.find('mer-text', {'data-testid': 'description'}) or
                soup.find('pre', {'data-testid': 'description'}) or
                soup.find('div', {'data-testid': 'description'}) or
                soup.find('section', {'aria-labelledby': lambda x: x and 'description' in str(x).lower()})
            )
            if desc_elem:
                product['description'] = desc_elem.get_text(strip=True)
            else:
                # Fallback: look for any large text block
                desc_section = soup.find('section', class_=lambda x: x and 'description' in str(x).lower())
                product['description'] = desc_section.get_text(strip=True) if desc_section else 'No description available'
            
            # Shipping Information
            shipping_elem = (
                soup.find('span', {'data-testid': 'shipping-fee'}) or
                soup.find('mer-text', string=lambda x: x and ('送料' in str(x) or '配送' in str(x)))
            )
            if shipping_elem:
                product['shipping'] = shipping_elem.get_text(strip=True)
            else:
                # Look in table rows
                for row in soup.find_all(['mer-display-row', 'tr', 'div']):
                    text = row.get_text(strip=True)
                    if '送料' in text or '配送' in text:
                        product['shipping'] = text
                        break
                else:
                    product['shipping'] = 'See listing'
            
            # Seller Information
            seller_elem = (
                soup.find('a', {'data-testid': 'seller-name'}) or
                soup.find('mer-user-object') or
                soup.find('a', href=lambda x: x and '/user/profile/' in str(x))
            )
            if seller_elem:
                product['seller_name'] = seller_elem.get_text(strip=True) or seller_elem.get('name', 'Unknown')
                seller_link = seller_elem.get('href', '')
                if seller_link and not seller_link.startswith('http'):
                    seller_link = self.BASE_URL + seller_link
                product['seller_url'] = seller_link
            else:
                product['seller_name'] = 'Unknown'
                product['seller_url'] = ''
            
            # Category
            category_elem = soup.find('mer-breadcrumbs') or soup.find('nav', {'aria-label': 'breadcrumb'})
            if category_elem:
                breadcrumb_items = category_elem.find_all('a') or category_elem.find_all('span')
                product['category'] = ' > '.join([item.get_text(strip=True) for item in breadcrumb_items if item.get_text(strip=True)])
            else:
                product['category'] = 'Not specified'
            
            # Sold Status
            sold_indicator = (
                soup.find('div', {'aria-label': '売り切れ'}) or
                soup.find('mer-text', string=lambda x: x and 'SOLD' in str(x).upper()) or
                soup.find(string=lambda x: x and '売り切れ' in str(x))
            )
            product['is_sold'] = bool(sold_indicator)
            
            # Number of likes/favorites
            likes_elem = soup.find('span', {'data-testid': 'like-count'}) or soup.find('mer-icon-button', {'name': 'heart'})
            if likes_elem:
                likes_text = likes_elem.get_text(strip=True)
                likes_clean = ''.join(filter(str.isdigit, likes_text))
                product['likes'] = int(likes_clean) if likes_clean else 0
            else:
                product['likes'] = 0
            
            # Images
            img_elements = soup.find_all('img', {'data-testid': lambda x: x and 'image' in str(x).lower()})
            if not img_elements:
                img_elements = soup.find_all('img', src=lambda x: x and 'static.mercdn.net' in str(x))
            product['images'] = [img.get('src') for img in img_elements[:10] if img.get('src')]
            product['image_count'] = len(product['images'])
            
            print(f"[Scraper] Successfully extracted details for: {product['name'][:50]}...")
            return product
            
        except Exception as e:
            print(f"[Scraper] Error fetching product details: {e}")
            return None

    def __del__(self):
        self._close_driver()

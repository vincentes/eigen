"""
Comprehensive web scraper for shop.aluminios.com product catalog.
"""

import time
import random
import argparse
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For LLM descriptions
try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: openai not available. Install with: pip install openai")

import config
from utils import (
    setup_logging, clean_text, extract_price, extract_currency, extract_sku,
    determine_availability, build_absolute_url, validate_url, extract_category_from_url,
    save_json, calculate_success_rate, format_duration, create_scrape_metadata,
    validate_product_data, retry_on_failure
)


class AluminiosProductScraper:
    """
    Main scraper class for extracting product information from shop.aluminios.com.
    Supports multiple product categories: perfiles, accesorios, and policarbonatos.
    """
    
    def __init__(self, delay: float = config.DEFAULT_DELAY, output_file: str = config.DEFAULT_OUTPUT_FILE, 
                 categories: List[str] = None, detailed_scraping: bool = False, 
                 generate_descriptions: bool = False):
        self.delay = delay
        self.output_file = output_file
        self.categories = categories or list(config.CATEGORIES_CONFIG.keys())  # Default to all categories
        self.detailed_scraping = detailed_scraping
        self.generate_descriptions = generate_descriptions
        self.session = requests.Session()
        
        # Initialize OpenAI client for descriptions
        self.openai_client = None
        if self.generate_descriptions and LLM_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            else:
                self.logger.warning("OPENAI_API_KEY not found. LLM descriptions will be skipped.")
                self.generate_descriptions = False
        self.logger = setup_logging(
            log_file=os.path.join(config.LOG_DIRECTORY, f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        )
        
        # Initialize session with headers
        self.session.headers.update({
            'User-Agent': random.choice(config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Tracking variables
        self.products = []
        self.products_by_category = {category: [] for category in self.categories}
        self.total_requests = 0
        self.successful_requests = 0
        self.start_time = None
        self.end_time = None
        
        # Validate categories
        valid_categories = set(config.CATEGORIES_CONFIG.keys())
        invalid_categories = set(self.categories) - valid_categories
        if invalid_categories:
            raise ValueError(f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}")
    
    @retry_on_failure(max_retries=config.MAX_RETRIES, backoff_factor=config.RETRY_BACKOFF_FACTOR)
    def make_request(self, url: str) -> Optional[requests.Response]:
        """Make a request with error handling and rate limiting."""
        self.total_requests += 1
        
        try:
            # Rotate user agent occasionally
            if self.total_requests % 10 == 0:
                self.session.headers['User-Agent'] = random.choice(config.USER_AGENTS)
            
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            self.successful_requests += 1
            self.logger.debug(f"Successfully fetched: {url}")
            
            # Rate limiting
            time.sleep(self.delay + random.uniform(0, 0.5))
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise
    
    def extract_product_data(self, card_element: BeautifulSoup, page_number: int, category: str) -> Optional[Dict[str, Any]]:
        """Extract product data from a product card element."""
        try:
            product = {}
            
            # Extract product name
            name_element = card_element.select_one(config.SELECTORS['product_name'])
            if name_element:
                product['name'] = clean_text(name_element.get_text())
            else:
                self.logger.warning(f"No product name found in card on page {page_number}")
                return None
            
            # Extract SKU
            sku_element = card_element.select_one(config.SELECTORS['sku'])
            if sku_element:
                product['sku'] = extract_sku(sku_element.get_text())
            else:
                self.logger.warning(f"No SKU found for product: {product.get('name', 'Unknown')}")
                product['sku'] = None
            
            # Extract price
            price_element = card_element.select_one(config.SELECTORS['price'])
            if price_element:
                price_text = price_element.get_text()
                product['price'] = extract_price(price_text)
                
                # Extract currency
                currency_element = card_element.select_one(config.SELECTORS['currency'])
                if currency_element:
                    product['currency'] = extract_currency(currency_element.get_text())
                else:
                    product['currency'] = extract_currency(price_text)
            else:
                product['price'] = None
                product['currency'] = "USD"
            
            # Extract product URL
            url_element = card_element.select_one(config.SELECTORS['product_url'])
            if url_element and url_element.get('href'):
                relative_url = url_element.get('href')
                product['product_url'] = build_absolute_url(config.BASE_URL, relative_url)
            else:
                self.logger.warning(f"No product URL found for: {product.get('name', 'Unknown')}")
                product['product_url'] = None
            
            # Extract image URL
            img_element = card_element.select_one(config.SELECTORS['image'])
            if img_element:
                # Try different attributes for lazy-loaded images
                img_src = (img_element.get('data-src') or 
                          img_element.get('data-original') or 
                          img_element.get('data-lazy-src') or
                          img_element.get('src'))
                
                if img_src:
                    full_img_url = build_absolute_url(config.BASE_URL, img_src)
                    # Filter out loading/placeholder GIFs
                    if 'cargador.gif' in full_img_url or 'loading' in full_img_url.lower():
                        product['image_url'] = None
                    else:
                        product['image_url'] = full_img_url
                else:
                    product['image_url'] = None
            else:
                product['image_url'] = None
            
            # Extract availability
            availability_element = card_element.select_one(config.SELECTORS['availability'])
            if availability_element:
                product['availability'] = determine_availability(availability_element.get_text())
            else:
                # Try to infer from price availability
                if product['price'] is None:
                    product['availability'] = "OutOfStock"
                else:
                    product['availability'] = "Unknown"
            
            # Set main category and extract subcategory from URL
            product['main_category'] = config.CATEGORIES_CONFIG[category]['name']
            
            if product['product_url']:
                # Try to extract subcategory from URL
                subcategories_map = config.SUBCATEGORIES.get(category, {})
                product['subcategory'] = extract_category_from_url(product['product_url'], subcategories_map)
                
                # Legacy category field for backward compatibility
                product['category'] = product['subcategory'] or product['main_category']
            else:
                product['subcategory'] = None
                product['category'] = product['main_category']
            
            # Initialize other fields
            product['system'] = None
            product['finish'] = None
            product['length'] = None
            product['scraped_from_page'] = page_number
            
            # Try to extract system and finish from product name
            name_lower = product['name'].lower() if product['name'] else ""
            
            # Extract system
            for system_key, system_value in config.SYSTEMS.items():
                if system_key.replace('-', ' ') in name_lower:
                    product['system'] = system_value
                    break
            
            # Extract finish
            for finish_key, finish_value in config.FINISHES.items():
                if finish_key in name_lower:
                    product['finish'] = finish_value
                    break
            
            return product
            
        except Exception as e:
            self.logger.error(f"Error extracting product data on page {page_number}: {e}")
            return None
    
    def scrape_product_details(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape detailed information from individual product page."""
        if not product.get('product_url'):
            return product
            
        try:
            self.logger.debug(f"Scraping details for: {product.get('name', 'Unknown')}")
            response = self.make_request(product['product_url'])
            if not response:
                return product
                
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract real product image
            real_image = self._extract_real_image(soup)
            if real_image:
                product['image_url'] = real_image
            
            # Extract detailed attributes
            attributes = self._extract_attributes(soup)
            product.update(attributes)
            
            # Extract product variants (if any)
            variants = self._extract_variants(soup)
            if variants:
                product['variants'] = variants
                
            # Extract detailed description
            description = self._extract_description(soup)
            if description:
                product['description'] = description
            
            # Generate LLM description if enabled
            if self.generate_descriptions and self.openai_client:
                llm_description = self._generate_llm_description(product)
                if llm_description:
                    product['ai_description'] = llm_description
                
            return product
            
        except Exception as e:
            self.logger.error(f"Error scraping details for {product.get('name', 'Unknown')}: {e}")
            return product
    
    def _extract_real_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the real product image from detail page."""
        # Look for image in gallery
        img_selectors = [
            '.galeria_fotos .swiper-slide img',
            '.producto__imagenes img[src*="productos"]',
            '.swiper-slide img[src*="productos"]'
        ]
        
        for selector in img_selectors:
            img_element = soup.select_one(selector)
            if img_element:
                img_src = img_element.get('src')
                if img_src and 'productos' in img_src and 'cargador.gif' not in img_src:
                    return build_absolute_url(config.BASE_URL, img_src)
        
        return None
    
    def _extract_attributes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract detailed product attributes."""
        attributes = {}
        
        # Extract from attributes section
        attr_rows = soup.select('.atributos__items--fila')
        for row in attr_rows:
            item = row.select_one('.atributos__items--fila--item strong')
            value = row.select_one('.atributos__items--fila--valor p')
            
            if item and value:
                key = clean_text(item.get_text()).replace(':', '').lower()
                val = clean_text(value.get_text())
                
                # Map Spanish attribute names to English
                attr_mapping = {
                    'material': 'material',
                    'terminación': 'finish',
                    'terminacion': 'finish', 
                    'color': 'color',
                    'sistema': 'system',
                    'combina con': 'compatible_with',
                    'largo': 'length',
                    'ancho': 'width',
                    'alto': 'height',
                    'espesor': 'thickness'
                }
                
                mapped_key = attr_mapping.get(key, key)
                attributes[mapped_key] = val
        
        return attributes
    
    def _extract_variants(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract product variants with individual SKUs and prices."""
        variants = []
        
        # Look for variant options in select dropdown
        variant_options = soup.select('#combo_variente option[value]:not([value=""])')
        
        for option in variant_options:
            variant_id = option.get('value')
            if not variant_id:
                continue
                
            option_text = clean_text(option.get_text())
            if not option_text or option_text == 'Seleccione':
                continue
                
            # Parse option text: "SKU - Description"
            if ' - ' in option_text:
                sku, description = option_text.split(' - ', 1)
                sku = sku.strip()
                description = description.strip()
            else:
                sku = variant_id
                description = option_text
            
            # Extract price from hidden input
            price_input = soup.select_one(f'#precio_{variant_id}')
            price = None
            if price_input:
                price_text = price_input.get('value', '')
                if price_text:
                    try:
                        # Convert comma decimal to dot decimal
                        price_text = price_text.replace(',', '.')
                        price = float(price_text)
                    except ValueError:
                        pass
            
            # Extract cutting length
            corte_input = soup.select_one(f'#corte_{variant_id}')
            cutting_length = None
            if corte_input:
                corte_value = corte_input.get('value', '')
                if corte_value:
                    try:
                        cutting_length = int(corte_value)
                    except ValueError:
                        pass
            
            variant = {
                'variant_id': variant_id,
                'sku': sku,
                'description': description,
                'price': price,
                'cutting_length_mm': cutting_length
            }
            
            variants.append(variant)
        
        return variants
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description."""
        # Look for main product title
        title_element = soup.select_one('.producto__info--fav h1')
        if title_element:
            return clean_text(title_element.get_text())
        
        return None
    
    def _generate_llm_description(self, product: Dict[str, Any]) -> Optional[str]:
        """Generate AI description using GPT-4o."""
        try:
            # Prepare product context
            context_parts = []
            
            # Basic info
            if product.get('name'):
                context_parts.append(f"Product Name: {product['name']}")
            if product.get('sku'):
                context_parts.append(f"SKU: {product['sku']}")
            if product.get('main_category'):
                context_parts.append(f"Category: {product['main_category']}")
            
            # Attributes
            attributes = []
            for attr in ['material', 'finish', 'system', 'color', 'compatible_with']:
                if product.get(attr):
                    attributes.append(f"{attr.title()}: {product[attr]}")
            
            if attributes:
                context_parts.append("Attributes: " + ", ".join(attributes))
            
            # Variants info
            if product.get('variants'):
                variant_count = len(product['variants'])
                price_range = []
                sizes = []
                
                for variant in product['variants']:
                    if variant.get('price'):
                        price_range.append(variant['price'])
                    
                    # Extract size info from description
                    desc = variant.get('description', '')
                    if 'X' in desc and 'MM' in desc.upper():
                        # Extract dimensions like "10.00 X 10.00 X 1.50"
                        import re
                        size_match = re.search(r'(\d+\.?\d*)\s*X\s*(\d+\.?\d*)', desc)
                        if size_match:
                            sizes.append(f"{size_match.group(1)}x{size_match.group(2)}mm")
                
                context_parts.append(f"Available in {variant_count} variants")
                
                if price_range:
                    min_price = min(price_range)
                    max_price = max(price_range)
                    if min_price == max_price:
                        context_parts.append(f"Price: ${min_price:.2f}")
                    else:
                        context_parts.append(f"Price range: ${min_price:.2f} - ${max_price:.2f}")
                
                if sizes:
                    unique_sizes = list(set(sizes[:5]))  # Show up to 5 unique sizes
                    context_parts.append(f"Available sizes: {', '.join(unique_sizes)}")
            
            context = "\n".join(context_parts)
            
            prompt = f"""You are an expert in aluminum construction materials and profiles. Based on the following product information, write a concise, professional product description suitable for a construction materials catalog.

Product Information:
{context}

Write a 2-3 sentence description that:
1. Explains what the product is and its primary use
2. Highlights key features, materials, and finishes
3. Mentions applications or industries where it's commonly used
4. Uses technical but accessible language

Focus on practical construction applications. Do not mention pricing or availability."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            description = response.choices[0].message.content.strip()
            self.logger.debug(f"Generated description for {product.get('name', 'Unknown')}")
            return description
            
        except Exception as e:
            self.logger.error(f"Error generating LLM description for {product.get('name', 'Unknown')}: {e}")
            return None
    
    def scrape_page(self, page_url: str, page_number: int, category: str) -> List[Dict[str, Any]]:
        """Scrape products from a single page."""
        self.logger.info(f"Scraping {category} page {page_number}: {page_url}")
        
        response = self.make_request(page_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        product_cards = soup.select(config.SELECTORS['product_cards'])
        
        if not product_cards:
            self.logger.warning(f"No product cards found on {category} page {page_number}")
            return []
        
        page_products = []
        for card in product_cards:
            product_data = self.extract_product_data(card, page_number, category)
            if product_data and validate_product_data(product_data, config.REQUIRED_FIELDS):
                # Optionally scrape detailed information
                if self.detailed_scraping:
                    product_data = self.scrape_product_details(product_data)
                
                page_products.append(product_data)
            elif product_data:
                self.logger.warning(f"Product data validation failed: {product_data}")
        
        self.logger.info(f"Extracted {len(page_products)} products from {category} page {page_number}")
        return page_products
    
    def get_pagination_urls(self, base_page_url: str, category: str) -> List[str]:
        """Get all pagination URLs from the first page."""
        self.logger.info(f"Discovering {category} pagination URLs...")
        
        response = self.make_request(base_page_url)
        if not response:
            return [base_page_url]
        
        soup = BeautifulSoup(response.content, 'lxml')
        pagination_links = soup.select(config.SELECTORS['pagination'])
        
        page_urls = [base_page_url]  # Include first page
        
        for link in pagination_links:
            href = link.get('href')
            if href and href != '#':
                full_url = build_absolute_url(config.BASE_URL, href)
                if validate_url(full_url) and full_url not in page_urls:
                    page_urls.append(full_url)
        
        # Sort URLs by page number if possible
        def extract_page_number(url):
            try:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                if 'page' in query_params:
                    return int(query_params['page'][0])
                elif '/n' in parsed.path:
                    # Extract from path like /n1-4/ or /n2-4/
                    match = re.search(r'/n(\d+)-', parsed.path)
                    if match:
                        return int(match.group(1))
            except (ValueError, AttributeError):
                pass
            return 0
        
        page_urls.sort(key=extract_page_number)
        
        self.logger.info(f"Found {len(page_urls)} {category} pages to scrape")
        return page_urls
    
    def scrape_category(self, category: str, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape all products from a specific category."""
        category_config = config.CATEGORIES_CONFIG[category]
        category_url = category_config['url']
        
        self.logger.info(f"Starting {category} scrape")
        
        # Get all pagination URLs for this category
        page_urls = self.get_pagination_urls(category_url, category)
        
        # Filter pages based on start/end parameters
        if start_page > 1 or end_page:
            if end_page:
                page_urls = page_urls[start_page-1:end_page]
            else:
                page_urls = page_urls[start_page-1:]
        
        self.logger.info(f"Will scrape {len(page_urls)} {category} pages")
        
        category_products = []
        
        # Scrape each page with progress bar
        desc = f"Scraping {category}"
        with tqdm(total=len(page_urls), desc=desc) as pbar:
            for i, page_url in enumerate(page_urls, 1):
                try:
                    page_products = self.scrape_page(page_url, i, category)
                    category_products.extend(page_products)
                    self.products_by_category[category].extend(page_products)
                    pbar.set_postfix({
                        f'{category}': len(category_products),
                        'Success Rate': f"{calculate_success_rate(self.total_requests, self.successful_requests):.1f}%"
                    })
                    pbar.update(1)
                    
                except Exception as e:
                    self.logger.error(f"Error scraping {category} page {i} ({page_url}): {e}")
                    pbar.update(1)
                    continue
        
        self.logger.info(f"{category} scraping completed: {len(category_products)} products")
        return category_products

    def scrape_all_products(self, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape all products from all specified categories."""
        self.start_time = datetime.now()
        self.logger.info(f"Starting multi-category scrape at {self.start_time}")
        self.logger.info(f"Categories to scrape: {', '.join(self.categories)}")
        
        all_products = []
        
        # Scrape each category
        for category in self.categories:
            try:
                category_products = self.scrape_category(category, start_page, end_page)
                all_products.extend(category_products)
            except Exception as e:
                self.logger.error(f"Error scraping category {category}: {e}")
                continue
        
        self.products = all_products
        self.end_time = datetime.now()
        self.logger.info(f"Multi-category scraping completed at {self.end_time}")
        self.logger.info(f"Total products scraped: {len(self.products)}")
        
        # Log category breakdown
        for category in self.categories:
            count = len(self.products_by_category[category])
            self.logger.info(f"  {category}: {count} products")
        
        return self.products
    
    def save_results(self) -> bool:
        """Save scraping results to JSON file."""
        if not self.products:
            self.logger.warning("No products to save")
            return False
        
        # Create metadata
        metadata = create_scrape_metadata(
            total_products=len(self.products),
            pages_scraped=len({p.get('scraped_from_page', 0) for p in self.products}),
            base_url=config.BASE_URL,
            start_time=self.start_time or datetime.now(),
            end_time=self.end_time or datetime.now(),
            success_rate=calculate_success_rate(self.total_requests, self.successful_requests)
        )
        
        # Add category-specific metadata
        metadata['categories_scraped'] = self.categories
        metadata['products_by_category'] = {
            category: len(products) for category, products in self.products_by_category.items()
        }
        
        # Create final output structure
        output_data = {
            "scrape_metadata": metadata,
            "products": self.products
        }
        
        # Save to file
        success = save_json(output_data, self.output_file)
        if success:
            self.logger.info(f"Results saved to {self.output_file}")
        else:
            self.logger.error(f"Failed to save results to {self.output_file}")
        
        return success
    
    def run(self, start_page: int = 1, end_page: Optional[int] = None) -> bool:
        """Run the complete scraping process."""
        try:
            self.logger.info("=== Aluminios.com Product Scraper Started ===")
            
            # Scrape all products
            products = self.scrape_all_products(start_page, end_page)
            
            # Save results
            success = self.save_results()
            
            # Log summary
            self.logger.info("=== Scraping Summary ===")
            self.logger.info(f"Total products scraped: {len(products)}")
            self.logger.info(f"Total requests made: {self.total_requests}")
            self.logger.info(f"Success rate: {calculate_success_rate(self.total_requests, self.successful_requests):.1f}%")
            if self.start_time and self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
                self.logger.info(f"Total duration: {format_duration(duration)}")
            
            return success
            
        except KeyboardInterrupt:
            self.logger.info("Scraping interrupted by user")
            if self.products:
                self.logger.info("Saving partial results...")
                self.save_results()
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error during scraping: {e}")
            return False


def main():
    """Main entry point with CLI interface."""
    parser = argparse.ArgumentParser(description="Scrape products from shop.aluminios.com")
    parser.add_argument("--output", "-o", default=config.DEFAULT_OUTPUT_FILE,
                       help="Output JSON file path")
    parser.add_argument("--delay", "-d", type=float, default=config.DEFAULT_DELAY,
                       help="Delay between requests in seconds")
    valid_categories = list(config.CATEGORIES_CONFIG.keys()) + ['all']
    parser.add_argument("--categories", "-c", nargs='+', 
                       choices=valid_categories,
                       default=['all'],
                       help="Categories to scrape (default: all categories)")
    parser.add_argument("--start-page", type=int, default=1,
                       help="Starting page number")
    parser.add_argument("--end-page", type=int, default=None,
                       help="Ending page number (optional)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--detailed", action="store_true",
                       help="Enable detailed scraping (visits each product page for more info)")
    parser.add_argument("--generate-descriptions", action="store_true",
                       help="Generate AI descriptions using GPT-4o (requires --detailed and OPENAI_API_KEY)")
    
    args = parser.parse_args()
    
    # Handle category selection
    categories = args.categories
    if 'all' in categories:
        categories = list(config.CATEGORIES_CONFIG.keys())
    
    # Auto-select output file if not specified
    output_file = args.output
    if output_file == config.DEFAULT_OUTPUT_FILE:
        if len(categories) > 1:
            output_file = config.CATEGORY_OUTPUT_FILES['all']
        elif len(categories) == 1:
            category_key = categories[0]
            if category_key in config.CATEGORY_OUTPUT_FILES:
                output_file = config.CATEGORY_OUTPUT_FILES[category_key]
    
    # Create logs directory
    os.makedirs(config.LOG_DIRECTORY, exist_ok=True)
    
    # Validate arguments
    if args.generate_descriptions and not args.detailed:
        print("Error: --generate-descriptions requires --detailed to be enabled")
        return 1
    
    # Initialize scraper
    scraper = AluminiosProductScraper(
        delay=args.delay,
        output_file=output_file,
        categories=categories,
        detailed_scraping=args.detailed,
        generate_descriptions=args.generate_descriptions
    )
    
    # Set logging level
    if args.verbose:
        scraper.logger.setLevel(logging.DEBUG)
    
    # Run scraper
    success = scraper.run(args.start_page, args.end_page)
    
    if success:
        print(f"✅ Scraping completed successfully! Results saved to {args.output}")
        return 0
    else:
        print("❌ Scraping failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit(main())

import os
from flask import Flask, render_template, request, jsonify, Response
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import json
import io
import time
import traceback
from datetime import datetime

app = Flask(__name__)

def scrape_beacons_roster(url):
    driver = None
    try:
        print(f"\n{'='*80}\nStarting scrape of URL: {url}\n{'='*80}\n")
        
        # Initialize undetected-chromedriver
        options = uc.ChromeOptions()
        options.add_argument('--window-size=1920,1080')
        
        try:
            driver = uc.Chrome(options=options)
            driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            return None, f"Failed to initialize Chrome driver: {str(e)}"
        
        print("\nNavigating to URL...")
        try:
            driver.get(url)
        except TimeoutException:
            return None, "Page load timed out. Please try again."
        
        # Wait for initial page load
        print("\nWaiting for page load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for Cloudflare to clear
        print("\nWaiting for Cloudflare check...")
        time.sleep(10)
        
        print("\nPage title:", driver.title)
        print("Current URL:", driver.current_url)
        
        # Function to check if content is loaded
        def is_content_loaded():
            try:
                # Try different indicators that content is loaded
                return driver.execute_script("""
                    // Check if we see any creator-like content
                    const hasCreatorContent = document.body.innerHTML.toLowerCase().includes('creator') ||
                                           document.body.innerHTML.toLowerCase().includes('roster') ||
                                           document.body.innerHTML.toLowerCase().includes('profile');
                    
                    // Check if we see social media links
                    const hasSocialLinks = document.body.innerHTML.includes('instagram.com') ||
                                         document.body.innerHTML.includes('tiktok.com');
                    
                    // Check if we see typical metrics
                    const hasMetrics = document.body.innerHTML.includes('%') &&
                                     (document.body.innerHTML.toLowerCase().includes('engagement') ||
                                      document.body.innerHTML.toLowerCase().includes('female') ||
                                      document.body.innerHTML.toLowerCase().includes('male'));
                    
                    // Check if we have any grid or list structures
                    const hasStructure = document.querySelector('[role="grid"], [role="list"], [class*="grid"], [class*="list"]') !== null;
                    
                    console.log('Content check:', {
                        hasCreatorContent,
                        hasSocialLinks,
                        hasMetrics,
                        hasStructure
                    });
                    
                    return hasCreatorContent && (hasSocialLinks || hasMetrics || hasStructure);
                """)
            except:
                return False
        
        # Wait for content with timeout
        print("\nWaiting for content to load...")
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if is_content_loaded():
                print("Content detected!")
                break
            print("Waiting for content...")
            time.sleep(2)
        
        # Additional wait for any animations
        time.sleep(5)
        
        # Try to scroll the page to trigger lazy loading
        print("\nScrolling page to trigger lazy loading...")
        driver.execute_script("""
            function smoothScroll() {
                const height = document.body.scrollHeight;
                const steps = 10;
                const delay = 200;
                
                for (let i = 0; i <= steps; i++) {
                    setTimeout(() => {
                        const nextPos = (i / steps) * height;
                        window.scrollTo(0, nextPos);
                    }, i * delay);
                }
                
                // Scroll back to top
                setTimeout(() => window.scrollTo(0, 0), (steps + 1) * delay);
            }
            smoothScroll();
        """)
        
        # Wait for any lazy loaded content
        time.sleep(5)
        
        # Try to find content using JavaScript with more specific selectors
        print("\nSearching for creator data...")
        creators = driver.execute_script("""
            function findCreators() {
                // Helper function to extract text content
                function getTextContent(element) {
                    return element ? (element.textContent || '').trim() : '';
                }
                
                // Helper function to check if element is in sidebar
                function isInSidebar(element) {
                    let current = element;
                    while (current) {
                        // Check for common sidebar indicators
                        const classNames = (current.className || '').toLowerCase();
                        const id = (current.id || '').toLowerCase();
                        
                        if (
                            classNames.includes('sidebar') ||
                            classNames.includes('side-bar') ||
                            classNames.includes('side_bar') ||
                            id.includes('sidebar') ||
                            id.includes('side-bar') ||
                            id.includes('side_bar') ||
                            // Check for common layout patterns
                            classNames.includes('aside') ||
                            classNames.includes('drawer') ||
                            classNames.includes('panel') ||
                            // Check position
                            (window.getComputedStyle(current).position === 'fixed' && 
                             (current.getBoundingClientRect().left === 0 || 
                              current.getBoundingClientRect().right === window.innerWidth))
                        ) {
                            return true;
                        }
                        current = current.parentElement;
                    }
                    return false;
                }

                // Helper function to extract handle from social media URL
                function extractHandle(url, platform) {
                    if (!url) return '';
                    let match;
                    if (platform === 'instagram') {
                        match = url.match(/instagram\.com\/([^/?]+)/);
                    } else if (platform === 'tiktok') {
                        match = url.match(/tiktok\.com\/@([^/?]+)/);
                    }
                    return match ? '@' + match[1] : '';
                }
                
                const creators = new Set();
                
                // First, try to find the main content area
                const mainContent = document.querySelector(
                    'main, [role="main"], [id*="main"], [class*="main"], ' +
                    '[id*="content"], [class*="content"], [role="grid"], ' +
                    '[class*="grid"], [class*="list"], [class*="roster"]'
                );
                
                // If we found a main content area, search within it
                const searchRoot = mainContent || document.body;
                
                // Try different selectors for creator cards
                const selectors = [
                    // Common card selectors
                    '[class*="creator"]',
                    '[class*="roster"]',
                    '[class*="member"]',
                    '[class*="card"]',
                    '[class*="profile"]',
                    // Grid/list selectors
                    '[role="grid"] > *',
                    '[role="list"] > *',
                    // Table selectors
                    'tr[class*="row"]',
                    // Specific Beacons selectors
                    '[data-testid*="creator"]',
                    '[data-testid*="roster"]',
                    // Try more general selectors
                    'div[class*="item"]',
                    'div[class*="cell"]',
                    'div[class*="box"]'
                ];
                
                // Find all potential creator elements
                const potentialCreators = new Set();
                for (const selector of selectors) {
                    try {
                        const elements = searchRoot.querySelectorAll(selector);
                        elements.forEach(el => {
                            // Skip elements in sidebar
                            if (isInSidebar(el)) {
                                return;
                            }
                            
                            // Check if this element or its children have social links or @ mentions
                            const html = el.innerHTML.toLowerCase();
                            // Skip elements that look like roster owner info
                            if (html.includes('total creators') || 
                                html.includes('total reach') || 
                                html.includes('talent management') ||
                                html.includes('@clique-now.com')) {
                                return;
                            }
                            if (html.includes('instagram.com') || 
                                html.includes('tiktok.com') || 
                                html.includes('@') ||
                                html.includes('engagement') ||
                                html.includes('female') ||
                                html.includes('male')) {
                                potentialCreators.add(el);
                            }
                        });
                    } catch (e) {
                        console.error('Error with selector:', selector, e);
                    }
                }
                
                console.log('Found', potentialCreators.size, 'potential creator elements');
                
                // Process each potential creator element
                for (const element of potentialCreators) {
                    try {
                        const creatorInfo = {};
                        
                        // Debug info
                        console.log('Processing element:', {
                            class: element.className,
                            id: element.id,
                            html: element.outerHTML.slice(0, 200)
                        });
                        
                        // Get all text content first
                        const allText = element.textContent;
                        console.log('Element text:', allText.slice(0, 200));
                        
                        // Look for name in headers or strong/b tags first
                        const nameElements = element.querySelectorAll('h1,h2,h3,h4,h5,h6,strong,b');
                        console.log('Checking element for name:', element.outerHTML.slice(0, 200));
                        
                        for (const el of nameElements) {
                            const text = getTextContent(el);
                            console.log('Potential name text:', text);
                            // Skip common UI text that might be mistaken for names
                            if (text && 
                                !text.includes('@') && 
                                !text.includes('http') && 
                                !text.match(/\d{3,}/) &&
                                !text.toLowerCase().includes('filter') &&
                                !text.toLowerCase().includes('menu') &&
                                !text.toLowerCase().includes('button') &&
                                !text.toLowerCase().includes('search') &&
                                !text.toLowerCase().includes('sort') &&
                                !text.toLowerCase().includes('default') &&
                                text.length > 1) {
                                creatorInfo.name = text.trim();
                                console.log('Found name:', creatorInfo.name);
                                break;
                            }
                        }
                        
                        // If no name found in headers, look for first text node that's not a number or link
                        if (!creatorInfo.name) {
                            const walker = document.createTreeWalker(
                                element,
                                NodeFilter.SHOW_TEXT,
                                null,
                                false
                            );
                            let node;
                            while (node = walker.nextNode()) {
                                const text = node.textContent.trim();
                                console.log('Checking text node:', text);
                                if (text && 
                                    !text.includes('@') && 
                                    !text.includes('http') && 
                                    !text.match(/\d{3,}/) &&
                                    !text.toLowerCase().includes('filter') &&
                                    !text.toLowerCase().includes('menu') &&
                                    !text.toLowerCase().includes('button') &&
                                    !text.toLowerCase().includes('search') &&
                                    !text.toLowerCase().includes('sort') &&
                                    !text.toLowerCase().includes('default') &&
                                    text.length > 1) {
                                    creatorInfo.name = text;
                                    console.log('Found name from text node:', creatorInfo.name);
                                    break;
                                }
                            }
                        }
                        
                        // Extract follower counts from links
                        const links = element.getElementsByTagName('a');
                        for (const link of links) {
                            const href = link.href || '';
                            const linkText = getTextContent(link);
                            // Match number followed by optional decimal and optional K/M suffix
                            const followerMatch = linkText.match(/(\d+(?:\.\d+)?)\s*[KkMm]?/);
                            const followerCount = followerMatch ? followerMatch[0].trim() : '';
                            
                            if (href.includes('tiktok.com')) {
                                creatorInfo.tiktok_link = href;
                                creatorInfo.tiktok_handle = extractHandle(href, 'tiktok');
                                if (followerCount) creatorInfo.tiktok_followers = followerCount;
                            } else if (href.includes('instagram.com')) {
                                creatorInfo.instagram_link = href;
                                creatorInfo.instagram_handle = extractHandle(href, 'instagram');
                                if (followerCount) creatorInfo.instagram_followers = followerCount;
                            } else if (href.includes('youtube.com')) {
                                creatorInfo.youtube_link = href;
                                if (followerCount) creatorInfo.youtube_subscribers = followerCount;
                            }
                        }
                        
                        // Look for metrics
                        const metricTexts = Array.from(element.querySelectorAll('*')).map(el => getTextContent(el));
                        for (const text of metricTexts) {
                            if (text.includes('%')) {
                                if (text.toLowerCase().includes('engagement')) {
                                    // Extract number and % only
                                    const match = text.match(/(\d+(?:\.\d+)?)\s*%/);
                                    if (match) {
                                        creatorInfo.engagement = match[1] + '% rate';
                                    }
                                } else if (text.toLowerCase().includes('female') || text.toLowerCase().includes('male')) {
                                    // Extract number and gender only
                                    const match = text.match(/(\d+(?:\.\d+)?)\s*%\s*(fe)?male/i);
                                    if (match) {
                                        const [_, number, isFemale] = match;
                                        creatorInfo.top_gender = `${number}% ${isFemale ? 'Female' : 'Male'}`;
                                    }
                                }
                            } else if (text.includes('18-24') || text.includes('25-34')) {
                                creatorInfo.top_age = text;
                            }
                        }
                        
                        // Only add if we have meaningful data and it's not just empty fields
                        if (creatorInfo.name || creatorInfo.tiktok_link || creatorInfo.instagram_link) {
                            // Ensure name is present and valid
                            if (!creatorInfo.name && creatorInfo.tiktok_handle) {
                                creatorInfo.name = creatorInfo.tiktok_handle;
                            }
                            
                            // Skip if the name is not valid
                            if (!creatorInfo.name || 
                                creatorInfo.name.toLowerCase() === 'default' ||
                                creatorInfo.name.length <= 1) {
                                console.log('Skipping invalid name:', creatorInfo.name);
                                continue;
                            }
                            
                            console.log('Found creator:', creatorInfo);
                            creators.add(JSON.stringify(creatorInfo));
                        }
                        
                    } catch (e) {
                        console.error('Error processing element:', e);
                    }
                }
                
                return Array.from(creators).map(str => JSON.parse(str));
            }
            
            return findCreators();
        """)
        
        if not creators:
            print("\nNo creators found. Debug information:")
            print("\nPage source preview:")
            print(driver.page_source[:2000])  # Show more of the page source
            
            # Take a screenshot
            print("\nTaking screenshot...")
            driver.save_screenshot("debug_screenshot.png")
            
            # Try to get any error messages
            error_elements = driver.find_elements(By.CSS_SELECTOR, '.error,#error,[class*="error"],[id*="error"]')
            if error_elements:
                print("\nFound error messages on page:")
                for elem in error_elements:
                    print(elem.text)
            
            return None, "No creators found. The page might be using a different structure or might require authentication."
        
        print(f"\nFound {len(creators)} creators")
        print("\nFirst few creators found:")
        
        # Debug: print raw creators data
        print("Raw creators data:")
        creators_list = []
        for creator in creators:
            try:
                if isinstance(creator, str):
                    creator_dict = json.loads(creator)
                else:
                    creator_dict = creator
                creators_list.append(creator_dict)
                print(json.dumps(creator_dict, indent=2))
            except json.JSONDecodeError as e:
                print(f"Error parsing creator data: {e}")
                print(f"Problematic creator data: {creator}")
        
        # Convert to DataFrame and CSV
        df = pd.DataFrame(creators_list)
        
        # Remove any duplicate entries based on name
        if not df.empty and 'name' in df.columns:
            # Remove rows with invalid names
            df = df[df['name'].notna()]  # Remove None values
            df = df[df['name'].str.strip() != '']  # Remove empty strings
            df = df[~df['name'].str.lower().isin(['default', 'filter', 'menu', 'button', 'search', 'sort'])]  # Remove UI elements
            
            # Then remove duplicates
            df = df.drop_duplicates(subset=['name'], keep='first')
        
        # Reorder columns to put name first and organize social media metrics together
        column_order = ['name', 
                      'instagram_handle', 'instagram_followers', 'instagram_link',
                      'tiktok_handle', 'tiktok_followers', 'tiktok_link',
                      'youtube_subscribers', 'youtube_link',
                      'engagement', 'top_gender', 'top_age']
        
        # Only include columns that exist in the DataFrame
        final_columns = [col for col in column_order if col in df.columns]
        df = df[final_columns]
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return csv_buffer.getvalue(), None
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return None, f"An error occurred while scraping: {str(e)}"
    
    finally:
        if driver:
            try:
                driver.quit()
                print("WebDriver closed successfully")
            except Exception as e:
                print(f"Error closing WebDriver: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()  # Try form data if JSON fails
            
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        if 'beacons.ai' not in url:
            return jsonify({'error': 'Please provide a valid Beacons.ai URL'}), 400
            
        csv_data, error = scrape_beacons_roster(url)
        if error:
            return jsonify({'error': error}), 400
            
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=creators.csv'
            }
        )
        
    except Exception as e:
        print(f"Error in /scrape endpoint: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)

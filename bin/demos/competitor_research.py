import json
import time
import sys
import argparse
import requests
import os

def demo_searcher(target_topic):
    print("\n[STEP 1] The Searcher (SearXNG Proxy)")
    print(f"Agent Goal: 'Find me recent articles discussing {target_topic}.'")
    print("...")
    
    # We are running inside the sandbox container (192.168.97.10), so localhost
    # points to the sandbox itself. We need to reach the host machine where the
    # docker containers mapped their ports. In Docker desktop/OrbStack, host.docker.internal works.
    searxng_port = os.environ.get("SEARXNG_PORT", "9003")
    url = f"http://host.docker.internal:{searxng_port}/search"
    params = {
        "q": target_topic,
        "format": "json",
        "engines": "google,duckduckgo,bing"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract the top 3 results
        results = data.get("results", [])[:3]
        formatted_results = [{"title": r.get("title"), "url": r.get("url")} for r in results]
        
        print("Searcher returned raw URLs:")
        print(json.dumps(formatted_results, indent=2))
        return formatted_results
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling SearXNG API: {e}")
        print("Ensure the SearXNG container is running (make -C services/searchers/searxng up).")
        return []

def demo_fetcher(urls):
    print("\n[STEP 2] The Fetcher (Crawl4AI Proxy)")
    if len(urls) > 0:
        target_url = urls[0]['url']
        print(f"Agent Goal: 'Grab the raw text from the first result so I can read about it.'")
        print(f"Target URL: {target_url}")
        print("...")

        crawl4ai_port = os.environ.get("CRAWL4AI_PORT", "11235")
        url = f"http://host.docker.internal:{crawl4ai_port}/crawl"
        
        # According to standard crawl4ai API, it takes a URL in the payload
        payload = {
            "urls": target_url,
            "word_count_threshold": 10
        }
        headers = {"Content-Type": "application/json"}
        
        # In this specific deployment, CRAWL4AI_API_TOKEN is set
        api_token = os.environ.get("CRAWL4AI_API_TOKEN")
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # The API usually returns a task ID or the result directly. 
            # Assuming synchronous return for simplicity if supported, or extracting markdown.
            markdown_content = "Extracted content not found in expected format."
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                if "markdown" in result:
                     markdown_content = result["markdown"]
                elif "html" in result:
                     markdown_content = result["html"] # Fallback if markdown missing
            
            # Truncate to 500 characters for demo output
            truncated_markdown = markdown_content[:500] + ("..." if len(markdown_content) > 500 else "")
            
            print("Fetcher returned clean, LLM-ready Markdown (ads and navbars stripped):")
            print(truncated_markdown.strip())
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Crawl4AI API: {e}")
            print("Ensure the Crawl4AI container is running (make -C services/fetchers/crawl4ai up).")

def demo_browser(urls):
    print("\n[STEP 3] The Browser (Browser Use Proxy)")
    
    target_url = urls[-1]['url'] if urls else "https://example.com"
    
    print(f"Agent Goal: 'Navigate to the last page and summarize what you see using AI vision/DOM parsing.'")
    print(f"Target URL: {target_url}")
    print("...")

    browseruse_port = os.environ.get("BROWSERUSE_PORT", "8080")
    # Using the standard /run endpoint for reqeique/browser-use-api
    url = f"http://host.docker.internal:{browseruse_port}/run"
    
    # We pass a natural language task to the Browser Use API
    payload = {
        "task": f"Go to {target_url}, find the pricing or main product description, and return a 1 sentence summary of the lowest cost or main feature.",
        "return_type": "string"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        print("Sending natural language task to Browser Use... (this may take 15-30 seconds as it actually drives a browser)")
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # The result is typically stored in the 'result' key
        result_text = data.get("result", "No result returned.")
        
        print("\nResult from autonomous browser session:")
        print(result_text)
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Browser Use API: {e}")
        print("Ensure the Browser Use container is running (make -C services/browsers/browseruse up) and active-proxy is reachable.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Competitor Intelligence Demo using LIVE APIS.')
    parser.add_argument('topic', nargs='?', default='alternatives to Notion', help='The topic to research')
    args = parser.parse_args()

    print("==================================================")
    print(f"MetaClaw Tier 0 Demonstration: Researching '{args.topic}'")
    print("==================================================")
    
    found_urls = demo_searcher(args.topic)
    demo_fetcher(found_urls)
    demo_browser(found_urls)
    
    print("\n==================================================")
    print("Demonstration Complete. Handoff successful.")
    print("==================================================")

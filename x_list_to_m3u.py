import time
import os
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
X_LIST_URL = "https://x.com/i/lists/1814228268662587775"  # <-- Ensure your list ID is here
OUTPUT_FILENAME = "x_video_playlist.m3u"
SCROLL_DURATION = 20 
# ---------------------

def extract_video_links():
    video_urls = []
    
    # Retrieve securely hidden cookies from GitHub Environment
    auth_token = os.environ.get("X_AUTH_TOKEN")
    ct0 = os.environ.get("X_CT0")

    if not auth_token or not ct0:
        print("CRITICAL ERROR: GitHub Secrets (X_AUTH_TOKEN or X_CT0) are missing!")
        return []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Inject cookies to simulate an active, logged-in user session
        context.add_cookies([
            {"name": "auth_token", "value": auth_token, "domain": ".x.com", "path": "/"},
            {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/"}
        ])
        
        page = context.new_page()
        
        print(f"Opening X List securely: {X_LIST_URL}")
        page.goto(X_LIST_URL)
        page.wait_for_timeout(7000)  # Give the authenticated timeline time to load
        
        discovered_videos = {}
        
        def handle_response(response):
            url = response.url
            if "://twimg.com" in url and (".m3u8" in url or ".mp4" in url):
                base_url = url.split("?")[0]
                if base_url not in discovered_videos:
                    discovered_videos[base_url] = url

        page.on("response", handle_response)

        # Scroll to discover video posts
        start_time = time.time()
        while time.time() - start_time < SCROLL_DURATION:
            page.evaluate("window.scrollBy(0, 1000);")
            page.wait_for_timeout(1500)
            
        browser.close()
        video_urls = list(discovered_videos.values())
        
    return video_urls

def generate_m3u(urls):
    if not urls:
        print("No videos found. Verify your cookies are valid and your List contains active video tweets.")
        # Create a placeholder track so the Apple TV app doesn't throw a parsing error
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXTINF:-1, No Videos Found - Check Logs\n")
            f.write("https://localhost/placeholder.mp4\n")
        return

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for i, url in enumerate(urls, start=1):
            clean_url = url.replace("&amp;", "&")
            f.write(f"#EXTINF:-1 tvg-id=\"X_{i}\" tvg-name=\"X Video {i}\", X Video {i}\n")
            f.write(f"{clean_url}\n")
            
    print(f"Success! Created {OUTPUT_FILENAME} with {len(urls)} videos.")

if __name__ == "__main__":
    detected_links = extract_video_links()
    generate_m3u(detected_links)

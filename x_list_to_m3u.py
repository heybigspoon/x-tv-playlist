import time
import re
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
# Replace this with your public X List URL
X_LIST_URL = "https://x.com/i/lists/1814228268662587775" 
# The filename that you will upload to the cloud
OUTPUT_FILENAME = "x_video_playlist.m3u"
# How many seconds to scroll down to collect videos (increase for more videos)
SCROLL_DURATION = 15 
# ---------------------

def extract_video_links():
    video_urls = []
    
    with sync_playwright() as p:
        # Launch a headless browser (runs in the background)
        browser = p.chromium.launch(headless=True)
        # Emulate a standard desktop user agent to avoid instant blocking
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Opening X List: {X_LIST_URL}")
        page.goto(X_LIST_URL)
        
        # Wait for the timeline to load initial tweets
        page.wait_for_timeout(5000)
        
        print("Scrolling and intercepting video network requests...")
        
        # Dictionary to store unique videos we discover
        discovered_videos = {}
        
        # Set up a network listener. X streams video via .m3u8 (HLS) or .mp4 files.
        # We listen to the network traffic while scrolling to catch the true video URLs.
        def handle_response(response):
            url = response.url
            # Target video streams (://twimg.com handles X/Twitter media)
            if "://twimg.com" in url and (".m3u8" in url or ".mp4" in url):
                # Clean up tracking tokens to find the base stream identifier
                base_url = url.split("?")[0]
                if base_url not in discovered_videos:
                    discovered_videos[base_url] = url

        page.on("response", handle_response)

        # Slowly scroll down the page to force lazy-loaded videos to trigger network calls
        start_time = time.time()
        while time.time() - start_time < SCROLL_DURATION:
            page.evaluate("window.scrollBy(0, 800);")
            page.wait_for_timeout(1500)
            
        browser.close()
        video_urls = list(discovered_videos.values())
        
    return video_urls

def generate_m3u(urls):
    if not urls:
        print("No video URLs were found. Ensure the X List is public and has recent video posts.")
        return

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        # Write the required M3U IPTV header
        f.write("#EXTM3U\n")
        
        for i, url in enumerate(urls, start=1):
            # Clean up URL encoding artifacts if present
            clean_url = url.replace("&amp;", "&")
            
            # Format each entry with metadata for the Apple TV app
            f.write(f"#EXTINF:-1 tvg-id=\"X_{i}\" tvg-name=\"X Video {i}\", X Video {i}\n")
            f.write(f"{clean_url}\n")
            
    print(f"Success! Created {OUTPUT_FILENAME} with {len(urls)} videos.")

if __name__ == "__main__":
    detected_links = extract_video_links()
    generate_m3u(detected_links)

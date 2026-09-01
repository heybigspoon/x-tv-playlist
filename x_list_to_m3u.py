import time
import os
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
X_LIST_URL = "https://x.com/i/lists/1814228268662587775" 
OUTPUT_FILENAME = "x_video_playlist.m3u"
SCROLL_DURATION = 20 
# ---------------------

def extract_video_links():
    video_urls = []
    
    auth_token = os.environ.get("X_AUTH_TOKEN")
    ct0 = os.environ.get("X_CT0")

    if not auth_token or not ct0:
        print("CRITICAL ERROR: GitHub Secrets (X_AUTH_TOKEN or X_CT0) are missing!")
        return []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # FIX: Duplicate cookies across all x.com and twitter.com domain variants
        # This prevents X from ignoring the session state on initial redirect
        domains = [".x.com", "x.com", ".twitter.com", "twitter.com"]
        cookie_list = []
        for domain in domains:
            cookie_list.append({"name": "auth_token", "value": auth_token, "domain": domain, "path": "/"})
            cookie_list.append({"name": "ct0", "value": ct0, "domain": domain, "path": "/"})
            
        context.add_cookies(cookie_list)
        page = context.new_page()
        
        print(f"Opening X List securely: {X_LIST_URL}")
        page.goto(X_LIST_URL)
        page.wait_for_timeout(5000)
        
        # FORCE RELOAD: Ensures the browser uses the newly injected cookies if stuck on login wall
        if "Sign in" in page.content() or "Happening now" in page.content():
            print("Authentication wall encountered. Forcing page refresh with active session...")
            page.reload()
            page.wait_for_timeout(7000)
        
        discovered_videos = {}
        
        def handle_response(response):
            url = response.url
            # X stores media files across twimg.com and x.com CDNs
            if ("twimg.com" in url or "x.com" in url) and (".m3u8" in url or ".mp4" in url):
                base_url = url.split("?")[0]
                if base_url not in discovered_videos:
                    discovered_videos[base_url] = url

        page.on("response", handle_response)

        # Scroll down to pull lazy-loaded video network files
        start_time = time.time()
        while time.time() - start_time < SCROLL_DURATION:
            page.evaluate("window.scrollBy(0, 1000);")
            page.wait_for_timeout(1500)
            
        browser.close()
        video_urls = list(discovered_videos.values())
        
    return video_urls

def generate_m3u(urls):
    if not urls:
        print("No videos found. Creating emergency placeholder entry.")
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXTINF:-1, No Videos Found - Check Session Cookies\n")
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


import feedparser
from typing import List, Dict
import datetime
import re
from urllib.parse import urlparse

class FeedParser:
    def __init__(self):
        self.feeds = {}

    def is_valid_url(self, url: str) -> bool:
        """Validate if the provided URL is well-formed"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def parse_feed(self, url: str) -> List[Dict]:
        """Parse RSS feed and return list of entries"""
        if not self.is_valid_url(url):
            raise Exception("Invalid URL format. Please provide a valid RSS feed URL.")

        try:
            feed = feedparser.parse(url)
            
            # Check content type and version
            if hasattr(feed, 'headers'):
                content_type = feed.headers.get('content-type', '').lower()
                if 'xml' not in content_type and 'rss' not in content_type and 'atom' not in content_type:
                    raise Exception(f"Invalid feed type: {content_type}. URL must point to an RSS/XML feed, not a webpage.")

            # Check if feed parsing was successful
            if feed.bozo and feed.bozo_exception:
                if 'SAX' in str(feed.bozo_exception):
                    raise Exception("Invalid RSS feed format. Please ensure the URL points to an RSS feed, not the website's homepage.")
                raise Exception(f"Feed parsing error: {str(feed.bozo_exception)}")

            # Check feed version
            if not hasattr(feed, 'version') or not feed.version:
                raise Exception("Could not detect RSS feed version. Please verify this is a valid RSS feed URL.")

            # Verify feed has entries
            if not hasattr(feed, 'entries') or not feed.entries:
                raise Exception("No entries found in the feed. Please verify this is a valid RSS feed.")

            entries = []
            for entry in feed.entries:
                # Extract content with fallbacks
                content = ''
                if 'content' in entry:
                    content = entry.content[0].value
                elif 'summary' in entry:
                    content = entry.summary
                elif 'description' in entry:
                    content = entry.description

                parsed_entry = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'summary': entry.get('summary', ''),
                    'content': content,
                    'source': feed.feed.get('title', 'Unknown Source')
                }
                entries.append(parsed_entry)

            return entries

        except Exception as e:
            raise Exception(f"Error parsing feed: {str(e)}")

    def add_feed(self, name: str, url: str) -> None:
        """Add feed to managed feeds"""
        if not name or not url:
            raise Exception("Both feed name and URL are required")

        if not self.is_valid_url(url):
            raise Exception("Invalid URL format. Please provide a valid RSS feed URL.")

        self.feeds[name] = url

    def remove_feed(self, name: str) -> None:
        """Remove feed from managed feeds"""
        if name in self.feeds:
            del self.feeds[name]
        else:
            raise Exception(f"Feed '{name}' not found")

    def get_all_feeds(self) -> Dict[str, str]:
        """Get all managed feeds"""
        return self.feeds
import requests
from typing import Dict
import base64
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import json

class WordPressAPI:
    def __init__(self, wp_url: str, username: str, app_password: str):
        """Initialize WordPress API with proper URL formatting and authentication"""
        # Clean and validate WordPress URL
        self.wp_url = wp_url.rstrip('/')
        if not self.wp_url.startswith(('http://', 'https://')):
            raise ValueError("WordPress URL must start with http:// or https://")

        # Format credentials properly
        # WordPress application passwords should be plain text, no need for additional encoding
        self.auth = base64.b64encode(
            f"{username}:{app_password}".encode()
        ).decode('ascii')

        # Set up headers for all requests
        self.headers = {
            'Authorization': f'Basic {self.auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504]
        )
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        self.session.mount("http://", HTTPAdapter(max_retries=retry_strategy))

        # Verify credentials by making a test request
        self._verify_credentials()

    def _verify_credentials(self):
        """Verify WordPress credentials by making a test request"""
        try:
            print(f"Testing WordPress connection to: {self.wp_url}")
            print(f"Request headers: {self.headers}")

            response = self.session.get(
                f"{self.wp_url}/wp-json/wp/v2/users/me",
                headers=self.headers,
                timeout=10
            )

            if response.status_code != 200:
                print(f"WordPress API response: {response.status_code}")
                print(f"Response headers: {response.headers}")
                try:
                    print(f"Response body: {response.json()}")
                except:
                    print(f"Response text: {response.text}")

            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "Invalid WordPress credentials. Please verify your username and application password. "
                    "Make sure you're using an application password generated from WordPress Dashboard → Users → Security → Application Passwords"
                )
            raise Exception(f"Error connecting to WordPress: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {str(e)}")

    def upload_media(self, image_url: str) -> Dict:
        """Upload media to WordPress with retries"""
        try:
            # Validate image URL
            if not image_url:
                raise ValueError("Image URL is required")

            # Download image from URL with retries
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    image_response = self.session.get(image_url, timeout=30)
                    image_response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise Exception(f"Failed to download image after {max_retries} attempts: {str(e)}")
                    time.sleep(retry_count)  # Exponential backoff

            # Upload to WordPress
            upload_endpoint = f"{self.wp_url}/wp-json/wp/v2/media"

            # Special headers for media upload
            headers = {
                'Authorization': f'Basic {self.auth}',
                'Content-Disposition': 'attachment; filename=image.jpg',
                'Content-Type': 'image/jpeg',
            }

            files = {
                'file': ('image.jpg', image_response.content, 'image/jpeg'),
            }

            # Upload with retries
            retry_count = 0
            while retry_count < max_retries:
                try:
                    print(f"Uploading media to: {upload_endpoint}")
                    print(f"Upload headers: {headers}")

                    response = self.session.post(
                        upload_endpoint,
                        headers=headers,
                        files=files,
                        timeout=60  # Longer timeout for uploads
                    )

                    if response.status_code != 201:
                        print(f"Media upload response: {response.status_code}")
                        print(f"Response headers: {response.headers}")
                        try:
                            print(f"Response body: {response.json()}")
                        except:
                            print(f"Response text: {response.text}")

                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        print(f"Authentication failed. Response: {e.response.text}")
                        raise Exception(
                            "WordPress authentication failed. Please verify your credentials. "
                            "Error details: " + str(e.response.text)
                        )
                    elif e.response.status_code == 500:
                        error_msg = str(e.response.text)
                        if "file type" in error_msg.lower():
                            raise Exception(
                                "WordPress rejected the image upload. This might be due to: \n"
                                "1. File type restrictions on your WordPress site\n"
                                "2. Insufficient permissions for media uploads\n"
                                "3. File size limitations\n"
                                "Please check your WordPress media settings and user permissions."
                            )
                    retry_count += 1
                    if retry_count == max_retries:
                        raise Exception(f"Failed to upload media after {max_retries} attempts: {str(e)}")
                    time.sleep(retry_count)
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise Exception(f"Failed to upload media after {max_retries} attempts: {str(e)}")
                    time.sleep(retry_count)

        except ValueError as e:
            raise Exception(f"Invalid input: {str(e)}")
        except Exception as e:
            raise Exception(f"Error uploading media: {str(e)}")

    def create_post(self, content: Dict, status: str = 'draft') -> Dict:
        """Create a new WordPress post with SEO metadata"""
        try:
            endpoint = f"{self.wp_url}/wp-json/wp/v2/posts"

            post_data = {
                'title': content['title'],
                'content': content['content'],
                'status': status,
                'slug': content.get('slug', ''),
                'meta': {
                    '_yoast_wpseo_metadesc': content.get('meta_description', ''),
                    '_yoast_wpseo_focuskw': content.get('keywords', '').split(',')[0],
                    '_yoast_wpseo_meta-robots-noindex': '0',
                    '_yoast_wpseo_meta-robots-nofollow': '0'
                }
            }

            response = self.session.post(
                endpoint,
                headers=self.headers,
                json=post_data,
                timeout=30
            )

            if response.status_code != 201:
                print(f"Post creation response: {response.status_code}")
                print(f"Response headers: {response.headers}")
                try:
                    print(f"Response body: {response.json()}")
                except:
                    print(f"Response text: {response.text}")

            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("WordPress authentication failed. Please verify your credentials.")
            raise Exception(f"Error creating WordPress post: {str(e)}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out while creating post. Please try again.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error creating WordPress post: {str(e)}")
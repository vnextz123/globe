import streamlit as st
import json
import datetime
from utils.feed_parser import FeedParser
import os
import signal
import sys

# Set environment variables for Streamlit configuration
os.environ['STREAMLIT_SERVER_PORT'] = '8501'
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

import streamlit as st

# Set Streamlit configuration
st.set_page_config(
    page_title="AI Content Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import after configuration
from utils.content_generator import ContentGenerator
from utils.wordpress_api import WordPressAPI
from utils.seo_optimizer import SEOOptimizer
from utils.trend_analyzer import TrendAnalyzer

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'feed_parser' not in st.session_state:
    st.session_state.feed_parser = FeedParser()
if 'content_generator' not in st.session_state:
    st.session_state.content_generator = ContentGenerator()
if 'seo_optimizer' not in st.session_state:
    st.session_state.seo_optimizer = SEOOptimizer()
if 'trend_analyzer' not in st.session_state:
    st.session_state.trend_analyzer = TrendAnalyzer()
if 'wordpress_api' not in st.session_state:
    st.session_state.wordpress_api = None
if 'feed_cache' not in st.session_state:
    st.session_state.feed_cache = {}
if 'content_cache' not in st.session_state:
    st.session_state.content_cache = {}
if 'site_config' not in st.session_state:
    st.session_state.site_config = {}
if 'generated_articles' not in st.session_state:
    st.session_state.generated_articles = []

# Streamlit handles process management internally

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Site Management", "Bulk Article Generator"])
st.session_state.page = page.lower()

if st.session_state.page == "home":
    st.title("AI Content Generator")
    st.markdown("""
    Welcome to the AI Content Generator! This tool helps you:
    1. Generate SEO-optimized content from RSS feeds
    2. Analyze Google Trends
    3. Manage multiple WordPress sites
    4. Create bulk articles efficiently

    Get started by navigating to:
    - **Site Management** to configure your WordPress sites
    - **Bulk Article Generator** to create content
    """)

elif st.session_state.page == "site management":
    st.title("Site Management")

    # Display existing sites
    if st.session_state.site_config:
        st.header("Configured Sites")
        cols = st.columns(3)
        for i, (site_name, config) in enumerate(st.session_state.site_config.items()):
            with cols[i % 3]:
                if st.button(f"📝 {site_name}"):
                    st.session_state.selected_site = site_name

    # Display selected site details
    if 'selected_site' in st.session_state and st.session_state.selected_site:
        site = st.session_state.site_config[st.session_state.selected_site]
        st.subheader(f"Configuration: {st.session_state.selected_site}")

        with st.form("edit_site"):
            wp_url = st.text_input("WordPress URL", value=site.get('wp_url', ''))
            wp_username = st.text_input("Username", value=site.get('wp_username', ''))
            wp_password = st.text_input("Application Password", type="password")
            feed_urls = st.text_area("RSS Feed URLs (one per line)", 
                                   value='\n'.join(site.get('feed_urls', [])))

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Update"):
                    st.session_state.site_config[st.session_state.selected_site].update({
                        'wp_url': wp_url,
                        'wp_username': wp_username,
                        'wp_password': wp_password if wp_password else site.get('wp_password', ''),
                        'feed_urls': [url.strip() for url in feed_urls.split('\n') if url.strip()]
                    })
                    st.success("Site updated successfully!")

            with col2:
                if st.form_submit_button("Delete"):
                    del st.session_state.site_config[st.session_state.selected_site]
                    del st.session_state.selected_site
                    st.success("Site deleted successfully!")
                    st.rerun()

    # Add new site form
    st.header("Add New Site")
    site_name = st.text_input("Site Name")
    if site_name:
        if site_name not in st.session_state.site_config:
            st.session_state.site_config[site_name] = {}
            st.success(f"Site {site_name} added! Configure it above.")
            st.rerun()

elif st.session_state.page == "bulk article generator":
    st.title("Bulk Article Generator")

    # Site Selection
    if not st.session_state.site_config:
        st.warning("Please configure at least one site in Site Management first.")
    else:
        selected_site = st.selectbox("Select Site", list(st.session_state.site_config.keys()))
        config = st.session_state.site_config[selected_site]

        # Content Source Selection
        source_type = st.radio("Content Source", ["RSS Feeds", "Google Trends", "Custom Topics"])

        if source_type == "RSS Feeds":
            feed_source = st.radio("Feed Source", ["Saved Feeds", "Custom Feed"])
            if feed_source == "Saved Feeds":
                selected_feeds = st.multiselect("Select Feeds", config.get('feed_urls', []))
            else:
                custom_feed = st.text_input("Enter RSS Feed URL")
                selected_feeds = [custom_feed] if custom_feed else []

        elif source_type == "Google Trends":
            category = st.selectbox("Category", st.session_state.trend_analyzer.get_categories())
            trend_keywords = st.session_state.trend_analyzer.get_trending_topics(category)
            selected_topics = st.multiselect("Select Trending Topics", trend_keywords)

        else:  # Custom Topics
            custom_topics = st.text_area("Enter Topics (one per line)")
            selected_topics = [topic.strip() for topic in custom_topics.split('\n') if topic.strip()]

        # Language Selection
        target_language = st.selectbox("Target Language", ["English", "Hindi", "Spanish"])

        # Generation Settings
        with st.expander("Advanced Settings"):
            articles_per_topic = st.number_input("Articles per Topic", min_value=1, value=1)
            min_words = st.number_input("Minimum Words", min_value=300, value=600)
            include_images = st.checkbox("Include AI-generated Images", value=True)

        # Date selection
        today = datetime.date.today()
        start_date = st.date_input("Start Date", today - datetime.timedelta(days=7))
        end_date = st.date_input("End Date", today)

        if 'fetched_articles' not in st.session_state:
            st.session_state.fetched_articles = []

        # Article fetch count control
        num_articles = st.number_input("Number of articles to fetch", min_value=1, max_value=50, value=2)

        if st.button("Fetch Articles"):
            with st.spinner("Fetching articles..."):
                try:
                    # Clear previous fetched articles
                    st.session_state.fetched_articles = []
                    
                    # Fetch articles from selected feeds
                    if source_type == "RSS Feeds":
                        fetched = []
                        for feed_url in selected_feeds:
                            entries = st.session_state.feed_parser.parse_feed(feed_url)
                            fetched.extend(entries)
                            
                        # Only keep the requested number of articles
                        st.session_state.fetched_articles = fetched[:num_articles]
                        st.success(f"Fetched {len(st.session_state.fetched_articles)} articles successfully!")
                except Exception as e:
                    st.error(f"Error fetching articles: {str(e)}")

        # Display fetched articles for selection
        if st.session_state.fetched_articles:
            st.subheader("Select Articles to Rewrite")
            selected_articles = []

            # Remove duplicates based on title
            seen_titles = set()
            unique_articles = []
            for article in st.session_state.fetched_articles[:num_articles]:
                if article['title'] not in seen_titles:
                    seen_titles.add(article['title'])
                    unique_articles.append(article)

            for idx, article in enumerate(unique_articles):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    if st.checkbox("", key=f"select_{idx}"):
                        selected_articles.append(article)
                with col2:
                    with st.expander(f"{idx + 1}. {article['title']}"):
                        st.write(f"Source: {article.get('source', 'Unknown')}")
                        st.write(f"Published: {article.get('published', 'Unknown date')}")
                        if 'content' in article:
                            word_count = len(article['content'].split())
                            st.write(f"Word Count: {word_count}")

                        # Check SEO optimization
                        is_seo_optimized = (
                            article['word_count'] >= 600 and
                            'keywords' in article and
                            'meta_description' in article
                        )
                        st.write(f"SEO Optimized: {'✅' if is_seo_optimized else '❌'}")

                        st.text_area("Content", article['content'], height=200)

                        # Add WordPress publish button
                        if st.button("Publish to WordPress", key=f"publish_{article['id']}_{article['title'][:20]}"):
                            if 'wordpress_api' in st.session_state and st.session_state.wordpress_api:
                                try:
                                    response = st.session_state.wordpress_api.create_post(article)
                                    st.success(f"Published to WordPress! Post ID: {response['id']}")
                                except Exception as e:
                                    st.error(f"Failed to publish: {str(e)}")
                            else:
                                st.warning("Please configure WordPress site in Site Management first")

            if selected_articles and st.button("Rewrite Selected Articles"):
                with st.spinner("Generating optimized articles..."):
                    try:
                        new_articles = []
                        for article in selected_articles:
                            # Generate optimized content using ContentGenerator
                            generated = st.session_state.content_generator.generate_content({
                                'title': article['title'],
                                'content': article['content']
                            })

                            if isinstance(generated, str):
                                generated = json.loads(generated)

                            new_article = {
                                'id': len(st.session_state.generated_articles) + 1,
                                'title': generated['title'],
                                'content': generated['content'],
                                'status': 'draft',
                                'meta_description': generated['meta_description'],
                                'keywords': generated['keywords'],
                                'slug': generated['slug'],
                                'word_count': len(generated['content'].split()),
                                'date': datetime.date.today()
                            }
                            new_articles.append(new_article)

                        st.session_state.generated_articles.extend(new_articles)
                        st.success(f"Generated {len(new_articles)} optimized articles successfully!")
                    except Exception as e:
                        st.error(f"Error generating articles: {str(e)}")

        # Display Generated Articles
        if st.session_state.generated_articles:
            st.header("Generated Articles")

            # Filter articles by date
            filtered_articles = [
                article for article in st.session_state.generated_articles 
                if start_date <= article['date'] <= end_date
            ]

            if not filtered_articles:
                st.info("No articles found for the selected date range.")
            else:
                for article in filtered_articles:
                    with st.expander(f"{article['title']} - {article['date']}"):
                        st.write(f"Status: {article['status']}")
                        st.write(f"Word Count: {article['word_count']}")
                        st.write(f"Date: {article['date']}")
                        st.text_area("Content", article['content'], height=200)

                        if st.button("Delete", key=f"delete_{article['id']}_{article['title'][:20]}"):
                            st.session_state.generated_articles.remove(article)
                            st.rerun()
import os
from openai import OpenAI
from typing import Dict, List, Optional

class ContentGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        self.model = "gpt-4o"

    def _format_content(self, content: str) -> str:
        """Format content with proper HTML and anchors"""
        # Convert markdown headings to HTML with anchors
        def heading_replace(match):
            level = len(match.group(1))
            text = match.group(2)
            # Create anchor ID from text (transliterated if Hindi)
            import re
            anchor_id = re.sub(r'[^\w\s-]', '', text.lower())
            anchor_id = re.sub(r'\s+', '-', anchor_id.strip())
            return f'<h{level} id="{anchor_id}">{text}</h{level}>'
            
        content = re.sub(r'^(#{1,6})\s*(.+)$', heading_replace, content, flags=re.MULTILINE)
        
        # Convert markdown links to HTML
        content = re.sub(
            r'\[([^\]]+)\]\(([^\)]+)\)',
            r'<a href="\2" target="_blank" rel="noopener">\1</a>',
            content
        )
        
        return content

    def generate_hindi_content(self, source_content: Dict, keywords: List[str] = None) -> Dict:
        """Generate Hindi content from source material"""
        try:
            # Auto-generate focus keyword if none provided
            if not keywords:
                analysis_prompt = f"Analyze this content and suggest the most relevant Hindi keywords:\n{source_content['content']}"
                keyword_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": analysis_prompt}]
                )
                keywords = [keyword_response.choices[0].message.content.strip()]

            prompt = f"""
            Create a unique Hindi blog post based on this content:
            Title: {source_content['title']}
            Source Content: {source_content['content']}
            Focus Keyword: {keywords[0]}
            
            Requirements:
            1. Write entirely in Hindi using Devanagari script (use English only for technical terms)
            2. Title must be in proper Devanagari script
            3. Minimum 300 words
            4. SEO optimized with proper keyword density
            5. Use proper HTML formatting:
               - Convert all headings to proper HTML tags (<h1>, <h2>, etc.)
               - Create anchor IDs for table of contents using English transliteration
               - Format external links as proper HTML <a> tags with target="_blank" and rel="noopener"
            6. Generate SEO meta tags in Hindi
            
            Format the response as a JSON with:
            {{
                "title": "Hindi SEO title with keywords",
                "content": "Well-structured Hindi blog post",
                "meta_description": "Hindi meta description with keywords",
                "meta_keywords": "Hindi keywords",
                "slug": "english-url-friendly-slug",
                "estimated_keyword_density": "percentage"
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            generated = json.loads(response.choices[0].message.content)
            generated['content'] = self._format_content(generated['content'])
            return json.dumps(generated)

        except Exception as e:
            raise Exception(f"Error generating Hindi content: {str(e)}")

    def generate_content(self, source_content: Dict, keywords: List[str] = None, article_type: str = "news", language: str = "English", include_toc: bool = False) -> Dict:
        """Generate unique content from source material"""
        try:
            # Auto-generate focus keyword if none provided
            if not keywords:
                analysis_prompt = f"Analyze this content and suggest the most relevant focus keyword:\n{source_content['content']}"
                keyword_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": analysis_prompt}]
                )
                keywords = [keyword_response.choices[0].message.content.strip()]

            prompt = f"""
            Create an SEO-optimized {article_type} article in {language} based on this content. {f'Include a table of contents.' if include_toc else 'Do not include a table of contents.'} For news articles, focus on factual reporting and avoid unnecessary formatting:
            Title: {source_content['title']}
            Source Content: {source_content['content']}
            Focus Keyword: {keywords[0] if keywords else ''}
            Article Type: {article_type}  # news, review, or blog
            Include TOC: {include_toc}    # true/false
            
            Requirements:
            1. Title must:
               - Match the article type (news: factual; review: evaluative; blog: engaging)
               - Preserve the original meaning and context
               - Be 50-60 characters long
               - For news articles: keep close to original title
               
            2. Meta Description must:
               - Be in Hindi
               - Include focus keyword near beginning  
               - Be 150-160 characters long
               - Be compelling and encourage clicks
               
            3. URL slug must:
               - Use English transliteration 
               - Include focus keyword
               - Use hyphens between words
               - Be concise (3-5 words maximum)
               
            4. Content must:
               - Be minimum 600 words in Hindi
               - Include focus keyword in first paragraph
               - Have proper keyword density (1-3%)
               - Use proper heading hierarchy (H1, H2, H3)
            
            Follow these SEO requirements strictly:
            1. Title must:
               - Include focus keyword near the beginning
               - Contain a number (e.g., "5 Ways...", "7 Tips...")
               - Include a power word (e.g., amazing, exclusive, proven)
               - Include a sentiment word (e.g., best, great)
               
            2. Content must:
               - Be minimum 600 words
               - Include focus keyword in first paragraph
               - Have 1% keyword density
               - Include focus keyword in H2/H3 subheadings
               - Use short paragraphs
               - Include table of contents if requested
               - Include both internal and external dofollow links
               - Include images with focus keyword in alt text
               
            3. Meta description must include focus keyword
            4. URL slug must include focus keyword and be concise
            
            Please format the response as a JSON object with the following structure:
            {{
                "title": "SEO optimized title meeting all requirements",
                "content": "Well-structured blog post with table of contents, headings, links, and images",
                "meta_description": "SEO-optimized meta description with focus keyword",
                "keywords": "focus-keyword, related-keywords",
                "slug": "seo-friendly-url-with-keyword",
                "estimated_keyword_density": "percentage"
            }}

            Ensure the content is:
            1. Minimum 600 words
            2. Has focus keyword in title, meta description, and content
            3. Includes proper heading structure (H2, H3)
            4. Contains both internal and external links
            5. Has image placeholders with keyword-optimized alt text
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Error generating content: {str(e)}")

    def generate_image_prompt(self, content: Dict) -> str:
        """Generate image prompt based on content"""
        try:
            prompt = f"""
            Based on this blog post title and content, create a detailed image prompt for DALL-E:
            Title: {content['title']}
            Content summary: {content['content'][:200]}

            Generate a creative and specific image description that would work well as a blog header image.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Error generating image prompt: {str(e)}")

    def generate_image(self, prompt: str) -> Optional[str]:
        """Generate image using DALL-E"""
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                n=1
            )

            return response.data[0].url

        except Exception as e:
            raise Exception(f"Error generating image: {str(e)}")
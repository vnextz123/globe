
from typing import Dict, List
import re
from textblob import TextBlob

class SEOOptimizer:
    def __init__(self):
        self.min_word_count = 600
        self.max_word_count = 2500
        self.min_keyword_density = 0.01
        self.max_keyword_density = 0.03
        self.power_words = set(['amazing', 'exclusive', 'free', 'instant', 'new', 'proven', 'guaranteed', 'powerful'])
        self.sentiment_words = set(['best', 'great', 'awesome', 'terrible', 'worst', 'amazing', 'awful', 'excellent'])

    def analyze_content(self, content: Dict, keywords: List[str] = None) -> Dict:
        """Analyze content for SEO metrics"""
        text = content['content']
        title = content.get('title', '')
        meta_description = content.get('meta_description', '')
        
        # Auto-generate focus keyword if none provided
        if not keywords:
            blob = TextBlob(text)
            keywords = [phrase.string for phrase in blob.noun_phrases[:1]]
        
        word_count = len(text.split())
        metrics = {
            'focus_keyword': keywords[0] if keywords else '',
            'word_count': word_count,
            'keyword_density': {},
            'readability_score': self._calculate_readability(text),
            'suggestions': [],
            'title_analysis': {},
            'content_analysis': {},
            'technical_analysis': {}
        }

        # Title analysis
        title_words = title.lower().split()
        metrics['title_analysis'].update({
            'has_keyword': any(kw.lower() in title.lower() for kw in keywords),
            'keyword_at_beginning': any(kw.lower() in ' '.join(title_words[:3]).lower() for kw in keywords),
            'has_number': any(word.isdigit() for word in title_words),
            'has_power_word': any(word.lower() in self.power_words for word in title_words),
            'has_sentiment': any(word.lower() in self.sentiment_words for word in title_words)
        })

        # Content analysis
        metrics['content_analysis'].update({
            'has_keyword_beginning': any(kw.lower() in ' '.join(text.split()[:50]).lower() for kw in keywords),
            'has_subheadings': bool(re.findall(r'<h[2-4]>', text)),
            'has_keyword_in_subheading': bool(re.findall(r'<h[2-4]>.*?' + re.escape(keywords[0] if keywords else '') + r'.*?</h[2-4]>', text, re.I)),
            'has_images': bool(re.findall(r'<img.*?>', text)),
            'has_keyword_in_alt': bool(re.findall(r'<img.*?alt=".*?' + re.escape(keywords[0] if keywords else '') + r'.*?".*?>', text, re.I)),
            'has_external_links': bool(re.findall(r'<a.*?href="https?://.*?".*?>', text)),
            'has_internal_links': bool(re.findall(r'<a.*?href="/".*?>', text)),
            'paragraph_length': self._analyze_paragraphs(text)
        })

        # Calculate keyword density
        for keyword in keywords:
            count = len(re.findall(rf'\b{re.escape(keyword)}\b', text.lower()))
            density = count / word_count if word_count > 0 else 0
            metrics['keyword_density'][keyword] = density

        # Generate suggestions based on analysis
        self._generate_suggestions(metrics)

        return metrics

    def _analyze_paragraphs(self, text: str) -> Dict:
        paragraphs = re.split(r'\n\s*\n', text)
        return {
            'avg_length': sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            'total_paragraphs': len(paragraphs)
        }

    def _generate_suggestions(self, metrics: Dict):
        """Generate SEO improvement suggestions"""
        if metrics['word_count'] < self.min_word_count:
            metrics['suggestions'].append(f"Increase content length to at least {self.min_word_count} words")
        
        if not metrics['title_analysis']['has_keyword']:
            metrics['suggestions'].append("Add focus keyword to SEO title")
        
        if not metrics['title_analysis']['keyword_at_beginning']:
            metrics['suggestions'].append("Move focus keyword closer to the beginning of the title")
            
        if not metrics['content_analysis']['has_keyword_in_subheading']:
            metrics['suggestions'].append("Add focus keyword to at least one subheading")
            
        if not metrics['content_analysis']['has_images']:
            metrics['suggestions'].append("Add at least one image to the content")
            
        if not metrics['content_analysis']['has_external_links']:
            metrics['suggestions'].append("Add external links to authoritative sources")
            
        if not metrics['content_analysis']['has_internal_links']:
            metrics['suggestions'].append("Add internal links to related content")

    def _calculate_readability(self, text: str) -> float:
        """Calculate basic readability score"""
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        syllables = self._count_syllables(text)
        
        if sentences == 0 or words == 0:
            return 0
        
        # Flesch Reading Ease score
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        return max(0, min(100, score))

    def _count_syllables(self, text: str) -> int:
        """Rough syllable count"""
        text = text.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False
        
        for char in text:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel
            
        return count

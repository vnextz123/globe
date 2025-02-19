
from pytrends.request import TrendReq
import pandas as pd
from typing import List

class TrendAnalyzer:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.categories = {
            "All": "",
            "Business": "/Business",
            "Technology": "/Technology",
            "Entertainment": "/Entertainment",
            "Sports": "/Sports",
            "Health": "/Health",
        }
        
    def get_categories(self) -> List[str]:
        return list(self.categories.keys())
        
    def get_trending_topics(self, category: str) -> List[str]:
        try:
            trending_searches_df = self.pytrends.trending_searches(
                pn='united_states' if category == "All" else f'united_states{self.categories[category]}'
            )
            return trending_searches_df[0].tolist()
        except Exception as e:
            print(f"Error fetching trends: {str(e)}")
            return []
            
    def get_related_topics(self, keyword: str) -> List[str]:
        try:
            self.pytrends.build_payload([keyword], timeframe='today 1-m')
            related_topics = self.pytrends.related_topics()
            if keyword in related_topics:
                rising = related_topics[keyword]['rising']
                return rising['topic_title'].tolist()[:10]
            return []
        except Exception as e:
            print(f"Error fetching related topics: {str(e)}")
            return []

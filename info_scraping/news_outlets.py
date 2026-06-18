from newspaper.google_news import GoogleNewsSource
from pathlib import Path
import os
from datetime import date


today = date.today().strftime("%Y%m%d")


# important paths 
cwd = Path(".")
news_dir = cwd.parent / "news"

def getNews(topic:str):
    # gets google news from last 1 day on your topic 
    # exports it into a .txt file in news 
    source = GoogleNewsSource(
        period="1d",
        max_results=5,
    )

    source.build(
        top_news=False,
        keyword=topic,
        )
    
    articles = ""
    for index, article in enumerate(source.articles):
        articles += f"Title: {article.title} \n"
        articles += f"URL:   {article.url} \n" 
        
        try:
            article.download()
            article.parse()
            articles += f"text: {article.text} \n \n \n" 
        except Exception as e:
            print(f"Could not download full text: {e}")
    
    Path(news_dir / f"TodaysNews.txt").write_text(articles)
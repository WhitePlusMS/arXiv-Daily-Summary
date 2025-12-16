from moviepy import VideoFileClip
import inspect

try:
    video = VideoFileClip(r"E:\ARXIV_daily_article_summary\docs\arxiv daily.mp4")
    print("Methods of video object:")
    print([m for m in dir(video) if not m.startswith('_')])
    video.close()
except Exception as e:
    print(e)

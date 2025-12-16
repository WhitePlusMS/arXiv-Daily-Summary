from moviepy import VideoFileClip, concatenate_videoclips
import os

def cut_video():
    # 文件路径
    input_path = r"E:\ARXIV_daily_article_summary\docs\arxiv daily.mp4"
    output_path = r"E:\ARXIV_daily_article_summary\docs\arxiv_daily_edited.mp4"

    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        return

    print("Loading video...")
    try:
        # 加载视频
        video = VideoFileClip(input_path)

        # 定义要切除的时间段
        # 截掉 2:15 - 2:19
        # 即保留 0:00 - 2:15 和 2:19 - end
        
        t1_end = "00:02:15"
        t2_start = "00:02:19"

        print(f"Cutting video: removing segment between {t1_end} and {t2_start}...")

        # 第一段：开始到 2:15
        clip1 = video.subclipped(0, t1_end)

        # 第二段：2:19 到 结束
        clip2 = video.subclipped(t2_start, video.duration)

        # 拼接
        final_clip = concatenate_videoclips([clip1, clip2])

        # 保存
        print(f"Writing output to {output_path}...")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # 关闭资源
        video.close()
        final_clip.close()
        print("Done!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    cut_video()

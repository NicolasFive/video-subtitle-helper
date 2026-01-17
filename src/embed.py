import ffmpeg
from utils import download_file, create_tempdir
import os
from subtitle import create_ssa_subtitles
from utils import modify_separator


class SubtitleEmbed:
    def __init__(self):
        pass

    def embed(self, video_path, subtitle_data):
        # 创建临时目录并生成字幕文件
        temp_dir = create_tempdir()
        subtitle_path = os.path.join(temp_dir, "styled_subtitles.ssa")
        output_path = os.path.join(temp_dir, "output.mp4")
        # 如果是URL则下载
        if video_path.startswith("http"):
            video_path = download_file(video_path, temp_dir)

        video_width, video_height = self.get_video_dimensions(video_path)
        

        # 转换字幕数据
        subtitle_path = create_ssa_subtitles(subtitle_data, subtitle_path, video_width, video_height)

        # 嵌入字幕
        subtitle_path = modify_separator(subtitle_path)


        print("开始处理...")

        ffmpeg.input(video_path).output(
            output_path,
            vf=f"ass={subtitle_path},scale={video_width}:{video_height}",  # 使用ass滤镜添加字幕
            vcodec="libx264",  # 重新编码视频以嵌入字幕
            acodec="aac",
        ).run(overwrite_output=True)

        print(f"完成！输出文件: {output_path}")
        return output_path
    
    def get_video_dimensions(self, video_path):
        # 使用ffprobe获取视频信息
        probe = ffmpeg.probe(video_path)
        # 查找视频流
        video_stream = None
        for stream in probe['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        if not video_stream:
            raise ValueError("未找到视频流")
        
        # 获取宽度和高度
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        return width, height
        


if __name__ == "__main__":
    # video_path = (
    #     r"./videos/immortality-killed-the-witch-animation-dnd-720-publer.io.mp4"
    # )
    # subtitle_path = r"./styled_subtitles.ssa"
    video_path = r"https://coze-project.cn-nb1.rains3.com/immortality-killed-the-witch-animation-dnd-720-publer.io.mp4"
    subtitle_path = r"https://coze-project.cn-nb1.rains3.com/styled_subtitles.ssa"
    output_path = r"./output.mp4"

    embeder = SubtitleEmbed()
    embeder.embed(video_path, subtitle_path, output_path)

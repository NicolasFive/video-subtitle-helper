from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import traceback
import json
from trans import Transcriber
from utils import create_tempdir, modify_separator, split_sentence_by_dot, download_file
import os
from embed import SubtitleEmbed
from s3 import S3Operator

app = FastAPI(title="音频转录与字幕嵌入API")


# 数据模型定义
class TranscribeRequest(BaseModel):
    video_path: str


class SubtitleData(BaseModel):
    text: str
    start: int
    end: int
    font_color: Optional[str] = "#FF0000"
    font_size: Optional[int] = 10


class EmbedSubtitleRequest(BaseModel):
    subtitle_data: List[SubtitleData]
    video_path: str


@app.post("/transcribe")
async def transcribe_api(request: TranscribeRequest):
    """
    音频转录API
    参数:
        video_path: 音频文件路径或URL
    """
    try:
        # 这里应该从环境变量或配置中获取API密钥
        api_key = "442e2d408ee948a8bd078066a493ac05"  # 建议改为环境变量
        trans = Transcriber(api_key)
        transcript = trans.exec(request.video_path)

        # 确保返回的是可序列化的数据
        result = transcript.json_response
        utterances = result.get("utterances", [])
        utterances = [s for u in utterances for s in split_sentence_by_dot(u)]
        result["utterances"] = utterances

        return {"status": "success", "data": result}
    except Exception as e:
        # 返回详细的错误信息
        error_info = {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        }
        raise HTTPException(status_code=500, detail=error_info)


@app.post("/embed_subtitle")
async def embed_subtitle_api(request: EmbedSubtitleRequest):
    """
    字幕嵌入API
    参数:
        subtitle_data: 字幕数据列表
        video_path: 视频文件路径或URL
    """
    try:
        # 将Pydantic模型转换为字典列表
        subtitle_data = []
        for item in request.subtitle_data:
            item_dict = item.model_dump(by_alias=True)  # 使用别名转换
            subtitle_data.append(item_dict)

        embeder = SubtitleEmbed()
        output_path = embeder.embed(request.video_path, subtitle_data)

        # 上传输出视频到对象存储
        s3_oper = S3Operator(
            endpoint="https://cn-nb1.rains3.com",
            access_key="6PZZwXqeL1dCdtqh",
            secret_key="uun5qw9oSmwkc1OhLfcBV2f3DhNseD",
            bucket="coze-project",
        )
        object_key = modify_separator(output_path[2:])
        output_link = s3_oper.upload(object_key, output_path)

        return {"status": "success", "message": "字幕嵌入完成", "output": output_link}
    except Exception as e:
        # 返回详细的错误信息
        error_info = {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        }
        raise HTTPException(status_code=500, detail=error_info)


if __name__ == "__main__":
    import uvicorn
    import argparse

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="音频转录与字幕嵌入API")
    parser.add_argument(
        "-p", "--port", type=int, default=8000, help="服务器端口号 (默认: 8000)"
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0)",
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 启动服务器
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

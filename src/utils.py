import os
import requests
import uuid
from datetime import datetime
import re


def modify_separator(path, new_sep="/"):
    if os.sep != new_sep:
        return path.replace(os.sep, new_sep)
    return path


def create_tempdir():
    # 生成带时间戳的文件夹名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uuid_short = uuid.uuid4().hex[:8]
    temp_dir_name = f"{timestamp}_{uuid_short}"

    # 在当前目录下创建临时文件夹
    temp_dir = os.path.join(".", "temp", temp_dir_name)

    # 创建临时文件夹
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def download_file(url, temp_dir=None):
    if temp_dir is None:
        temp_dir = create_tempdir()

    local_path = os.path.join(temp_dir, os.path.basename(url.split("?")[0]))

    print(f"正在下载: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    local_path = modify_separator(local_path)
    print(f"下载完成: {local_path}")
    return local_path



def split_sentence_by_dot(json_response):
    text = json_response.get("text", "")
    speaker = json_response.get("speaker", "")
    words = json_response.get("words", [])
    confidence = json_response.get("confidence", 0)
    # 分割并保留分隔符
    parts = re.split(r"([.!?。！？])", text)

    # 组合句子
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        if parts[i].strip():  # 非空句子
            sentences.append(parts[i] + parts[i + 1])

    # 处理最后一个部分（如果有）
    if parts[-1].strip():
        sentences.append(parts[-1])
    sentences = [
        {"text": s.strip(), "words": re.split(r"\s+", s.strip())} for s in sentences
    ]
    global_words_idx = 0
    global_start = 0
    global_end = 0
    handled_sentences = []
    for s in sentences:
        txt = s.get("text", "")
        wds = s.get("words", [])
        handled_wds=[]
        for idx, w in enumerate(wds):
            global_word = words[global_words_idx]
            global_word_text = global_word.get("text", "")
            if w != global_word_text:
                break
            global_words_idx+=1
            handled_wds.append(global_word)
            if idx == 0:
                global_start = global_word.get("start", 0)
            global_end = global_word.get("end", 0)
        handled_sentences.append(
            {
                "speaker": speaker,
                "text": txt,
                "confidence": confidence,
                "start": global_start,
                "end": global_end,
                "words": handled_wds
            }
        )
    return handled_sentences

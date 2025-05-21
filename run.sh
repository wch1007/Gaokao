#!/bin/bash

# 设置运行环境
echo "设置运行环境..."
pip install --upgrade yt-dlp
pip install requests
mkdir -p videos subtitles text_data

# 定义目标UP主
UP_LIST=(
    "张雪峰老师官方号"
    "取景框看世界"
)

# 运行下载和处理
echo "开始处理任务..."

for uploader in "${UP_LIST[@]}"; do
    echo "====================================="
    echo "处理UP主: $uploader"
    echo "====================================="
    
    # 下载视频和字幕
    echo "下载视频和字幕..."
    python bilibili_downloader.py --uploader "$uploader" --max 5
    
    # 处理字幕提取文本
    echo "提取字幕文本..."
    python subtitle_extractor.py --metadata
    
    echo "UP主 $uploader 处理完成"
    echo ""
done

echo "====================================="
echo "所有任务处理完毕!"
echo "=====================================" 
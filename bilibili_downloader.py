#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import json
import argparse
from datetime import datetime

def setup_environment():
    """检查并安装必要的依赖"""
    try:
        # 检查yt-dlp是否已安装
        subprocess.run(['yt-dlp', '--version'], check=True, stdout=subprocess.PIPE)
        print("yt-dlp已安装")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("正在安装yt-dlp...")
        subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], check=True)
        print("yt-dlp安装完成")
    
    # 创建输出目录
    os.makedirs('videos', exist_ok=True)
    os.makedirs('subtitles', exist_ok=True)
    os.makedirs('metadata', exist_ok=True)

def get_uploader_videos(uploader_name):
    """获取UP主的视频列表"""
    print(f"正在获取UP主 '{uploader_name}' 的视频列表...")
    
    # 使用yt-dlp搜索UP主视频
    search_cmd = [
        'yt-dlp', 
        f'bilisearch{uploader_name}', 
        '--flat-playlist',
        '--print', 'id,title',
        '--no-download'
    ]
    
    try:
        result = subprocess.run(search_cmd, check=True, stdout=subprocess.PIPE, text=True)
        videos = []
        
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_id, title = line.split(maxsplit=1)
                    videos.append({'id': video_id, 'title': title})
                except ValueError:
                    continue
                    
        print(f"找到 {len(videos)} 个视频")
        return videos
    except subprocess.SubprocessError as e:
        print(f"搜索视频失败: {e}")
        return []

def download_video(video_id, include_subtitles=True):
    """下载单个视频及其字幕"""
    print(f"正在下载视频: {video_id}")
    
    output_template = os.path.join('videos', '%(id)s-%(title)s.%(ext)s')
    
    # 基本下载命令
    download_cmd = [
        'yt-dlp',
        f'https://www.bilibili.com/video/{video_id}',
        '-o', output_template,
        '--write-info-json',
        '--write-thumbnail',
    ]
    
    # 如果需要字幕
    if include_subtitles:
        download_cmd.extend([
            '--write-auto-sub',
            '--sub-format', 'vtt',
            '--sub-langs', 'zh-CN',
            '--convert-subs', 'srt',
        ])
    
    try:
        subprocess.run(download_cmd, check=True)
        print(f"视频 {video_id} 下载完成")
        return True
    except subprocess.SubprocessError as e:
        print(f"下载视频 {video_id} 失败: {e}")
        return False

def batch_download(uploader_name, max_videos=10):
    """批量下载UP主视频"""
    videos = get_uploader_videos(uploader_name)
    
    if not videos:
        print("未找到视频，退出")
        return
    
    # 限制下载数量
    videos_to_download = videos[:min(max_videos, len(videos))]
    
    print(f"开始下载 {len(videos_to_download)} 个视频...")
    
    for i, video in enumerate(videos_to_download):
        print(f"[{i+1}/{len(videos_to_download)}] 正在处理: {video['title']}")
        download_video(video['id'])

def main():
    parser = argparse.ArgumentParser(description='B站视频下载工具')
    parser.add_argument('--uploader', '-u', help='UP主名称')
    parser.add_argument('--video', '-v', help='单个视频ID (BV号)')
    parser.add_argument('--max', '-m', type=int, default=10, help='最大下载视频数量')
    parser.add_argument('--no-subtitles', action='store_true', help='不下载字幕')
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    # 记录开始时间
    start_time = datetime.now()
    print(f"下载开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.uploader:
        batch_download(args.uploader, args.max)
    elif args.video:
        download_video(args.video, not args.no_subtitles)
    else:
        parser.print_help()
    
    # 记录结束时间
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"下载结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration}")

if __name__ == "__main__":
    main() 
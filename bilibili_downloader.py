#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import json
import argparse
import requests
import re
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
    
    # 安装requests库
    try:
        import requests
        print("requests库已安装")
    except ImportError:
        print("正在安装requests...")
        subprocess.run(['pip', 'install', 'requests'], check=True)
        print("requests安装完成")
    
    # 创建输出目录
    os.makedirs('videos', exist_ok=True)
    os.makedirs('subtitles', exist_ok=True)
    os.makedirs('metadata', exist_ok=True)

def get_uploader_id(uploader_name):
    """通过UP主名称获取UP主UID"""
    print(f"正在查找UP主 '{uploader_name}' 的UID...")
    
    # 使用B站搜索API查找UP主
    search_url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword={uploader_name}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        response = requests.get(search_url, headers=headers)
        data = response.json()
        
        if data['code'] == 0 and data['data']['result']:
            for result in data['data']['result']:
                if result['uname'] == uploader_name:
                    uid = result['mid']
                    print(f"找到UP主UID: {uid}")
                    return uid
            
            # 如果没有完全匹配，使用第一个结果
            uid = data['data']['result'][0]['mid']
            print(f"未找到完全匹配的UP主，使用最相关结果 UID: {uid}")
            return uid
        else:
            print(f"未找到UP主: {uploader_name}")
            return None
    
    except Exception as e:
        print(f"查找UP主UID失败: {e}")
        return None

def get_uploader_videos_by_uid(uid, max_videos=10):
    """通过UP主UID获取视频列表"""
    if not uid:
        return []
    
    print(f"正在获取UP主(UID:{uid})的视频列表...")
    
    # 使用B站API获取UP主视频列表
    videos_url = f"https://api.bilibili.com/x/space/arc/search?mid={uid}&ps={max_videos}&pn=1&order=pubdate"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        response = requests.get(videos_url, headers=headers)
        data = response.json()
        
        if data['code'] == 0 and 'list' in data['data'] and 'vlist' in data['data']['list']:
            video_list = data['data']['list']['vlist']
            videos = []
            
            for video in video_list:
                bvid = video['bvid']
                title = video['title']
                videos.append({'id': bvid, 'title': title})
            
            print(f"找到 {len(videos)} 个视频")
            return videos
        else:
            print(f"获取视频列表失败，API返回: {data}")
            return []
    
    except Exception as e:
        print(f"获取视频列表失败: {e}")
        return []

def get_uploader_videos(uploader_name, max_videos=10):
    """获取UP主的视频列表"""
    # 先获取UP主UID
    uid = get_uploader_id(uploader_name)
    if not uid:
        # 尝试直接使用名称作为关键词搜索视频
        print(f"尝试直接搜索 '{uploader_name}' 的视频...")
        
        search_url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={uploader_name}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        try:
            response = requests.get(search_url, headers=headers)
            data = response.json()
            
            if data['code'] == 0 and data['data']['result']:
                videos = []
                for video in data['data']['result'][:max_videos]:
                    bvid = video['bvid']
                    title = video['title']
                    videos.append({'id': bvid, 'title': title})
                
                print(f"通过关键词搜索找到 {len(videos)} 个视频")
                return videos
            else:
                print("未找到相关视频")
                return []
        
        except Exception as e:
            print(f"搜索视频失败: {e}")
            return []
    
    # 使用UID获取视频列表
    return get_uploader_videos_by_uid(uid, max_videos)

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
    videos = get_uploader_videos(uploader_name, max_videos)
    
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
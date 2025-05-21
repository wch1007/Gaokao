#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import glob
import argparse
from datetime import datetime

def clean_subtitle_text(text):
    """清理字幕文本，去除时间戳和格式信息等"""
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除多余空格和换行
    text = re.sub(r'\s+', ' ', text)
    # 去除前后空格
    text = text.strip()
    return text

def parse_srt_file(srt_file):
    """解析SRT格式字幕文件，提取纯文本"""
    if not os.path.exists(srt_file):
        print(f"文件不存在: {srt_file}")
        return ""
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 正则表达式匹配SRT格式中的文本部分
    pattern = r'\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}\s+(.*?)(?=\n\n\d+|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # 清理每个字幕文本
    cleaned_texts = [clean_subtitle_text(m) for m in matches]
    
    # 合并所有文本
    full_text = ' '.join(cleaned_texts)
    return full_text

def extract_subtitles_from_directory(directory='videos', output_dir='text_data'):
    """从目录中提取所有字幕文件的文本"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有SRT文件
    srt_files = glob.glob(os.path.join(directory, '**', '*.srt'), recursive=True)
    
    if not srt_files:
        print(f"在 {directory} 目录下未找到SRT字幕文件")
        return
    
    print(f"找到 {len(srt_files)} 个字幕文件")
    
    for i, srt_file in enumerate(srt_files):
        print(f"[{i+1}/{len(srt_files)}] 处理文件: {srt_file}")
        
        # 获取视频ID和标题
        filename = os.path.basename(srt_file)
        video_id = filename.split('-')[0]
        
        # 提取并清理文本
        text = parse_srt_file(srt_file)
        
        if text:
            # 保存提取的文本
            output_file = os.path.join(output_dir, f"{video_id}_text.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"保存文本文件: {output_file}")
        else:
            print(f"未能从 {srt_file} 提取到文本")

def process_video_info(directory='videos', output_dir='text_data'):
    """处理视频信息JSON文件，提取元数据"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有JSON信息文件
    json_files = glob.glob(os.path.join(directory, '*.info.json'))
    
    if not json_files:
        print(f"在 {directory} 目录下未找到视频信息文件")
        return
    
    print(f"找到 {len(json_files)} 个视频信息文件")
    
    # 创建汇总信息
    video_metadata = []
    
    for i, json_file in enumerate(json_files):
        print(f"[{i+1}/{len(json_files)}] 处理文件: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取关键信息
            metadata = {
                'id': data.get('id', ''),
                'title': data.get('title', ''),
                'uploader': data.get('uploader', ''),
                'upload_date': data.get('upload_date', ''),
                'description': data.get('description', ''),
                'view_count': data.get('view_count', 0),
                'like_count': data.get('like_count', 0),
                'tags': data.get('tags', []),
            }
            
            video_metadata.append(metadata)
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"处理文件 {json_file} 失败: {e}")
    
    # 保存汇总元数据
    if video_metadata:
        metadata_file = os.path.join(output_dir, 'video_metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(video_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"保存元数据文件: {metadata_file}")

def main():
    parser = argparse.ArgumentParser(description='B站视频字幕提取工具')
    parser.add_argument('--videos-dir', '-v', default='videos', help='视频和字幕文件目录')
    parser.add_argument('--output-dir', '-o', default='text_data', help='输出文本文件目录')
    parser.add_argument('--metadata', '-m', action='store_true', help='是否处理视频元数据')
    
    args = parser.parse_args()
    
    # 记录开始时间
    start_time = datetime.now()
    print(f"处理开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 提取字幕文本
    extract_subtitles_from_directory(args.videos_dir, args.output_dir)
    
    # 处理元数据
    if args.metadata:
        process_video_info(args.videos_dir, args.output_dir)
    
    # 记录结束时间
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"处理结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration}")

if __name__ == "__main__":
    main() 
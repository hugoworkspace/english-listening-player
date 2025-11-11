#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试示例文件
用于演示英语精听复读软件的功能和使用方法
"""

import os
import tempfile

def create_sample_srt():
    """创建一个示例SRT字幕文件用于测试"""
    
    # SRT文件内容示例
    srt_content = """1
00:00:01,000 --> 00:00:04,500
Hello, welcome to this English learning program.

2
00:00:04,600 --> 00:00:08,200
Today we will learn some useful English expressions.

3
00:00:08,300 --> 00:00:12,000
Practice makes perfect, so let's get started.

4
00:00:12,100 --> 00:00:16,500
The more you practice, the better you will become.

5
00:00:16,600 --> 00:00:20,000
Keep learning and never give up on your goals.
"""
    
    # 创建临时SRT文件
    temp_dir = tempfile.gettempdir()
    srt_path = os.path.join(temp_dir, "sample_english.srt")
    
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    print(f"示例SRT文件已创建: {srt_path}")
    return srt_path

def print_usage_instructions():
    """打印使用说明"""
    
    print("=" * 60)
    print("英语精听复读软件 - 使用说明")
    print("=" * 60)
    print()
    print("1. 软件启动")
    print("   运行命令: python english_listening_player.py")
    print()
    print("2. 文件加载")
    print("   - 点击'选择视频文件'按钮选择视频/音频文件")
    print("   - 点击'选择字幕文件'按钮选择SRT字幕文件")
    print("   - 文件格式支持:")
    print("     * 视频: MP4, AVI, MKV, MOV")
    print("     * 音频: MP3, WAV, FLAC")
    print("     * 字幕: SRT")
    print()
    print("3. 学习流程")
    print("   - 点击'播放'开始逐句精听")
    print("   - 当前句子会在A-B点之间自动循环播放")
    print("   - 使用'上一句'/'下一句'切换句子")
    print("   - 点击'播放列表'查看所有字幕内容")
    print()
    print("4. 学习建议")
    print("   - 每句话循环播放5-10遍")
    print("   - 跟读模仿发音和语调")
    print("   - 理解句子含义和语法结构")
    print()
    print("5. 获取学习素材")
    print("   - TED官网: https://www.ted.com")
    print("   - BBC Learning English: https://www.bbc.co.uk/learningenglish")
    print("   - VOA Learning English: https://learningenglish.voanews.com")
    print()
    print("6. 技术支持")
    print("   - 确保已安装VLC播放器")
    print("   - 检查视频和字幕文件格式")
    print("   - 确认SRT文件时间轴格式正确")
    print("=" * 60)

def demonstrate_srt_parsing():
    """演示SRT文件解析过程"""
    
    print("\n" + "=" * 50)
    print("SRT文件解析演示")
    print("=" * 50)
    
    # 创建示例SRT文件
    srt_path = create_sample_srt()
    
    # 模拟解析过程
    print(f"\n解析SRT文件: {srt_path}")
    print("\n解析结果:")
    
    # 模拟解析后的数据结构
    subtitles = [
        {
            'index': 1,
            'start': 1000,    # 毫秒
            'end': 4500,      # 毫秒
            'text': "Hello, welcome to this English learning program.",
            'duration': 3500  # 毫秒
        },
        {
            'index': 2,
            'start': 4600,
            'end': 8200,
            'text': "Today we will learn some useful English expressions.",
            'duration': 3600
        },
        {
            'index': 3,
            'start': 8300,
            'end': 12000,
            'text': "Practice makes perfect, so let's get started.",
            'duration': 3700
        }
    ]
    
    for sub in subtitles:
        print(f"\n句子 {sub['index']}:")
        print(f"  时间: {sub['start']}ms - {sub['end']}ms (时长: {sub['duration']}ms)")
        print(f"  内容: {sub['text']}")
    
    print(f"\n总句子数: {len(subtitles)}")
    print("\n时间轴转换说明:")
    print("  SRT格式: 00:01:30,500 -> 90500毫秒")
    print("  计算: (0*3600 + 1*60 + 30)*1000 + 500 = 90500ms")

def demonstrate_loop_control():
    """演示循环控制逻辑"""
    
    print("\n" + "=" * 50)
    print("循环控制逻辑演示")
    print("=" * 50)
    
    print("\n循环播放机制:")
    print("1. 设置循环区间: A点(开始) -> B点(结束)")
    print("2. 启动定时器检查播放位置")
    print("3. 当播放位置 >= B点时，跳回A点")
    print("4. 重复步骤2-3，实现无限循环")
    
    print("\n技术实现:")
    print("  - 使用QTimer定时器，每100ms检查一次")
    print("  - VLC播放器位置使用0-1的浮点数表示")
    print("  - 需要在毫秒和比例之间精确转换")
    
    print("\n示例:")
    print("  视频总时长: 120000ms (2分钟)")
    print("  循环区间: 10000ms - 15000ms")
    print("  位置计算:")
    print("    A点比例: 10000 / 120000 = 0.0833")
    print("    B点比例: 15000 / 120000 = 0.1250")
    print("  当播放位置 >= 0.1250时，设置位置为0.0833")

if __name__ == "__main__":
    print_usage_instructions()
    demonstrate_srt_parsing()
    demonstrate_loop_control()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("现在可以运行主程序开始学习:")
    print("  python english_listening_player.py")
    print("=" * 60)

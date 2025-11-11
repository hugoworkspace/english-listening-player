#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试播放按钮是否从定位的位置开始播放
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from english_listening_player import MainWindow

def test_play_from_position():
    """测试播放按钮是否从定位的位置开始播放"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 延迟3秒后检查播放器状态
    def check_state():
        if hasattr(window, 'vlc_player'):
            is_playing = window.vlc_player.is_playing
            play_button_text = window.play_pause_btn.text()
            current_pos = window.vlc_player.get_current_position()
            
            message = f"播放器状态检查:\n"
            message += f"播放器是否正在播放: {is_playing}\n"
            message += f"播放按钮文字: {play_button_text}\n"
            message += f"当前播放位置: {current_pos}ms\n"
            
            if not is_playing and play_button_text == "播放":
                message += "\n✅ 程序启动后处于暂停状态\n"
                
                # 模拟点击播放按钮
                window.toggle_play_pause()
                
                # 延迟1秒后检查播放是否从定位位置开始
                def check_play_position():
                    new_pos = window.vlc_player.get_current_position()
                    is_now_playing = window.vlc_player.is_playing
                    
                    message2 = f"点击播放按钮后:\n"
                    message2 += f"播放器是否正在播放: {is_now_playing}\n"
                    message2 += f"播放按钮文字: {window.play_pause_btn.text()}\n"
                    message2 += f"当前播放位置: {new_pos}ms\n"
                    
                    # 检查位置是否接近定位位置（允许一定误差）
                    if abs(new_pos - 46803) < 5000:  # 5秒误差范围
                        message2 += "\n✅ 测试通过：播放从定位位置开始"
                    else:
                        message2 += f"\n❌ 测试失败：播放从头开始，期望位置: 46803ms, 实际位置: {new_pos}ms"
                    
                    QMessageBox.information(window, "播放位置检查", message2)
                
                QTimer.singleShot(1000, check_play_position)
            else:
                message += "\n❌ 测试失败：程序启动后没有正确处于暂停状态"
                QMessageBox.information(window, "状态检查", message)
    
    # 3秒后执行检查
    QTimer.singleShot(3000, check_state)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_play_from_position()

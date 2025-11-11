#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试程序启动后是否处于暂停状态
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from english_listening_player import MainWindow

def test_pause_state():
    """测试程序启动后是否处于暂停状态"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 延迟2秒后检查播放器状态
    def check_state():
        if hasattr(window, 'vlc_player'):
            is_playing = window.vlc_player.is_playing
            play_button_text = window.play_pause_btn.text()
            
            message = f"播放器状态检查:\n"
            message += f"播放器是否正在播放: {is_playing}\n"
            message += f"播放按钮文字: {play_button_text}\n"
            message += f"播放按钮是否启用: {window.play_pause_btn.isEnabled()}\n"
            
            if not is_playing and play_button_text == "播放":
                message += "\n✅ 测试通过：程序启动后处于暂停状态，等待用户点击播放"
            else:
                message += "\n❌ 测试失败：程序启动后没有正确处于暂停状态"
            
            QMessageBox.information(window, "状态检查", message)
    
    # 2秒后执行检查
    QTimer.singleShot(2000, check_state)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_pause_state()

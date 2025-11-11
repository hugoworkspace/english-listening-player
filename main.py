#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语精听复读软件 - 主程序
实现尚雯婕英语学习法中的逐句精听和影子跟读功能

主要功能：
1. 视频/音频文件播放
2. SRT字幕文件解析和时间轴提取
3. 精确的逐句循环播放
4. 播放控制（播放/暂停、上一句/下一句）
5. 简洁直观的用户界面

技术栈：
- PyQt5: 图形界面
- python-vlc: 媒体播放
- pysrt: 字幕文件解析
"""

import sys
import os
import time
from typing import List, Tuple, Optional
import threading

# 第三方库
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    import vlc
    import pysrt
except ImportError as e:
    print(f"缺少必要的库: {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)


class SubtitleEntry:
    """字幕条目类，存储单个句子的时间信息"""
    def __init__(self, start_ms: int, end_ms: int, text: str):
        self.start_ms = start_ms  # 起始时间（毫秒）
        self.end_ms = end_ms        # 结束时间（毫秒）
        self.text = text            # 字幕文本
        self.start_time = start_ms / 1000.0  # 转换为秒
        self.end_time = end_ms / 1000.0      # 转换为秒


class MediaPlayer:
    """媒体播放器类 - 封装VLC播放器功能"""
    
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.is_playing = False
        self.current_media = None
        self.current_position = 0.0
        
    def load_media(self, file_path: str) -> bool:
        """加载媒体文件"""
        try:
            if not os.path.exists(file_path):
                return False
                
            self.current_media = file_path
            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            self.is_playing = False
            return True
        except Exception as e:
            print(f"加载媒体文件失败: {e}")
            return False
    
    def play(self) -> bool:
        """开始播放"""
        if not self.current_media:
            return False
            
        try:
            self.player.play()
            self.is_playing = True
            return True
        except Exception as e:
            print(f"播放失败: {e}")
            return False
    
    def pause(self):
        """暂停播放"""
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
    
    def stop(self):
        """停止播放"""
        self.player.stop()
        self.is_playing = False
        self.current_position = 0.0
    
    def get_position(self) -> float:
        """获取当前播放位置（秒）"""
        return self.player.get_time() / 1000.0
    
    def set_position(self, position: float):
        """设置播放位置（秒）"""
        self.player.set_time(int(position * 1000))
        self.current_position = position
    
    def get_duration(self) -> float:
        """获取媒体总时长（秒）"""
        return self.player.get_length() / 1000.0
    
    def is_playing(self) -> bool:
        return self.is_playing


class SubtitleParser:
    """字幕文件解析器"""
    
    @staticmethod
    def parse_srt_file(file_path: str) -> List[SubtitleEntry]:
        """
        解析SRT文件并返回字幕条目列表
        
        Args:
            file_path: SRT文件路径
            
        Returns:
            List[SubtitleEntry]: 字幕条目列表
        """
        try:
            # 使用pysrt解析SRT文件
            subs = pysrt.open(file_path)
            entries = []
            
            for sub in subs:
                # 转换时间戳到毫秒
                start_ms = SubtitleParser._time_to_ms(sub.start)
                end_ms = SubtitleParser._time_to_ms(sub.end)
                
                # 清理文本（移除多余空白和换行符）
                text = sub.text.replace('\n', ' ').strip()
                
                entry = SubtitleEntry(start_ms, end_ms, text)
                entries.append(entry)
                
            return entries
            
        except Exception as e:
            print(f"解析SRT文件失败: {e}")
            return []
    
    @staticmethod
    def _time_to_ms(time_obj) -> int:
        """
        将时间对象转换为毫秒
        
        Args:
            time_obj: pysrt时间对象
            
        Returns:
            int: 毫秒数
        """
        # pysrt的时间对象包含hours, minutes, seconds, milliseconds属性
        return (time_obj.hours * 3600 + 
                time_obj.minutes * 60 + 
                time_obj.seconds) * 1000 + time_obj.milliseconds


class PrecisionPlayer(QWidget):
    """精确播放组件"""
    
    # 信号定义
    sentence_changed = pyqtSignal(int)  # 当前句子索引变化
    position_updated = pyqtSignal(float)  # 位置更新（秒）
    
    def __init__(self):
        super().__init__()
        self.subtitle_entries: List[SubtitleEntry] = []
        self.current_sentence_index = 0
        self.loop_mode = True  # 循环模式
        self.loop_thread = None
        self.is_looping = False
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # 播放控制区域
        control_layout = QHBoxLayout()
        
        # 播放/暂停按钮
        self.play_button = QPushButton("▶️ 播放")
        self.play_button.clicked.connect(self.toggle_playback)
        control_layout.addWidget(self.play_button)
        
        # 循环模式按钮
        self.loop_button = QPushButton("🔄 循环模式: 开")
        self.loop_button.clicked.connect(self.toggle_loop_mode)
        control_layout.addWidget(self.loop_button)
        
        layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # 时间显示
        self.time_label = QLabel("00:00 / 00:00")
        layout.addWidget(self.time_label)
        
        # 当前句子显示
        self.sentence_label = QLabel("请加载媒体文件和字幕文件")
        self.sentence_label.setWordWrap(True)
        self.sentence_label.setAlignment(Qt.AlignCenter)
        self.sentence_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                min-height: 60px;
            }
        """)
        layout.addWidget(self.sentence_label)
        
        # 精听控制区域
        precision_layout = QHBoxLayout()
        
        # 精听按钮
        self.precision_button = QPushButton("🎯 精听模式")
        self.precision_button.clicked.connect(self.start_precision_mode)
        precision_layout.addWidget(self.precision_button)
        
        # 循环播放按钮
        self.loop_button = QButton("🔁 循环播放")
        self.loop_button.clicked.connect(self.start_loop_playback)
        precision_layout.addWidget(self.loop_button)
        
        layout.addLayout(precision_layout)
        
        self.setLayout(layout)
        
    def load_media_file(self, file_path: str) -> bool:
        """加载媒体文件"""
        return self.player.load_media_file(file_path)
        
    def load_subtitle_file(self, file_path: str) -> bool:
        """加载字幕文件"""
        try:
            self.subtitle_entries = SubtitleParser.parse_srt_file(file_path)
            if not self.subtitle_entries:
                return False
                
            # 更新显示
            self.update_sentence_display()
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"字幕文件解析失败: {e}")
            return False
    
    def update_sentence_display(self):
        """更新当前句子显示"""
        if not self.subtitle_entries:
            self.sentence_label.setText("请加载媒体文件和字幕文件")
            return
            
        if 0 <= self.current_sentence_index < len(self.subtitle_entries):
            current_entry = self.subtitle_entries[self.current_sentence_index]
            self.sentence_label.setText(f"第 {self.current_sentence_index + 1} 句:\n{current_entry.text}")
    
    def toggle_playback(self):
        """切换播放/暂停"""
        if self.player.is_playing:
            self.player.pause()
            self.play_button.setText("▶️ 播放")
        else:
            self.player.play()
            self.play_button.setText("⏸️ 暂停")
    
    def start_precision_mode(self):
        """启动精听模式"""
        if not self.subtitle_entries:
            QMessageBox.warning(self, "警告", "请先加载媒体文件和字幕文件")
            return
            
        self.loop_mode = True
        self.current_sentence_index = 0
        self.precision_button.setText("🎯 精听模式: 开")
        
        # 启动精听线程
        self.loop_thread = threading.Thread(target=self._precision_loop)
        self.loop_thread.daemon = True
        self.loop_thread.start()
        
    def _precision_loop(self):
        """精听模式主循环"""
        while self.loop_mode and self.current_sentence_index < len(self.subtitle_entries):
            entry = self.subtitle_entries[self.current_sentence_index]
            
            # 跳转到当前句子的开始时间
            self.player.set_position(entry.start_time)
            
            # 播放当前句子
            while (self.player.get_position() < entry.end_time and 
                   self.loop_mode and 
                   self.current_sentence_index < len(self.subtitle_entries)):
                
                if not self.player.is_playing():
                    self.player.play()
                
                # 更新UI（需要在主线程中执行）
                QTimer.singleShot(0, self.update_ui)
                time.sleep(0.1)  # 100ms更新间隔，确保精确控制
            
            # 发送信号通知主线程更新UI
            self.sentence_changed.emit(self.current_sentence_index)
            
            # 短暂停顿
            time.sleep(0.5)
            
            # 自动进入下一句
            if self.current_sentence_index < len(self.subtitle_entries) - 1:
                self.current_sentence_index += 1
            else:
                # 播放完毕
                self.loop_mode = False
                break
    
    def start_loop_playback(self):
        """开始循环播放"""
        if not self.subtitle_entries:
            QMessageBox.warning(self, "警告", "请先加载字幕文件")
            return
            
        self.loop_mode = True
        self.is_looping = True
        
        # 启动循环播放线程
        self.loop_thread = threading.Thread(target=self._loop_playback_thread)
        self.loop_thread.daemon = True
        self.loop_thread.start()
        
        self.loop_button.setText("🔄 循环播放: 开")
    
    def _loop_playback_thread(self):
        """循环播放线程"""
        while self.is_looping and self.loop_mode:
            for i, entry in enumerate(self.subtitle_entries):
                if not self.is_looping or not self.loop_mode:
                    break
                    
                # 跳转到当前句子
                self.player.set_position(entry.start_time)
                
                # 播放当前句子
                while (self.player.get_position() < entry.end_time and 
                       self.is_looping and self.loop_mode):
                    
                    if not self.player.is_playing():
                        self.player.play()
                    
                    time.sleep(0.1)  # 100ms更新间隔
                
                # 发送信号
                self.sentence_changed.emit(i)
                time.sleep(0.5)  # 句子间间隔
    
    def stop_loop_playback(self):
        """停止循环播放"""
        self.is_looping = False
        self.loop_mode = False
        self.loop_button.setText("🔄 循环播放: 关")
    
    def next_sentence(self):
        """跳转到下一句"""
        if self.current_sentence_index < len(self.subtitle_entries) - 1:
            self.current_sentence_index += 1
            self.update_sentence_display()
    
    def previous_sentence(self):
        """跳转到上一句"""
        if self.current_sentence_index > 0:
            self.current_sentence_index -= 1
            self.update_sentence_display()


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.player = PrecisionPlayer()
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("英语精听复读软件")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        
        # 媒体文件选择
        self.media_button = QPushButton("选择媒体文件")
        self.media_button.clicked.connect(self.select_media_file)
        file_layout.addWidget(self.media_button)
        
        # 字幕文件选择
        self.subtitle_button = QButton("选择字幕文件")
        self.subtitle_button.clicked.connect(self.select_subtitle_file)
        file_layout.addWidget(self.subtitle_button)
        
        layout.addLayout(file_layout)
        
        # 精听控制区域
        precision_layout = QHBoxLayout()
        
        # 精听模式按钮
        self.precision_mode_button = QPushButton("🎯 精听模式")
        self.precision_mode_button.clicked.connect(self.start_precision_mode)
        precision_layout.addWidget(self.precision_mode_button)
        
        # 循环播放按钮
        self.loop_button = QPushButton("🔄 循环播放")
        self.loop_button.clicked.connect(self.start_loop_mode)
        precision_layout.addWidget(self.loop_button)
        
        # 播放控制按钮
        self.play_button = QPushButton("▶️ 播放")
        self.play_button.clicked.connect(self.toggle_playback)
        precision_layout.addWidget(self.play_button)
        
        # 暂停按钮
        self.pause_button = QPushButton("⏸️ 暂停")
        self.pause_button.clicked.connect(self.pause_playback)
        precision_layout.addWidget(self.pause_button)
        
        # 精听控制按钮
        self.next_button = QPushButton("下一句")
        self.next_button.clicked.connect(self.next_sentence)
        precision_layout.addWidget(self.next_button)
        
        self.prev_button = QPushButton("上一句")
        self.prev_button.clicked.connect(self.previous_sentence)
        precision_layout.addWidget(self.prev_button)
        
        layout.addLayout(precision_layout)
        
        # 状态显示区域
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        # 精听模式状态
        self.precision_status_label = QLabel("精听模式: 关闭")
        layout.addWidget(self.precision_status_label)
        
        # 菜单栏
        self.create_menu_bar()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 打开媒体文件
        open_media_action = QAction('打开媒体文件', self)
        open_media_action.triggered.connect(self.select_media_file)
        file_menu.addAction(open_media_action)
        
        # 打开字幕文件
        open_subtitle_action = QAction('打开字幕文件')
        open_subtitle_action.triggered.connect(self.select_subtitle_file)
        file_menu.addAction(open_subtitle_action)
        
        # 精听菜单
        precision_menu = menubar.addMenu('精听模式')
        
        # 启动精听模式
        start_precision_action = QAction('启动精听模式')
        start_precision_action.triggered.connect(self.start_precision_mode)
        precision_menu.addAction(start_precision_action)
        
        # 停止精听模式
        stop_precision_action = QAction('停止精听模式')
        stop_precision_action.triggered.connect(self.stop_precision_mode)
        precision_menu.addAction(stop_precision_action)
        
    def select_media_file(self):
        """选择媒体文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择媒体文件", "", 
            "媒体文件 (*.mp4 *.mp3 *.avi *.mov);;所有文件 (*)"
        )
        
        if file_path:
            if self.player.load_media_file(file_path):
                self.status_label.setText(f"媒体文件已加载: {os.path.basename(file_path)}")
                self.status_label.setStyleSheet("color: green")
            else:
                self.status_label.setText("媒体文件加载失败")
                self.status_label.setStyleSheet("color: red")
    
    def select_subtitle_file(self):
        """选择字幕文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", 
            "SRT文件 (*.srt);;所有文件 (*)"
        )
        
        if file_path:
            if self.player.load_subtitle_file(file_path):
                self.status_label.setText(f"字幕文件已加载: {os.path.basename(file_path)}")
                self.status_label.setStyleSheet("color: blue")
            else:
                self.status_label.setText("字幕文件加载失败")
                self.status_label.setStyleSheet("color: red")
    
    def start_precision_mode(self):
        """启动精听模式"""
        self.player.start_precision_mode()
        self.precision_status_label.setText("精听模式: 开启")
        self.precision_status_label.setStyleSheet("color: green")
        self.status_label.setText("精听模式已启动")
    
    def start_loop_mode(self):
        """启动循环模式"""
        self.player.start_loop_playback()
        self.status_label.setText("循环模式: 开启")
        self.status_label.setStyleSheet("color: orange")
    
    def toggle_playback(self):
        """切换播放/暂停"""
        if self.player.is_playing():
            self.player.pause()
            self.play_button.setText("▶️ 播放")
        else:
            self.player.play()
            self.play_button.setText("⏸️ 暂停")
    
    def pause_playback(self):
        """暂停播放"""
        self.player.pause()
        self.play_button.setText("▶️ 播放")
    
    def next_sentence(self):
        """跳转到下一句"""
        self.player.next_sentence()
        self.status_label.setText(f"已跳转到第 {self.player.current_sentence_index + 1} 句")
    
    def previous_sentence(self):
        """跳转到上一句"""
        self.player.previous_sentence()
        self.status_label.setText(f"已跳转到第 {self.player.current_sentence_index + 1} 句")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("英语精听复读软件")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("English Learning Tools")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 启动应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语精听复读软件
基于尚雯婕英语学习法 - 逐句精听和影子跟读
作者: 个人学习项目
"""

import sys
import os
import json
import vlc
import pysrt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QListWidget, QStackedWidget, QFrame, QMessageBox,
                            QSpinBox, QDialog, QDialogButtonBox, QFormLayout,
                            QFontComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor


class SoftwareSettingsDialog(QDialog):
    """软件设置对话框"""
    
    def __init__(self, parent=None, current_font_size=16, current_font_family="Arial", 
                 repeat_interval=0, repeat_count=0, auto_next=False):
        super().__init__(parent)
        self.current_font_size = current_font_size
        self.current_font_family = current_font_family
        self.repeat_interval = repeat_interval
        self.repeat_count = repeat_count
        self.auto_next = auto_next
        self.setup_ui()
    
    def setup_ui(self):
        """设置对话框UI"""
        self.setWindowTitle("软件设置")
        self.setGeometry(200, 200, 450, 400)
        
        layout = QFormLayout()
        
        # 字体设置区域
        font_group = QFrame()
        font_group.setStyleSheet("QFrame { border: 1px solid #555; border-radius: 5px; padding: 10px; }")
        font_layout = QFormLayout(font_group)
        
        # 字体家族选择
        self.font_family_combo = QFontComboBox()
        self.font_family_combo.setCurrentFont(QFont(self.current_font_family))
        font_layout.addRow("字体家族:", self.font_family_combo)
        
        # 字体大小选择
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 48)  # 8到48点字体
        self.font_size_spin.setValue(self.current_font_size)
        self.font_size_spin.setSuffix(" 点")
        font_layout.addRow("字体大小:", self.font_size_spin)
        
        # 预览标签
        self.preview_label = QLabel(f"预览文字 - {self.current_font_family} {self.current_font_size}点")
        self.preview_label.setStyleSheet(f"font-family: {self.current_font_family}; font-size: {self.current_font_size}px; padding: 10px;")
        font_layout.addRow("预览:", self.preview_label)
        
        layout.addRow("字体设置:", font_group)
        
        # 复读设置区域
        repeat_group = QFrame()
        repeat_group.setStyleSheet("QFrame { border: 1px solid #555; border-radius: 5px; padding: 10px; }")
        repeat_layout = QFormLayout(repeat_group)
        
        # 复读间隔秒数
        self.repeat_interval_spin = QSpinBox()
        self.repeat_interval_spin.setRange(0, 60)  # 0到60秒
        self.repeat_interval_spin.setValue(self.repeat_interval)
        self.repeat_interval_spin.setSuffix(" 秒")
        repeat_layout.addRow("复读间隔:", self.repeat_interval_spin)
        
        # 复读次数
        self.repeat_count_spin = QSpinBox()
        self.repeat_count_spin.setRange(0, 999)  # 0到999次
        self.repeat_count_spin.setValue(self.repeat_count)
        self.repeat_count_spin.setSuffix(" 次")
        repeat_layout.addRow("复读次数:", self.repeat_count_spin)
        
        # 自动跳到下一句
        self.auto_next_checkbox = QCheckBox("复读完自动跳到下一句")
        self.auto_next_checkbox.setChecked(self.auto_next)
        repeat_layout.addRow("", self.auto_next_checkbox)
        
        layout.addRow("复读设置:", repeat_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        # 连接信号
        self.font_size_spin.valueChanged.connect(self.update_preview)
        self.font_family_combo.currentFontChanged.connect(self.update_preview)
        
        self.setLayout(layout)
    
    def update_preview(self):
        """更新预览"""
        font_family = self.font_family_combo.currentFont().family()
        font_size = self.font_size_spin.value()
        self.preview_label.setText(f"预览文字 - {font_family} {font_size}点")
        self.preview_label.setStyleSheet(f"font-family: {font_family}; font-size: {font_size}px; padding: 10px;")
    
    def get_font_size(self):
        """获取选择的字体大小"""
        return self.font_size_spin.value()
    
    def get_font_family(self):
        """获取选择的字体家族"""
        return self.font_family_combo.currentFont().family()
    
    def get_repeat_interval(self):
        """获取复读间隔秒数"""
        return self.repeat_interval_spin.value()
    
    def get_repeat_count(self):
        """获取复读次数"""
        return self.repeat_count_spin.value()
    
    def get_auto_next(self):
        """获取自动跳到下一句设置"""
        return self.auto_next_checkbox.isChecked()


class SubtitleParser:
    """SRT字幕解析器"""
    
    def __init__(self):
        self.subtitles = []
        self.current_index = 0
    
    def load_srt(self, srt_path):
        """加载并解析SRT字幕文件"""
        try:
            subs = pysrt.open(srt_path)
            self.subtitles = []
            
            for sub in subs:
                # 将时间转换为毫秒
                start_ms = (sub.start.hours * 3600 + sub.start.minutes * 60 + 
                           sub.start.seconds) * 1000 + sub.start.milliseconds
                end_ms = (sub.end.hours * 3600 + sub.end.minutes * 60 + 
                         sub.end.seconds) * 1000 + sub.end.milliseconds
                
                self.subtitles.append({
                    'text': sub.text,
                    'start': start_ms,
                    'end': end_ms,
                    'duration': end_ms - start_ms
                })
            
            self.current_index = 0
            return True
            
        except Exception as e:
            print(f"解析SRT文件失败: {e}")
            return False
    
    def get_current_subtitle(self):
        """获取当前字幕"""
        if 0 <= self.current_index < len(self.subtitles):
            return self.subtitles[self.current_index]
        return None
    
    def next_subtitle(self):
        """跳转到下一句字幕"""
        if self.current_index < len(self.subtitles) - 1:
            self.current_index += 1
            return self.get_current_subtitle()
        return None
    
    def previous_subtitle(self):
        """跳转到上一句字幕"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.get_current_subtitle()
        return None
    
    def get_total_count(self):
        """获取总字幕数量"""
        return len(self.subtitles)


class VLCPlayer(QWidget):
    """VLC播放器封装类"""
    
    # 定义信号
    repeat_completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # 创建VLC实例和媒体播放器
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        
        # 循环播放相关变量
        self.is_looping = False
        self.loop_start = 0
        self.loop_end = 0
        self.loop_timer = QTimer()
        self.loop_timer.timeout.connect(self._check_loop_position)
        
        # 播放状态
        self.is_playing = False
        
        # 复读设置
        self.repeat_count = 0
        self.current_repeat = 0
        self.repeat_interval = 0
        self.auto_next = False
        self.repeat_timer = QTimer()
        self.repeat_timer.timeout.connect(self._handle_repeat_complete)
        
        # 位置设置相关
        self.target_position = 0
        self.position_set_timer = QTimer()
        self.position_set_timer.timeout.connect(self._try_set_position)
        self.position_set_attempts = 0
    
    def load_media(self, media_path):
        """加载媒体文件"""
        media = self.instance.media_new(media_path)
        self.media_player.set_media(media)
        return True
    
    def set_media_position(self, position_ms):
        """设置播放位置（毫秒）"""
        # VLC使用0-1的浮点数表示播放位置
        if self.media_player.get_media():
            length = self.media_player.get_media().get_duration()
            if length > 0:
                position = position_ms / length
                self.media_player.set_position(position)
    
    def get_current_position(self):
        """获取当前播放位置（毫秒）"""
        if self.media_player.get_media():
            position = self.media_player.get_position()
            length = self.media_player.get_media().get_duration()
            return int(position * length)
        return 0
    
    def play(self):
        """开始播放"""
        if self.media_player.play() == 0:
            self.is_playing = True
            return True
        return False
    
    def pause(self):
        """暂停播放"""
        self.media_player.pause()
        self.is_playing = False
    
    def stop(self):
        """停止播放"""
        self.media_player.stop()
        self.is_playing = False
        self.is_looping = False
        self.loop_timer.stop()
    
    def set_loop(self, start_ms, end_ms):
        """设置循环播放区间"""
        self.loop_start = start_ms
        self.loop_end = end_ms
        self.is_looping = True
        
        # 设置初始位置
        self.set_media_position(start_ms)
        
        # 启动循环检查定时器
        self.loop_timer.start(100)  # 每100ms检查一次
    
    def stop_loop(self):
        """停止循环播放"""
        self.is_looping = False
        self.loop_timer.stop()
    
    def _check_loop_position(self):
        """检查循环位置，实现自动循环"""
        if self.is_looping and self.is_playing:
            current_pos = self.get_current_position()
            
            # 如果播放位置超过循环结束点，跳回循环开始点
            if current_pos >= self.loop_end:
                # 更新复读计数
                self.current_repeat += 1
                print(f"复读计数: {self.current_repeat}/{self.repeat_count}")
                
                # 检查是否达到设定的复读次数
                if self.repeat_count > 0 and self.current_repeat >= self.repeat_count:
                    # 达到复读次数，停止循环
                    print(f"达到复读次数 {self.repeat_count}，停止循环")
                    self.stop_loop()
                    # 如果有复读间隔，先暂停播放，等待间隔时间
                    if self.repeat_interval > 0:
                        print(f"复读间隔 {self.repeat_interval} 秒")
                        self.pause()  # 暂停播放
                        self.repeat_timer.start(self.repeat_interval * 1000)
                    else:
                        self._handle_repeat_complete()
                else:
                    # 如果还有复读次数，检查是否需要间隔
                    if self.repeat_interval > 0 and self.current_repeat > 0:
                        # 暂停播放，等待间隔时间后再继续
                        print(f"复读间隔 {self.repeat_interval} 秒")
                        self.pause()
                        self.repeat_timer.start(self.repeat_interval * 1000)
                    else:
                        # 继续循环播放
                        print("继续循环播放")
                        self.set_media_position(self.loop_start)
    
    def _handle_repeat_complete(self):
        """处理复读完成后的逻辑"""
        self.repeat_timer.stop()
        
        # 检查是复读间隔还是复读完成
        if self.current_repeat < self.repeat_count:
            # 这是复读间隔，继续播放
            self.set_media_position(self.loop_start)
            self.play()
        else:
            # 这是复读完成，如果设置了自动跳到下一句，触发下一句
            if self.auto_next:
                # 发射信号通知主窗口
                self.repeat_completed.emit()
    
    def set_repeat_settings(self, repeat_count, repeat_interval, auto_next):
        """设置复读参数"""
        self.repeat_count = repeat_count
        self.repeat_interval = repeat_interval
        self.auto_next = auto_next
        self.current_repeat = 0
    
    def reset_repeat_count(self):
        """重置复读计数"""
        self.current_repeat = 0
    
    def set_position_with_retry(self, position_ms, max_attempts=10):
        """设置播放位置并重试，直到位置设置成功"""
        self.target_position = position_ms
        self.position_set_attempts = 0
        
        print(f"开始设置位置: {position_ms}ms")
        
        # 直接设置位置，不进行任何播放操作
        self.set_media_position(position_ms)
        
        # 确保处于暂停状态
        self.pause()
        
        # 启动重试定时器
        self.position_set_timer.start(100)  # 每100ms检查一次
        
        # 设置最大重试次数
        self.max_position_attempts = max_attempts
    
    def _try_set_position(self):
        """尝试设置位置的重试逻辑"""
        if self.position_set_attempts >= self.max_position_attempts:
            print(f"位置设置失败，已达到最大重试次数: {self.max_position_attempts}")
            self.position_set_timer.stop()
            return
        
        current_pos = self.get_current_position()
        print(f"重试设置位置: 目标={self.target_position}ms, 当前={current_pos}ms, 尝试次数={self.position_set_attempts + 1}")
        
        # 如果当前位置与目标位置相差较大，重新设置位置
        if abs(current_pos - self.target_position) > 1000:  # 相差超过1秒
            self.set_media_position(self.target_position)
            self.position_set_attempts += 1
        else:
            print(f"位置设置成功: 当前={current_pos}ms, 目标={self.target_position}ms")
            self.position_set_timer.stop()


class PlayerWidget(QWidget):
    """播放器控件 - 支持自适应缩放"""
    
    def __init__(self, vlc_player):
        super().__init__()
        self.vlc_player = vlc_player
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        
        # 视频显示区域 - 支持自适应缩放
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumSize(960, 540)  # 设置1080P比例的最小尺寸(16:9)
        
        # 使用弹性布局使视频窗口可以自适应
        layout.addWidget(self.video_frame)
        self.setLayout(layout)
    
    def resizeEvent(self, event):
        """窗口大小改变时自动调整视频尺寸"""
        super().resizeEvent(event)
        # 视频窗口会自动适应父容器大小
    
    def attach_vlc(self):
        """将VLC播放器附加到窗口"""
        if sys.platform == "win32":
            # Windows平台
            self.vlc_player.media_player.set_hwnd(int(self.video_frame.winId()))
        else:
            # Linux/Mac平台
            self.vlc_player.media_player.set_xwindow(int(self.video_frame.winId()))


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.vlc_player = VLCPlayer()
        self.subtitle_parser = SubtitleParser()
        
        self.current_media_path = ""
        self.current_srt_path = ""
        self.config_file = "english_player_config.json"
        
        # 加载配置
        config = self.load_config()
        self.font_size = config['font_size']
        self.font_family = config['font_family']
        self.last_video_dir = config['last_video_dir']
        self.last_srt_dir = config['last_srt_dir']
        self.repeat_interval = config['repeat_interval']
        self.repeat_count = config['repeat_count']
        self.auto_next = config['auto_next']
        
        # 上次播放的文件和进度
        self.last_video_path = config.get('last_video_path', "")
        self.last_srt_path = config.get('last_srt_path', "")
        self.last_subtitle_index = config.get('last_subtitle_index', 0)
        
        self.setup_ui()
        self.setup_signals()
        
        # 初始化时应用复读设置
        self.vlc_player.set_repeat_settings(self.repeat_count, self.repeat_interval, self.auto_next)
        
        # 尝试恢复上次的播放进度
        self.restore_last_session()
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)  # 每500ms更新一次状态
    
    def setup_ui(self):
        """设置主界面UI"""
        self.setWindowTitle("英语精听复读软件")
        self.setGeometry(100, 100, 1000, 700)  # 增加窗口大小
        
        # 设置深色主题
        self.set_dark_theme()
        
        # 设置全局字体
        self.set_global_font()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题栏
        self.title_label = QLabel("英语精听复读软件")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont(self.font_family, max(14, self.font_size), QFont.Bold))
        self.title_label.setStyleSheet("color: white; padding: 10px;")
        main_layout.addWidget(self.title_label)
        
        # 内容区域堆叠窗口
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # 播放界面
        self.setup_play_interface()
        
        # 播放列表界面
        self.setup_playlist_interface()
        
        # 底部控制栏
        self.setup_control_bar(main_layout)
        
        # 默认显示播放界面
        self.stacked_widget.setCurrentIndex(0)
    
    def set_global_font(self):
        """设置全局字体"""
        font = QFont(self.font_family, self.font_size)  # 使用配置的字体家族和大小
        self.setFont(font)
    
    def set_dark_theme(self):
        """设置深色主题"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)
    
    def setup_play_interface(self):
        """设置播放界面"""
        play_widget = QWidget()
        play_layout = QVBoxLayout()
        play_widget.setLayout(play_layout)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        
        self.select_video_btn = QPushButton("选择视频文件")
        self.select_video_btn.setStyleSheet(self.get_button_style())
        file_layout.addWidget(self.select_video_btn)
        
        self.select_srt_btn = QPushButton("选择字幕文件")
        self.select_srt_btn.setStyleSheet(self.get_button_style())
        file_layout.addWidget(self.select_srt_btn)
        
        play_layout.addLayout(file_layout)
        
        # 播放器控件
        self.player_widget = PlayerWidget(self.vlc_player)
        play_layout.addWidget(self.player_widget)
        
        # 进度信息 - 固定高度
        self.progress_label = QLabel("进度: 0/0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setFixedHeight(30)  # 固定高度
        self.progress_label.setStyleSheet(f"color: #ccc; font-family: {self.font_family}; font-size: {max(10, self.font_size - 4)}px;")
        play_layout.addWidget(self.progress_label)
        
        self.stacked_widget.addWidget(play_widget)
    
    def setup_playlist_interface(self):
        """设置播放列表界面"""
        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout()
        playlist_widget.setLayout(playlist_layout)
        
        # 播放列表标题
        playlist_title = QLabel("播放列表")
        playlist_title.setAlignment(Qt.AlignCenter)
        playlist_title.setStyleSheet("color: white; font-size: 18px; padding: 10px;")
        playlist_layout.addWidget(playlist_title)
        
        # 播放列表
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #42a2da;
            }
        """)
        playlist_layout.addWidget(self.playlist_widget)
        
        self.stacked_widget.addWidget(playlist_widget)
    
    def setup_control_bar(self, main_layout):
        """设置底部控制栏"""
        control_frame = QFrame()
        control_frame.setStyleSheet("background-color: #2a2a2a; padding: 10px;")
        control_layout = QHBoxLayout()
        control_frame.setLayout(control_layout)
        
        # 界面切换按钮
        self.playlist_btn = QPushButton("播放列表")
        self.playlist_btn.setStyleSheet(self.get_button_style())
        control_layout.addWidget(self.playlist_btn)
        
        # 软件设置按钮
        self.software_settings_btn = QPushButton("软件设置")
        self.software_settings_btn.setStyleSheet(self.get_button_style())
        control_layout.addWidget(self.software_settings_btn)
        
        control_layout.addStretch()
        
        # 播放控制按钮
        self.prev_btn = QPushButton("上一句")
        self.prev_btn.setStyleSheet(self.get_button_style())
        self.prev_btn.setEnabled(False)
        control_layout.addWidget(self.prev_btn)
        
        self.play_pause_btn = QPushButton("播放")
        self.play_pause_btn.setStyleSheet(self.get_button_style(primary=True))
        self.play_pause_btn.setEnabled(False)
        control_layout.addWidget(self.play_pause_btn)
        
        self.next_btn = QPushButton("下一句")
        self.next_btn.setStyleSheet(self.get_button_style())
        self.next_btn.setEnabled(False)
        control_layout.addWidget(self.next_btn)
        
        control_layout.addStretch()
        
        # 返回播放界面按钮（在播放列表界面显示）
        self.back_btn = QPushButton("返回播放")
        self.back_btn.setStyleSheet(self.get_button_style())
        self.back_btn.setVisible(False)
        control_layout.addWidget(self.back_btn)
        
        main_layout.addWidget(control_frame)
    
    def get_button_style(self, primary=False):
        """获取按钮样式"""
        if primary:
            return f"""
                QPushButton {{
                    background-color: #42a2da;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    font-family: {self.font_family};
                    font-size: {max(14, self.font_size + 2)}px;
                    min-width: 120px;
                    min-height: 50px;
                }}
                QPushButton:hover {{
                    background-color: #3598c5;
                }}
                QPushButton:pressed {{
                    background-color: #2a7ba2;
                }}
                QPushButton:disabled {{
                    background-color: #666;
                    color: #999;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: #555;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 20px;
                    font-family: {self.font_family};
                    font-size: {max(12, self.font_size)}px;
                    min-width: 100px;
                    min-height: 45px;
                }}
                QPushButton:hover {{
                    background-color: #666;
                }}
                QPushButton:pressed {{
                    background-color: #444;
                }}
                QPushButton:disabled {{
                    background-color: #333;
                    color: #666;
                }}
            """
    
    def setup_signals(self):
        """设置信号连接"""
        # 文件选择
        self.select_video_btn.clicked.connect(self.select_video_file)
        self.select_srt_btn.clicked.connect(self.select_srt_file)
        
        # 播放控制
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.next_btn.clicked.connect(self.next_sentence)
        self.prev_btn.clicked.connect(self.previous_sentence)
        
        # 界面切换
        self.playlist_btn.clicked.connect(self.show_playlist)
        self.back_btn.clicked.connect(self.show_play_interface)
        
        # 软件设置
        self.software_settings_btn.clicked.connect(self.show_software_settings)
        
        # 复读完成信号
        self.vlc_player.repeat_completed.connect(self.on_repeat_completed)
    
    def select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", self.last_video_dir, 
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm);;音频文件 (*.mp3 *.wav *.flac *.m4a *.aac);;所有文件 (*.*)"
        )
        
        if file_path:
            self.current_media_path = file_path
            # 更新按钮文字显示文件名（全称，不显示后缀名）
            file_name = os.path.basename(file_path)
            # 移除文件后缀名
            file_name_without_ext = os.path.splitext(file_name)[0]
            self.select_video_btn.setText(file_name_without_ext)
            
            # 保存上次选择的目录
            self.last_video_dir = os.path.dirname(file_path)
            
            if self.vlc_player.load_media(file_path):
                self.player_widget.attach_vlc()
                self.update_file_status()
    
    def select_srt_file(self):
        """选择字幕文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", self.last_srt_dir, "字幕文件 (*.srt)"
        )
        
        if file_path:
            self.current_srt_path = file_path
            # 更新按钮文字显示文件名（全称，不显示后缀名）
            file_name = os.path.basename(file_path)
            # 移除文件后缀名
            file_name_without_ext = os.path.splitext(file_name)[0]
            self.select_srt_btn.setText(file_name_without_ext)
            
            # 保存上次选择的目录
            self.last_srt_dir = os.path.dirname(file_path)
            
            if self.subtitle_parser.load_srt(file_path):
                self.update_file_status()
                # 加载成功后自动开始播放第一句
                self.start_playing_current_sentence()
    
    def update_file_status(self):
        """更新文件状态"""
        has_video = bool(self.current_media_path)
        has_srt = bool(self.current_srt_path)
        
        # 启用播放控制按钮
        self.play_pause_btn.setEnabled(has_video and has_srt)
        self.next_btn.setEnabled(has_video and has_srt)
        self.prev_btn.setEnabled(has_video and has_srt)
    
    def start_playing_current_sentence(self, auto_play=True):
        """开始播放当前句子
        Args:
            auto_play: 是否自动开始播放，False表示只定位到位置但不播放
        """
        current_sub = self.subtitle_parser.get_current_subtitle()
        if current_sub and self.current_media_path:
            # 停止之前的循环
            self.vlc_player.stop_loop()
            
            # 重置复读计数
            self.vlc_player.reset_repeat_count()
            
            # 根据参数决定是否设置循环播放
            if auto_play:
                # 设置循环播放并开始播放
                self.vlc_player.set_loop(current_sub['start'], current_sub['end'])
                if self.vlc_player.play():
                    self.play_pause_btn.setText("暂停")
                    self.update_subtitle_display()
            else:
                # 只定位到位置，不设置循环播放，不播放
                print(f"定位到第 {self.subtitle_parser.current_index + 1} 句，时间位置: {current_sub['start']}ms")
                
                # 确保播放器处于停止状态
                self.vlc_player.stop()
                
                # 直接设置位置，不进行任何播放操作
                self.vlc_player.set_media_position(current_sub['start'])
                
                # 确保处于暂停状态
                self.vlc_player.pause()
                self.play_pause_btn.setText("播放")
                self.update_subtitle_display()
    
    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        if self.vlc_player.is_playing:
            self.vlc_player.pause()
            self.play_pause_btn.setText("播放")
        else:
            # 在开始播放前，先设置循环播放区间
            current_sub = self.subtitle_parser.get_current_subtitle()
            if current_sub and self.current_media_path:
                # 强制从句子开始位置播放，因为我们知道已经定位到这里了
                print(f"从定位位置 {current_sub['start']}ms 开始播放")
                
                # 先设置到句子开始位置
                self.vlc_player.set_media_position(current_sub['start'])
                
                # 延迟一小段时间确保位置设置生效
                QTimer.singleShot(100, lambda: self.vlc_player.set_media_position(current_sub['start']))
                
                # 延迟后开始播放，但不设置循环播放
                def start_playback():
                    if self.vlc_player.play():
                        self.play_pause_btn.setText("暂停")
                        # 播放开始后设置循环播放，使用50毫秒延迟
                        QTimer.singleShot(50, lambda: self.vlc_player.set_loop(current_sub['start'], current_sub['end']))
                
                QTimer.singleShot(150, start_playback)
            else:
                if self.vlc_player.play():
                    self.play_pause_btn.setText("暂停")
    
    def next_sentence(self):
        """播放下一句"""
        next_sub = self.subtitle_parser.next_subtitle()
        if next_sub:
            self.start_playing_current_sentence()
    
    def previous_sentence(self):
        """播放上一句"""
        prev_sub = self.subtitle_parser.previous_subtitle()
        if prev_sub:
            self.start_playing_current_sentence()
    
    def update_subtitle_display(self):
        """更新字幕显示"""
        current_sub = self.subtitle_parser.get_current_subtitle()
        if current_sub:
            # 更新进度信息
            total = self.subtitle_parser.get_total_count()
            current = self.subtitle_parser.current_index + 1
            self.progress_label.setText(f"进度: {current}/{total}")
    
    def update_status(self):
        """更新状态信息"""
        if self.vlc_player.is_playing:
            current_pos = self.vlc_player.get_current_position()
            current_sub = self.subtitle_parser.get_current_subtitle()
            
            if current_sub:
                # 显示当前播放位置信息
                progress_text = f"进度: {self.subtitle_parser.current_index + 1}/{self.subtitle_parser.get_total_count()}"
                self.progress_label.setText(progress_text)
    
    def show_playlist(self):
        """显示播放列表界面"""
        # 更新播放列表内容
        self.playlist_widget.clear()
        for i, sub in enumerate(self.subtitle_parser.subtitles):
            text = sub['text'][:50] + "..." if len(sub['text']) > 50 else sub['text']
            self.playlist_widget.addItem(f"{i+1}. {text}")
        
        # 切换到播放列表界面
        self.stacked_widget.setCurrentIndex(1)
        self.back_btn.setVisible(True)
        self.playlist_btn.setVisible(False)
    
    def show_software_settings(self):
        """显示软件设置对话框"""
        dialog = SoftwareSettingsDialog(self, self.font_size, self.font_family,
                                       self.repeat_interval, self.repeat_count, self.auto_next)
        if dialog.exec_() == QDialog.Accepted:
            new_font_size = dialog.get_font_size()
            new_font_family = dialog.get_font_family()
            new_repeat_interval = dialog.get_repeat_interval()
            new_repeat_count = dialog.get_repeat_count()
            new_auto_next = dialog.get_auto_next()
            
            self.font_size = new_font_size
            self.font_family = new_font_family
            self.repeat_interval = new_repeat_interval
            self.repeat_count = new_repeat_count
            self.auto_next = new_auto_next
            
            # 应用复读设置到播放器
            self.vlc_player.set_repeat_settings(self.repeat_count, self.repeat_interval, self.auto_next)
            
            self.update_font_settings()
    
    def on_repeat_completed(self):
        """处理复读完成信号"""
        # 自动跳到下一句
        self.next_sentence()
    
    def update_font_settings(self):
        """更新所有UI元素的字体设置"""
        # 更新全局字体
        font = QFont(self.font_family, self.font_size)
        self.setFont(font)
        
        # 更新按钮样式
        self.update_button_styles()
        
        
        # 更新进度信息字体
        self.progress_label.setStyleSheet(f"color: #ccc; font-family: {self.font_family}; font-size: {max(10, self.font_size - 4)}px;")
        
        # 更新标题字体
        title_font = QFont(self.font_family, max(14, self.font_size), QFont.Bold)
        # 遍历所有子控件找到标题标签
        for child in self.findChildren(QLabel):
            if child.text() == "英语精听复读软件":
                child.setFont(title_font)
                break
        
        
        # 更新播放列表标题字体
        for child in self.findChildren(QLabel):
            if child.text() == "播放列表":
                child.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(14, self.font_size)}px; padding: 10px;")
                break
        
        # 更新播放列表项字体
        self.playlist_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                font-family: {self.font_family};
                font-size: {max(10, self.font_size - 4)}px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #444;
            }}
            QListWidget::item:selected {{
                background-color: #42a2da;
            }}
        """)
    
    def update_button_styles(self):
        """更新所有按钮的字体大小"""
        # 更新文件选择按钮
        self.select_video_btn.setStyleSheet(self.get_button_style())
        self.select_srt_btn.setStyleSheet(self.get_button_style())
        
        # 更新播放控制按钮
        self.play_pause_btn.setStyleSheet(self.get_button_style(primary=True))
        self.next_btn.setStyleSheet(self.get_button_style())
        self.prev_btn.setStyleSheet(self.get_button_style())
        
        # 更新界面切换按钮
        self.playlist_btn.setStyleSheet(self.get_button_style())
        self.back_btn.setStyleSheet(self.get_button_style())
        self.software_settings_btn.setStyleSheet(self.get_button_style())
    
    def load_config(self):
        """加载配置文件"""
        default_font_size = 16
        default_font_family = "Arial"
        default_repeat_interval = 0
        default_repeat_count = 0
        default_auto_next = False
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    font_size = config.get('font_size', default_font_size)
                    font_family = config.get('font_family', default_font_family)
                    last_video_dir = config.get('last_video_dir', "")
                    last_srt_dir = config.get('last_srt_dir', "")
                    repeat_interval = config.get('repeat_interval', default_repeat_interval)
                    repeat_count = config.get('repeat_count', default_repeat_count)
                    auto_next = config.get('auto_next', default_auto_next)
                    last_video_path = config.get('last_video_path', "")
                    last_srt_path = config.get('last_srt_path', "")
                    last_subtitle_index = config.get('last_subtitle_index', 0)
                    
                    print(f"从配置文件加载: video={last_video_path}, srt={last_srt_path}, index={last_subtitle_index}")  # 调试信息
                    
                    # 确保字体大小在有效范围内
                    if 8 <= font_size <= 48:
                        return {
                            'font_size': font_size,
                            'font_family': font_family,
                            'last_video_dir': last_video_dir,
                            'last_srt_dir': last_srt_dir,
                            'repeat_interval': repeat_interval,
                            'repeat_count': repeat_count,
                            'auto_next': auto_next,
                            'last_video_path': last_video_path,
                            'last_srt_path': last_srt_path,
                            'last_subtitle_index': last_subtitle_index
                        }
                    else:
                        return {
                            'font_size': default_font_size,
                            'font_family': default_font_family,
                            'last_video_dir': "",
                            'last_srt_dir': "",
                            'repeat_interval': default_repeat_interval,
                            'repeat_count': default_repeat_count,
                            'auto_next': default_auto_next,
                            'last_video_path': "",
                            'last_srt_path': "",
                            'last_subtitle_index': 0
                        }
            else:
                return {
                    'font_size': default_font_size,
                    'font_family': default_font_family,
                    'last_video_dir': "",
                    'last_srt_dir': "",
                    'repeat_interval': default_repeat_interval,
                    'repeat_count': default_repeat_count,
                    'auto_next': default_auto_next,
                    'last_video_path': "",
                    'last_srt_path': "",
                    'last_subtitle_index': 0
                }
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {
                'font_size': default_font_size,
                'font_family': default_font_family,
                'last_video_dir': "",
                'last_srt_dir': "",
                'repeat_interval': default_repeat_interval,
                'repeat_count': default_repeat_count,
                'auto_next': default_auto_next,
                'last_video_path': "",
                'last_srt_path': "",
                'last_subtitle_index': 0
            }
    
    def save_config(self):
        """保存配置文件"""
        try:
            config = {
                'font_size': self.font_size,
                'font_family': self.font_family,
                'last_video_dir': self.last_video_dir,
                'last_srt_dir': self.last_srt_dir,
                'repeat_interval': self.repeat_interval,
                'repeat_count': self.repeat_count,
                'auto_next': self.auto_next,
                'last_video_path': self.current_media_path,
                'last_srt_path': self.current_srt_path,
                'last_subtitle_index': self.subtitle_parser.current_index
            }
            print(f"保存配置: {config}")  # 调试信息
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print("配置保存成功")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件 - 保存配置"""
        self.save_config()
        event.accept()
    
    def restore_last_session(self):
        """恢复上次的播放进度"""
        try:
            print(f"尝试恢复上次播放进度: video={self.last_video_path}, srt={self.last_srt_path}, index={self.last_subtitle_index}")
            
            # 检查上次播放的文件是否存在
            if (self.last_video_path and os.path.exists(self.last_video_path) and
                self.last_srt_path and os.path.exists(self.last_srt_path)):
                
                print("文件存在，开始恢复...")
                
                # 设置当前文件路径
                self.current_media_path = self.last_video_path
                self.current_srt_path = self.last_srt_path
                
                # 更新按钮文字显示文件名
                video_file_name = os.path.basename(self.last_video_path)
                video_file_name_without_ext = os.path.splitext(video_file_name)[0]
                self.select_video_btn.setText(video_file_name_without_ext)
                
                srt_file_name = os.path.basename(self.last_srt_path)
                srt_file_name_without_ext = os.path.splitext(srt_file_name)[0]
                self.select_srt_btn.setText(srt_file_name_without_ext)
                
                # 加载媒体文件
                if self.vlc_player.load_media(self.last_video_path):
                    print("媒体文件加载成功")
                    self.player_widget.attach_vlc()
                    
                    # 加载字幕文件
                    if self.subtitle_parser.load_srt(self.last_srt_path):
                        print(f"字幕文件加载成功，共 {len(self.subtitle_parser.subtitles)} 句")
                        
                        # 设置上次的播放进度
                        if 0 <= self.last_subtitle_index < len(self.subtitle_parser.subtitles):
                            self.subtitle_parser.current_index = self.last_subtitle_index
                            print(f"设置播放进度为第 {self.subtitle_parser.current_index + 1} 句")
                        
                        # 更新文件状态
                        self.update_file_status()
                        
                        # 确保播放器处于停止状态
                        self.vlc_player.stop()
                        
                        # 定位到上次播放的句子位置，但不自动播放
                        self.start_playing_current_sentence(auto_play=False)
                        print("恢复完成，已定位到上次播放位置，等待用户点击播放")
                        return True
                    else:
                        print("字幕文件加载失败")
                else:
                    print("媒体文件加载失败")
            else:
                # 文件不存在，清除保存的路径
                if self.last_video_path and not os.path.exists(self.last_video_path):
                    print(f"上次的视频文件不存在: {self.last_video_path}")
                if self.last_srt_path and not os.path.exists(self.last_srt_path):
                    print(f"上次的字幕文件不存在: {self.last_srt_path}")
                print("文件不存在，无法恢复")
                
        except Exception as e:
            print(f"恢复上次播放进度失败: {e}")
        
        return False
    
    def show_play_interface(self):
        """显示播放界面"""
        self.stacked_widget.setCurrentIndex(0)
        self.back_btn.setVisible(False)
        self.playlist_btn.setVisible(True)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("英语精听复读软件")
    app.setApplicationVersion("1.0")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

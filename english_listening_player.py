#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语精听复读软件
基于尚雯婕英语学习法 - 逐句精听和影子跟读
作者: 个人学习项目
"""

import sys
import os
import vlc
import pysrt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QListWidget, QStackedWidget, QFrame, QMessageBox,
                            QSpinBox, QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor


class FontSettingsDialog(QDialog):
    """字体设置对话框"""
    
    def __init__(self, parent=None, current_font_size=16):
        super().__init__(parent)
        self.current_font_size = current_font_size
        self.setup_ui()
    
    def setup_ui(self):
        """设置对话框UI"""
        self.setWindowTitle("字体设置")
        self.setGeometry(200, 200, 300, 150)
        
        layout = QFormLayout()
        
        # 字体大小选择
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 48)  # 8到48点字体
        self.font_size_spin.setValue(self.current_font_size)
        self.font_size_spin.setSuffix(" 点")
        layout.addRow("字体大小:", self.font_size_spin)
        
        # 预览标签
        self.preview_label = QLabel(f"预览文字 - {self.current_font_size}点")
        self.preview_label.setStyleSheet(f"font-size: {self.current_font_size}px; padding: 10px;")
        layout.addRow("预览:", self.preview_label)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        # 连接信号
        self.font_size_spin.valueChanged.connect(self.update_preview)
        
        self.setLayout(layout)
    
    def update_preview(self, size):
        """更新预览"""
        self.preview_label.setText(f"预览文字 - {size}点")
        self.preview_label.setStyleSheet(f"font-size: {size}px; padding: 10px;")
    
    def get_font_size(self):
        """获取选择的字体大小"""
        return self.font_size_spin.value()


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


class VLCPlayer:
    """VLC播放器封装类"""
    
    def __init__(self):
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
                self.set_media_position(self.loop_start)


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
        self.video_frame.setMinimumSize(400, 300)  # 设置最小尺寸
        
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
        self.font_size = 16  # 默认字体大小
        
        self.setup_ui()
        self.setup_signals()
        
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
        title_label = QLabel("英语精听复读软件")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: white; padding: 10px;")
        main_layout.addWidget(title_label)
        
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
        """设置全局字体大小"""
        font = QFont()
        font.setPointSize(16)  # 进一步增大字体大小
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
        
        # 资源提示
        tip_label = QLabel("需要素材？请前往 TED 官方演讲列表等网站自行下载对应的视频和 SRT 字幕文件")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("color: #888; font-size: 12px; padding: 5px;")
        tip_label.setWordWrap(True)
        play_layout.addWidget(tip_label)
        
        # 播放器控件
        self.player_widget = PlayerWidget(self.vlc_player)
        play_layout.addWidget(self.player_widget)
        
        # 字幕显示区域
        self.subtitle_label = QLabel("请选择视频和字幕文件开始学习")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: white;
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
                min-height: 60px;
            }
        """)
        self.subtitle_label.setWordWrap(True)
        play_layout.addWidget(self.subtitle_label)
        
        # 进度信息
        self.progress_label = QLabel("进度: 0/0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #ccc;")
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
        
        # 字体设置按钮
        self.font_settings_btn = QPushButton("字体设置")
        self.font_settings_btn.setStyleSheet(self.get_button_style())
        control_layout.addWidget(self.font_settings_btn)
        
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
        
        # 字体设置
        self.font_settings_btn.clicked.connect(self.show_font_settings)
    
    def select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm);;音频文件 (*.mp3 *.wav *.flac *.m4a *.aac);;所有文件 (*.*)"
        )
        
        if file_path:
            self.current_media_path = file_path
            if self.vlc_player.load_media(file_path):
                self.player_widget.attach_vlc()
                self.update_file_status()
    
    def select_srt_file(self):
        """选择字幕文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "字幕文件 (*.srt)"
        )
        
        if file_path:
            self.current_srt_path = file_path
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
        
        # 更新状态显示
        if has_video and has_srt:
            self.subtitle_label.setText("文件加载成功！点击播放开始学习")
        elif has_video:
            self.subtitle_label.setText("视频文件已加载，请选择字幕文件")
        elif has_srt:
            self.subtitle_label.setText("字幕文件已加载，请选择视频文件")
        else:
            self.subtitle_label.setText("请选择视频和字幕文件开始学习")
    
    def start_playing_current_sentence(self):
        """开始播放当前句子"""
        current_sub = self.subtitle_parser.get_current_subtitle()
        if current_sub and self.current_media_path:
            # 停止之前的循环
            self.vlc_player.stop_loop()
            
            # 设置循环播放
            self.vlc_player.set_loop(current_sub['start'], current_sub['end'])
            
            # 开始播放
            if self.vlc_player.play():
                self.play_pause_btn.setText("暂停")
                self.update_subtitle_display()
    
    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        if self.vlc_player.is_playing:
            self.vlc_player.pause()
            self.play_pause_btn.setText("播放")
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
            self.subtitle_label.setText(current_sub['text'])
            
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
    
    def show_font_settings(self):
        """显示字体设置对话框"""
        dialog = FontSettingsDialog(self, self.font_size)
        if dialog.exec_() == QDialog.Accepted:
            new_font_size = dialog.get_font_size()
            self.font_size = new_font_size
            self.update_font_size()
    
    def update_font_size(self):
        """更新所有UI元素的字体大小"""
        # 更新全局字体
        font = QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        
        # 更新按钮样式
        self.update_button_styles()
        
        # 更新字幕显示区域字体
        self.subtitle_label.setStyleSheet(f"""
            QLabel {{
                background-color: #2a2a2a;
                color: white;
                padding: 15px;
                border-radius: 10px;
                font-size: {max(12, self.font_size - 2)}px;
                min-height: 60px;
            }}
        """)
        
        # 更新进度信息字体
        self.progress_label.setStyleSheet(f"color: #ccc; font-size: {max(10, self.font_size - 4)}px;")
        
        # 更新标题字体
        title_font = QFont("Arial", max(14, self.font_size), QFont.Bold)
        # 遍历所有子控件找到标题标签
        for child in self.findChildren(QLabel):
            if child.text() == "英语精听复读软件":
                child.setFont(title_font)
                break
        
        # 更新资源提示字体
        for child in self.findChildren(QLabel):
            if "需要素材" in child.text():
                child.setStyleSheet(f"color: #888; font-size: {max(10, self.font_size - 6)}px; padding: 5px;")
                break
        
        # 更新播放列表标题字体
        for child in self.findChildren(QLabel):
            if child.text() == "播放列表":
                child.setStyleSheet(f"color: white; font-size: {max(14, self.font_size)}px; padding: 10px;")
                break
        
        # 更新播放列表项字体
        self.playlist_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
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
        self.font_settings_btn.setStyleSheet(self.get_button_style())
    
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

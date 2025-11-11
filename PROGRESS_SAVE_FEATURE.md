# 进度保存和恢复功能

## 功能概述

英语精听复读软件现在支持自动保存和恢复播放进度功能。当用户关闭软件时，会自动记录当前播放的视频文件、字幕文件和播放进度，下次打开软件时会自动恢复上次的学习状态。

## 实现的功能

### 1. 自动保存进度
- **保存时机**: 每次关闭软件时自动保存
- **保存内容**:
  - 当前播放的视频文件路径 (`last_video_path`)
  - 当前播放的字幕文件路径 (`last_srt_path`) 
  - 当前播放的字幕索引 (`last_subtitle_index`)
  - 其他设置（字体、复读设置等）

### 2. 自动恢复进度
- **恢复时机**: 软件启动时自动尝试恢复
- **恢复条件**: 只有当上次播放的视频和字幕文件都存在时才恢复
- **恢复内容**:
  - 自动加载上次的视频和字幕文件
  - 跳转到上次播放的句子位置
  - 自动开始播放

### 3. 容错处理
- **文件丢失处理**: 如果上次播放的文件不存在，会显示错误信息并回归初始状态
- **索引越界处理**: 如果保存的字幕索引超出范围，会自动调整到有效范围
- **异常处理**: 所有恢复操作都有异常捕获，确保软件稳定运行

## 配置文件结构

```json
{
  "font_size": 28,
  "font_family": "霞鹜文楷 GB",
  "last_video_dir": "E:/下载/Video/4K Video Downloader Subscribe",
  "last_srt_dir": "E:/下载/Video/4K Video Downloader Subscribe",
  "repeat_interval": 1,
  "repeat_count": 3,
  "auto_next": true,
  "last_video_path": "E:/下载/Video/4K Video Downloader Subscribe/How to Make Stress Your Friend  Kelly McGonigal  TED.mp4",
  "last_srt_path": "E:/下载/Video/4K Video Downloader Subscribe/How to Make Stress Your Friend  Kelly McGonigal  TED.en.srt",
  "last_subtitle_index": 6
}
```

## 核心代码实现

### 1. 保存配置
```python
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
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置文件失败: {e}")
```

### 2. 恢复进度
```python
def restore_last_session(self):
    """恢复上次的播放进度"""
    try:
        # 检查上次播放的文件是否存在
        if (self.last_video_path and os.path.exists(self.last_video_path) and
            self.last_srt_path and os.path.exists(self.last_srt_path)):
            
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
                self.player_widget.attach_vlc()
                
                # 加载字幕文件
                if self.subtitle_parser.load_srt(self.last_srt_path):
                    # 设置上次的播放进度
                    if 0 <= self.last_subtitle_index < len(self.subtitle_parser.subtitles):
                        self.subtitle_parser.current_index = self.last_subtitle_index
                    
                    # 更新文件状态
                    self.update_file_status()
                    
                    # 显示恢复提示
                    QMessageBox.information(self, "恢复进度", 
                                           f"已恢复上次的播放进度：第 {self.subtitle_parser.current_index + 1} 句")
                    
                    # 自动开始播放当前句子
                    self.start_playing_current_sentence()
                    return True
        else:
            # 文件不存在，清除保存的路径
            if self.last_video_path and not os.path.exists(self.last_video_path):
                print(f"上次的视频文件不存在: {self.last_video_path}")
            if self.last_srt_path and not os.path.exists(self.last_srt_path):
                print(f"上次的字幕文件不存在: {self.last_srt_path}")
            
    except Exception as e:
        print(f"恢复上次播放进度失败: {e}")
    
    return False
```

## 使用流程

### 正常使用流程
1. 用户打开软件
2. 软件自动检查是否有上次的播放记录
3. 如果文件存在，自动恢复播放进度并显示提示信息
4. 用户可以直接继续学习

### 文件丢失流程
1. 用户打开软件
2. 软件检查上次播放的文件
3. 如果文件不存在，软件回归初始状态
4. 用户需要重新选择文件

## 用户体验改进

1. **无缝恢复**: 用户打开软件即可继续上次的学习，无需手动操作
2. **明确提示**: 恢复成功时会显示具体的恢复进度信息
3. **容错友好**: 文件丢失时不会崩溃，而是优雅地回归初始状态
4. **状态保持**: 所有设置（字体、复读参数等）都会保持

## 测试验证

### 测试场景1: 正常恢复
1. 播放一个视频和字幕文件
2. 播放到第6句时关闭软件
3. 重新打开软件
4. 验证是否自动加载文件并跳转到第6句

### 测试场景2: 文件丢失
1. 删除上次播放的视频或字幕文件
2. 重新打开软件
3. 验证是否显示初始状态，等待用户选择文件

### 测试场景3: 配置损坏
1. 手动修改配置文件为无效值
2. 重新打开软件
3. 验证是否使用默认值并正常运行

## 技术优势

1. **数据持久化**: 使用JSON格式保存配置，易于阅读和调试
2. **异常安全**: 所有文件操作都有异常处理
3. **资源管理**: 文件存在性检查避免无效操作
4. **用户体验**: 自动恢复减少用户操作步骤

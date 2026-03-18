---
name: libtv-advanced
description: LibTV (LibLib.tv) 高级视频工作流技能，支持一键完成 AI 视频生成、自动下载、智能剪辑（含转场、字幕、BGM）。Use when the user wants to create AI videos or short films using LibTV, especially when they need automatic video editing with transitions, subtitles, or background music.
---

# LibTV 高级视频工作流

完整的 AI 视频制作流水线：生成素材 → 自动下载 → 智能剪辑成片。

## 前置要求

```bash
# 安装 moviepy
pip3 install moviepy

# 安装 FFmpeg（Mac）
brew install ffmpeg

# 或下载: https://ffmpeg.org/download.html
```

## 环境变量

```bash
export LIBTV_ACCESS_KEY="your-access-key"
```

## 快速开始

### 1. 一键完整工作流

生成 + 下载 + 剪辑一条龙：

```bash
python3 scripts/libtv_workflow.py "生成一个可口可乐1分钟宣传片"
```

带配置文件（字幕、BGM、转场）：

```bash
python3 scripts/libtv_workflow.py "生成古风武侠短片" --config scripts/config_example.json
```

### 2. 单独剪辑（已有素材）

```bash
python3 scripts/libtv_workflow.py "--" --skip-generate --video-dir ./my_videos --config my_config.json
```

### 3. 高级剪辑（精细控制）

```bash
python3 scripts/video_editor.py scene1.mp4 scene2.mp4 scene3.mp4 \
  --transition fade \
  --bgm ./music.mp3 \
  --bgm-volume 0.3 \
  --style cinematic \
  -o final.mp4
```

## Scripts

### scripts/libtv_workflow.py
完整工作流脚本，串联全部步骤。

```bash
# 基础用法
python3 scripts/libtv_workflow.py "生成短剧视频"

# 完整参数
python3 scripts/libtv_workflow.py "生成短剧" \
  --config config.json \
  --wait-timeout 600 \
  --output my_video.mp4
```

### scripts/video_editor.py
专业视频剪辑工具。

```bash
python3 scripts/video_editor.py video1.mp4 video2.mp4 \
  --transition fade \
  --transition-duration 1.5 \
  --bgm music.mp3 \
  --bgm-volume 0.25 \
  --style cinematic \
  -o output.mp4
```

### scripts/config_example.json
配置文件模板：

```json
{
  "transition": "fade",
  "transition_duration": 1.5,
  "style": "cinematic",
  "bgm": "./assets/music.mp3",
  "bgm_volume": 0.25,
  "subtitles": [
    {
      "text": "第一章",
      "start": 0,
      "duration": 3,
      "position": "center",
      "fontsize": 80,
      "color": "white"
    }
  ]
}
```

## 功能特性

| 功能 | 说明 |
|------|------|
| 🎨 AI 生成 | 调用 LibTV 生成图片和视频素材 |
| 📥 自动下载 | 批量下载生成的所有素材 |
| ✨ 转场效果 | fade(淡入淡出)、slide(滑动) |
| 📝 字幕支持 | 自定义位置、大小、颜色、描边 |
| 🎵 背景音乐 | 自动循环、音量调节、淡入淡出 |
| 🎨 调色风格 | normal、warm、cool、cinematic |

## 典型工作流

```
用户: "帮我做一个古风武侠短片"

Agent:
  1. python3 libtv_workflow.py "生成古风武侠短片素材"
     → 生成分镜图和视频片段
  
  2. 等待生成完成
  
  3. 自动下载所有素材
  
  4. 调用 video_editor 拼接
     → 加转场、加字幕、加 BGM
  
  5. 返回: final_video.mp4
```

## 提示词技巧

生成短剧时，建议这样描述：

```
"生成一个1分钟古风武侠短片，包含：
- 主角出场（3个分镜）
- 打斗场景（4个分镜）
- 结尾定格（1个分镜）
要求画面连贯，风格统一"
```

## 注意事项

1. **生成需要时间**：短剧可能需要 5-10 分钟，耐心等待
2. **剪辑需要 FFmpeg**：确保已安装
3. **字幕需要字体**：默认使用系统字体，可自定义
4. **BGM 版权**：使用自己的音乐文件，注意版权

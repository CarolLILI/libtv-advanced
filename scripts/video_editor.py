#!/usr/bin/env python3
"""
LibTV 高级视频剪辑脚本
支持：转场效果、背景音乐、字幕、调色
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, 
        concatenate_videoclips, TextClip, ColorClip
    )
    from moviepy.video.fx.all import fadein, fadeout
except ImportError:
    print("❌ 请先安装 moviepy: pip3 install moviepy")
    sys.exit(1)


class VideoEditor:
    """视频编辑器"""
    
    def __init__(self, output_dir="./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.clips = []
    
    def load_clips(self, video_files):
        """加载视频片段"""
        print(f"📂 加载 {len(video_files)} 个视频片段...")
        for i, filepath in enumerate(video_files, 1):
            if not os.path.exists(filepath):
                print(f"⚠️  跳过不存在的文件: {filepath}")
                continue
            clip = VideoFileClip(filepath)
            self.clips.append(clip)
            print(f"  [{i}] {os.path.basename(filepath)} - {clip.duration:.1f}s")
        return self
    
    def add_transitions(self, transition_type="fade", duration=1.0):
        """
        添加转场效果
        
        Args:
            transition_type: fade(淡入淡出), slide(滑动), none(无)
            duration: 转场持续时间（秒）
        """
        if transition_type == "none" or len(self.clips) < 2:
            return self
        
        print(f"✨ 添加 {transition_type} 转场效果...")
        
        processed = []
        for i, clip in enumerate(self.clips):
            if transition_type == "fade":
                # 淡入淡出
                clip = fadein(clip, duration).fadeout(duration)
            processed.append(clip)
        
        self.clips = processed
        return self
    
    def add_subtitles(self, subtitles_config):
        """
        添加字幕
        
        Args:
            subtitles_config: 字幕配置列表
            [
                {"text": "第一幕", "start": 0, "duration": 3, "position": "center"},
                {"text": "第二幕", "start": 5, "duration": 3, "position": "bottom"}
            ]
        """
        if not subtitles_config:
            return self
        
        print(f"📝 添加 {len(subtitles_config)} 条字幕...")
        
        # 先合并视频
        main_clip = concatenate_videoclips(self.clips, method="compose")
        
        # 创建字幕层
        subtitle_clips = []
        for sub in subtitles_config:
            text_clip = (TextClip(
                sub["text"],
                fontsize=sub.get("fontsize", 60),
                color=sub.get("color", "white"),
                stroke_color=sub.get("stroke_color", "black"),
                stroke_width=sub.get("stroke_width", 2),
                font=sub.get("font", "Arial-Bold")
            )
            .set_start(sub["start"])
            .set_duration(sub["duration"])
            .set_position(sub.get("position", "center")))
            
            subtitle_clips.append(text_clip)
        
        # 合并视频和字幕
        final = CompositeVideoClip([main_clip] + subtitle_clips)
        self.clips = [final]
        return self
    
    def add_background_music(self, music_path, volume=0.3, fade_duration=2):
        """
        添加背景音乐
        
        Args:
            music_path: 音乐文件路径
            volume: 音量（0-1）
            fade_duration: 淡入淡出时间（秒）
        """
        if not os.path.exists(music_path):
            print(f"⚠️  音乐文件不存在: {music_path}")
            return self
        
        print(f"🎵 添加背景音乐: {os.path.basename(music_path)}")
        
        # 获取主视频时长
        if not self.clips:
            return self
        
        main_clip = concatenate_videoclips(self.clips) if len(self.clips) > 1 else self.clips[0]
        video_duration = main_clip.duration
        
        # 加载并裁剪音乐
        audio = AudioFileClip(music_path)
        
        # 如果音乐比视频长，裁剪；如果短，循环
        if audio.duration > video_duration:
            audio = audio.subclip(0, video_duration)
        else:
            # 循环播放
            loops = int(video_duration / audio.duration) + 1
            audio = audio.fx(lambda c: c.loop(n=loops)).subclip(0, video_duration)
        
        # 调整音量并添加淡入淡出
        audio = (audio
                 .volumex(volume)
                 .audio_fadein(fade_duration)
                 .audio_fadeout(fade_duration))
        
        # 合并
        final = main_clip.set_audio(audio)
        self.clips = [final]
        return self
    
    def add_color_grading(self, style="normal"):
        """
        调色
        
        Args:
            style: normal(原色), warm(暖色), cool(冷色), cinematic(电影感)
        """
        if style == "normal":
            return self
        
        print(f"🎨 应用 {style} 调色风格...")
        
        processed = []
        for clip in self.clips:
            if style == "warm":
                clip = clip.fx(lambda c: c.colorx(1.1).fadein(0))  # 增加饱和度
            elif style == "cool":
                clip = clip.fx(lambda c: c.fadeout(0))  # 可以扩展更多效果
            elif style == "cinematic":
                # 电影感：轻微降低饱和度，增加对比度
                clip = clip.fx(lambda c: c.colorx(0.9))
            processed.append(clip)
        
        self.clips = processed
        return self
    
    def export(self, output_filename="final_video.mp4", fps=24, codec="libx264"):
        """
        导出最终视频
        
        Args:
            output_filename: 输出文件名
            fps: 帧率
            codec: 视频编码器
        """
        if not self.clips:
            raise ValueError("没有可导出的视频片段")
        
        output_path = self.output_dir / output_filename
        print(f"\n🎬 导出视频: {output_path}")
        print(f"   编码: {codec}, FPS: {fps}")
        
        # 如果只有一个片段，直接导出；多个则拼接
        if len(self.clips) == 1:
            final = self.clips[0]
        else:
            final = concatenate_videoclips(self.clips, method="compose")
        
        final.write_videofile(
            str(output_path),
            fps=fps,
            codec=codec,
            audio_codec="aac",
            threads=4,
            logger=None  # 关闭详细日志
        )
        
        # 清理资源
        for clip in self.clips:
            clip.close()
        
        print(f"✅ 导出完成: {output_path}")
        return str(output_path)


def load_config(config_path):
    """从 JSON 文件加载配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="LibTV 高级视频剪辑工具")
    parser.add_argument("videos", nargs="+", help="输入视频文件列表")
    parser.add_argument("--config", "-c", help="配置文件路径 (JSON)")
    parser.add_argument("--output", "-o", default="final_video.mp4", help="输出文件名")
    parser.add_argument("--output-dir", "-d", default="./output", help="输出目录")
    parser.add_argument("--transition", choices=["fade", "slide", "none"], default="fade",
                        help="转场效果")
    parser.add_argument("--transition-duration", type=float, default=1.0, help="转场持续时间")
    parser.add_argument("--bgm", help="背景音乐文件路径")
    parser.add_argument("--bgm-volume", type=float, default=0.3, help="背景音乐音量 (0-1)")
    parser.add_argument("--style", choices=["normal", "warm", "cool", "cinematic"],
                        default="normal", help="调色风格")
    parser.add_argument("--fps", type=int, default=24, help="输出帧率")
    
    args = parser.parse_args()
    
    # 初始化编辑器
    editor = VideoEditor(output_dir=args.output_dir)
    
    # 加载配置或命令行参数
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # 加载视频
    editor.load_clips(args.videos)
    
    if not editor.clips:
        print("❌ 没有可处理的视频片段")
        sys.exit(1)
    
    # 添加转场
    transition = config.get("transition", args.transition)
    trans_duration = config.get("transition_duration", args.transition_duration)
    editor.add_transitions(transition, trans_duration)
    
    # 添加字幕
    subtitles = config.get("subtitles")
    if subtitles:
        editor.add_subtitles(subtitles)
    
    # 添加背景音乐
    bgm = config.get("bgm", args.bgm)
    bgm_volume = config.get("bgm_volume", args.bgm_volume)
    if bgm:
        editor.add_background_music(bgm, bgm_volume)
    
    # 调色
    style = config.get("style", args.style)
    editor.add_color_grading(style)
    
    # 导出
    output = editor.export(args.output, fps=args.fps)
    
    # 输出 JSON 结果
    result = {
        "output_file": output,
        "duration": sum(c.duration for c in editor.clips),
        "clips_count": len(editor.clips)
    }
    print("\n" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

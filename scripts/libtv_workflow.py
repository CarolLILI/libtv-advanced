#!/usr/bin/env python3
"""
LibTV 完整工作流：生成 → 下载 → 剪辑
一键完成从生图到成片的全部流程
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class LibTVWorkflow:
    """LibTV 完整工作流"""
    
    def __init__(self, access_key=None):
        self.access_key = access_key or os.environ.get("LIBTV_ACCESS_KEY")
        if not self.access_key:
            raise ValueError("请设置 LIBTV_ACCESS_KEY")
        
        self.session_id = None
        self.project_uuid = None
        self.downloaded_files = []
    
    def generate(self, prompt, session_id=None):
        """生成视频素材"""
        from libtv_client import LibTVClient
        
        client = LibTVClient(self.access_key)
        print(f"🎨 发送生成请求: {prompt}")
        
        result = client.create_session(prompt, session_id)
        self.session_id = result.get("sessionId")
        self.project_uuid = result.get("projectUuid")
        
        print(f"✅ 任务已提交")
        print(f"   会话 ID: {self.session_id}")
        print(f"   项目链接: https://www.liblib.tv/canvas?projectId={self.project_uuid}")
        
        return self.session_id
    
    def wait_for_completion(self, timeout=300, poll_interval=10):
        """等待生成完成"""
        from libtv_client import LibTVClient
        
        client = LibTVClient(self.access_key)
        print(f"\n⏳ 等待生成完成（最多 {timeout} 秒）...")
        
        start_time = time.time()
        last_seq = 0
        
        while time.time() - start_time < timeout:
            result = client.query_session(self.session_id, last_seq)
            messages = result.get("messages", [])
            
            if messages:
                last_seq = max(m.get("seq", 0) for m in messages)
                print(f"   收到 {len(messages)} 条新消息")
                
                # 检查是否包含完成标记或结果
                for msg in messages:
                    content = msg.get("content", "")
                    if "完成" in content or "生成" in content:
                        print(f"   🤖 {content[:100]}...")
            
            # 简单等待，实际可以检查特定完成标记
            time.sleep(poll_interval)
            
            # 检查是否已经运行了一段时间，假设完成了
            if time.time() - start_time > 60:  # 至少等60秒
                print("   假设生成完成，继续下载...")
                break
        
        return True
    
    def download(self, output_dir="./libtv_downloads"):
        """下载生成的素材"""
        from libtv_client import LibTVClient
        import re
        from urllib import request
        
        client = LibTVClient(self.access_key)
        print(f"\n📥 下载素材到: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        result = client.query_session(self.session_id)
        messages = result.get("messages", [])
        
        # 提取所有媒体 URL
        urls = []
        for msg in messages:
            content = msg.get("content", "")
            found = re.findall(r'https?://[^\s<>"\']+\.(?:png|jpg|jpeg|gif|mp4|mov)', content, re.IGNORECASE)
            urls.extend(found)
        
        # 分类
        images = [u for u in urls if any(ext in u.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif'])]
        videos = [u for u in urls if any(ext in u.lower() for ext in ['.mp4', '.mov'])]
        
        print(f"   发现 {len(images)} 张图片, {len(videos)} 个视频")
        
        # 下载
        downloaded = []
        for i, url in enumerate(urls, 1):
            ext = os.path.splitext(url.split('?')[0])[1] or '.mp4'
            filename = f"{i:02d}{ext}"
            filepath = os.path.join(output_dir, filename)
            
            print(f"   [{i}/{len(urls)}] 下载: {filename}")
            req = request.Request(url, headers={"User-Agent": "LibTV-Client/1.0"})
            with request.urlopen(req) as resp:
                with open(filepath, 'wb') as f:
                    f.write(resp.read())
            downloaded.append(filepath)
        
        self.downloaded_files = downloaded
        print(f"✅ 下载完成: {len(downloaded)} 个文件")
        
        return {
            "images": [f for f in downloaded if any(ext in f.lower() for ext in ['.png', '.jpg', '.jpeg'])],
            "videos": [f for f in downloaded if any(ext in f.lower() for ext in ['.mp4', '.mov'])],
            "output_dir": output_dir
        }
    
    def edit(self, video_files, config=None, output_file="final_video.mp4"):
        """剪辑视频"""
        from video_editor import VideoEditor
        
        print(f"\n🎬 开始剪辑...")
        
        editor = VideoEditor(output_dir="./output")
        editor.load_clips(video_files)
        
        if not editor.clips:
            print("⚠️ 没有可剪辑的视频")
            return None
        
        # 应用配置
        if config:
            if config.get("transition"):
                editor.add_transitions(config["transition"], config.get("transition_duration", 1.0))
            if config.get("subtitles"):
                editor.add_subtitles(config["subtitles"])
            if config.get("bgm"):
                editor.add_background_music(config["bgm"], config.get("bgm_volume", 0.3))
            if config.get("style"):
                editor.add_color_grading(config["style"])
        
        result = editor.export(output_file)
        return result
    
    def run(self, prompt, config=None, wait_timeout=300):
        """运行完整工作流"""
        print("=" * 50)
        print("🚀 LibTV 完整工作流")
        print("=" * 50)
        
        # 1. 生成
        self.generate(prompt)
        
        # 2. 等待
        self.wait_for_completion(wait_timeout)
        
        # 3. 下载
        downloaded = self.download()
        
        # 4. 剪辑（如果有视频）
        final_video = None
        if downloaded["videos"]:
            final_video = self.edit(downloaded["videos"], config)
        
        # 返回结果
        return {
            "session_id": self.session_id,
            "project_url": f"https://www.liblib.tv/canvas?projectId={self.project_uuid}",
            "downloaded": downloaded,
            "final_video": final_video
        }


def main():
    parser = argparse.ArgumentParser(description="LibTV 完整工作流")
    parser.add_argument("prompt", help="生成提示词，如 '生成一个可口可乐宣传片'")
    parser.add_argument("--config", "-c", help="剪辑配置文件 (JSON)")
    parser.add_argument("--session-id", help="复用已有会话")
    parser.add_argument("--wait-timeout", type=int, default=300, help="等待生成的超时时间(秒)")
    parser.add_argument("--output", "-o", default="final_video.mp4", help="最终输出文件名")
    parser.add_argument("--skip-generate", action="store_true", help="跳过生成，只剪辑已有素材")
    parser.add_argument("--video-dir", help="已有视频素材目录（与 --skip-generate 配合使用）")
    
    args = parser.parse_args()
    
    # 加载配置
    config = None
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    workflow = LibTVWorkflow()
    
    if args.skip_generate and args.video_dir:
        # 只剪辑模式
        video_files = [os.path.join(args.video_dir, f) for f in os.listdir(args.video_dir)
                       if f.endswith(('.mp4', '.mov'))]
        result = workflow.edit(sorted(video_files), config, args.output)
        print(f"\n✅ 剪辑完成: {result}")
    else:
        # 完整工作流
        result = workflow.run(args.prompt, config, args.wait_timeout)
        
        print("\n" + "=" * 50)
        print("🎉 工作流完成!")
        print("=" * 50)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

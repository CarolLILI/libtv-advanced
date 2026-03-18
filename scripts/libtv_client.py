#!/usr/bin/env python3
"""
LibTV HTTP 客户端（复用官方版本，稍作调整）
"""

import os
import json
from urllib import request, error


class LibTVClient:
    """LibTV API 客户端"""
    
    API_BASE = os.environ.get("LIBTV_API_BASE", "https://im.liblib.tv")
    TIMEOUT = 60
    
    def __init__(self, access_key=None):
        self.access_key = access_key or os.environ.get("LIBTV_ACCESS_KEY")
        if not self.access_key:
            raise ValueError("请设置 LIBTV_ACCESS_KEY")
    
    def make_request(self, method, path, data=None):
        url = f"{self.API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {self.access_key}",
            "Content-Type": "application/json",
        }
        
        body = json.dumps(data).encode('utf-8') if data else None
        req = request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with request.urlopen(req, timeout=self.TIMEOUT) as response:
                return json.loads(response.read().decode('utf-8'))
        except error.HTTPError as e:
            raise Exception(f"API 错误: {e.read().decode()}")
    
    def create_session(self, message=None, session_id=None):
        data = {}
        if message:
            data["message"] = message
        if session_id:
            data["sessionId"] = session_id
        
        result = self.make_request("POST", "/openapi/session", data)
        return result.get("data", {})
    
    def query_session(self, session_id, after_seq=None):
        from urllib import parse
        params = f"?afterSeq={after_seq}" if after_seq else ""
        result = self.make_request("GET", f"/openapi/session/{session_id}{params}")
        return result.get("data", {})

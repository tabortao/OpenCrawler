"""
测试 MCP Server stdio 模式
"""

import subprocess
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_stdio_mode():
    """测试 stdio 模式"""
    print("=== 测试 MCP Server stdio 模式 ===\n")
    
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        },
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
    ]
    
    input_data = "\n".join([json.dumps(r) for r in requests])
    
    print(f"发送请求:\n{input_data[:200]}...\n")
    
    proc = subprocess.Popen(
        ["micromamba", "run", "-p", "./venv", "python", "mcp_server.py", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    
    try:
        stdout, stderr = proc.communicate(input=input_data, timeout=30)
        
        print("=== 标准输出 ===")
        for line in stdout.strip().split("\n"):
            if line.strip():
                try:
                    data = json.loads(line)
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                except json.JSONDecodeError:
                    print(line[:500])
        
        print("\n=== 标准错误 ===")
        print(stderr[:500] if stderr else "(无)")
        
        return True
    except subprocess.TimeoutExpired:
        proc.kill()
        print("超时!")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False


if __name__ == "__main__":
    success = test_stdio_mode()
    sys.exit(0 if success else 1)

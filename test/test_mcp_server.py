"""
MCP Server 测试脚本

测试 MCP 服务器的核心功能。
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp.server import MCPServer
from app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCMessageParser,
)
from app.mcp_tools import (
    register_opencrawler_tools,
    register_opencrawler_resources,
    register_opencrawler_prompts,
)


def create_test_server() -> MCPServer:
    """创建测试服务器"""
    server = MCPServer(
        name="TestServer",
        version="1.0.0",
    )
    
    server.enable_tools()
    server.enable_resources()
    server.enable_prompts()
    
    register_opencrawler_tools(server.tools)
    register_opencrawler_resources(server.resources)
    register_opencrawler_prompts(server.prompts)
    
    return server


async def test_initialize():
    """测试初始化流程"""
    print("\n=== 测试初始化 ===")
    
    server = create_test_server()
    
    request = JSONRPCRequest(
        id=1,
        method="initialize",
        params={
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "TestClient",
                "version": "1.0.0",
            },
        },
    )
    
    response = await server._handle_initialize(request)
    
    print(f"请求: {request.to_dict()}")
    print(f"响应: {response.to_dict()}")
    
    assert response.error is None, f"初始化失败: {response.error}"
    assert response.result["protocolVersion"] == "2025-03-26"
    assert "capabilities" in response.result
    assert "serverInfo" in response.result
    
    print("✅ 初始化测试通过")
    return server


async def test_ping(server: MCPServer):
    """测试 ping"""
    print("\n=== 测试 Ping ===")
    
    request = JSONRPCRequest(id=2, method="ping", params={})
    response = await server._handle_ping(request)
    
    print(f"请求: {request.to_dict()}")
    print(f"响应: {response.to_dict()}")
    
    assert response.error is None
    assert response.result == {}
    
    print("✅ Ping 测试通过")


async def test_tools_list(server: MCPServer):
    """测试工具列表"""
    print("\n=== 测试工具列表 ===")
    
    request = JSONRPCRequest(id=3, method="tools/list", params={})
    response = await server._handle_tools_list(request)
    
    print(f"响应: {json.dumps(response.to_dict(), indent=2, ensure_ascii=False)}")
    
    assert response.error is None
    assert "tools" in response.result
    assert len(response.result["tools"]) >= 5
    
    for tool in response.result["tools"]:
        print(f"  - {tool['name']}: {tool['description'][:50]}...")
    
    print("✅ 工具列表测试通过")


async def test_tools_call_list_platforms(server: MCPServer):
    """测试调用 list_platforms 工具"""
    print("\n=== 测试调用 list_platforms 工具 ===")
    
    request = JSONRPCRequest(
        id=4,
        method="tools/call",
        params={
            "name": "list_platforms",
            "arguments": {},
        },
    )
    
    response = await server._handle_tools_call(request)
    
    print(f"响应: {json.dumps(response.to_dict(), indent=2, ensure_ascii=False)[:500]}...")
    
    assert response.error is None
    assert "content" in response.result
    assert response.result["isError"] is False
    
    print("✅ list_platforms 工具测试通过")


async def test_resources_list(server: MCPServer):
    """测试资源列表"""
    print("\n=== 测试资源列表 ===")
    
    request = JSONRPCRequest(id=5, method="resources/list", params={})
    response = await server._handle_resources_list(request)
    
    print(f"响应: {json.dumps(response.to_dict(), indent=2, ensure_ascii=False)}")
    
    assert response.error is None
    assert "resources" in response.result
    
    for resource in response.result["resources"]:
        print(f"  - {resource['uri']}: {resource['name']}")
    
    print("✅ 资源列表测试通过")


async def test_resources_read(server: MCPServer):
    """测试读取资源"""
    print("\n=== 测试读取资源 ===")
    
    request = JSONRPCRequest(
        id=6,
        method="resources/read",
        params={
            "uri": "opencrawler://platforms",
        },
    )
    
    response = await server._handle_resources_read(request)
    
    print(f"响应: {json.dumps(response.to_dict(), indent=2, ensure_ascii=False)[:500]}...")
    
    assert response.error is None
    assert "contents" in response.result
    
    print("✅ 读取资源测试通过")


async def test_prompts_list(server: MCPServer):
    """测试提示列表"""
    print("\n=== 测试提示列表 ===")
    
    request = JSONRPCRequest(id=7, method="prompts/list", params={})
    response = await server._handle_prompts_list(request)
    
    print(f"响应: {json.dumps(response.to_dict(), indent=2, ensure_ascii=False)}")
    
    assert response.error is None
    assert "prompts" in response.result
    
    for prompt in response.result["prompts"]:
        print(f"  - {prompt['name']}")
    
    print("✅ 提示列表测试通过")


async def test_prompts_get(server: MCPServer):
    """测试获取提示"""
    print("\n=== 测试获取提示 ===")
    
    request = JSONRPCRequest(
        id=8,
        method="prompts/get",
        params={
            "name": "crawl_article",
            "arguments": {
                "url": "https://example.com/test",
            },
        },
    )
    
    response = await server._handle_prompts_get(request)
    
    print(f"响应: {json.dumps(response.to_dict(), indent=2, ensure_ascii=False)[:500]}...")
    
    assert response.error is None
    assert "messages" in response.result
    
    print("✅ 获取提示测试通过")


async def test_error_handling(server: MCPServer):
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    request = JSONRPCRequest(
        id=9,
        method="tools/call",
        params={
            "name": "unknown_tool",
            "arguments": {},
        },
    )
    
    response = await server._handle_tools_call(request)
    
    print(f"响应: {json.dumps(response.to_dict(), indent=2, ensure_ascii=False)}")
    
    assert response.result["isError"] is True
    
    print("✅ 错误处理测试通过")


async def test_protocol_parser():
    """测试协议解析器"""
    print("\n=== 测试协议解析器 ===")
    
    request_json = '{"jsonrpc": "2.0", "id": 1, "method": "test", "params": {"key": "value"}}'
    request = JSONRPCMessageParser.parse(request_json)
    
    print(f"解析请求: {request.to_dict()}")
    assert request.id == 1
    assert request.method == "test"
    
    response_json = '{"jsonrpc": "2.0", "id": 1, "result": {"status": "ok"}}'
    response = JSONRPCMessageParser.parse(response_json)
    
    print(f"解析响应: {response.to_dict()}")
    assert response.result["status"] == "ok"
    
    notification_json = '{"jsonrpc": "2.0", "method": "notify", "params": {}}'
    notification = JSONRPCMessageParser.parse(notification_json)
    
    print(f"解析通知: {notification.to_dict()}")
    assert notification.method == "notify"
    
    print("✅ 协议解析器测试通过")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("OpenCrawler MCP Server 测试")
    print("=" * 60)
    
    try:
        await test_protocol_parser()
        
        server = await test_initialize()
        server._negotiator.set_initialized()
        
        await test_ping(server)
        await test_tools_list(server)
        await test_tools_call_list_platforms(server)
        await test_resources_list(server)
        await test_resources_read(server)
        await test_prompts_list(server)
        await test_prompts_get(server)
        await test_error_handling(server)
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

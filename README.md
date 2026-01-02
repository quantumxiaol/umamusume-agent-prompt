# Umamusume Agent Prompt

从角色名出发，通过 Web MCP 进行资料整理，并生成可用于角色扮演的 Prompt。

## 项目结构

```
umamusume-agent-prompt/
|-- umamusume_prompt/
|   |-- mcp/
|   |   |-- server.py           # Web MCP 服务（搜索 + 抓取工具）
|   |-- prompts/
|   |   |-- collect_web.md      # 阶段一：资料收集
|   |   |-- build_prompt.md     # 阶段二：Prompt 生成
|   |-- web/
|   |   |-- search.py           # Google 搜索封装
|   |   |-- crawler.py          # Crawl4AI 抓取封装
|   |-- characters.py           # 角色映射读取/解析
|   |-- pipeline.py             # 两阶段流程
|   |-- cli.py                  # CLI 入口
|   |-- config.py               # 环境变量配置
|-- tests/
|   |-- testongoogle.py         # Google 搜索测试
|   |-- test_mcp_tool.py        # MCP 工具调用测试
|   |-- test_stream_mcp.py      # Agent 调用 MCP 工具测试
|-- main.py                     # CLI 入口
|-- mcpserver.py                # MCP 入口
|-- umamusume_characters.json
|-- results/
```

## 环境

使用 uv 管理环境。

```bash
uv lock
uv sync
source .venv/bin/activate
playwright install

cat .env.example > .env
```

在 `.env` 中设置：
- `INFO_LLM_MODEL_API_KEY`
- `WRITER_LLM_MODEL_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID`
- `HTTP_PROXY` / `HTTPS_PROXY`（可选，如访问 google、萌娘百科需要代理时再设置；未设置则直接访问）

其中`INFO_LLM`负责工具调用，`WRITER_LLM`负责输出，这两个可以一样，但对于qwen来说，qwen-coder的工具调用更加稳定一点，qwen-long写作水平更好一点。

请在 [Google Cloud 凭证控制台](https://console.cloud.google.com/apis/credentials)中创建GOOGLE_API_KEY，并使用[可编程搜索引擎](https://programmablesearchengine.google.com/controlpanel/create)创建GOOGLE_CSE_ID。

## 运行

1) 启动 Web MCP 服务

```bash
python mcpserver.py --http -p 7777
```

2) 生成角色 Prompt

```bash
python main.py --mcp-url http://127.0.0.1:7777/mcp/ --character 爱慕织姬
```

输出会写入 `results/<角色名>/web_info.md` 和 `results/<角色名>/role_prompt.md`。

## 测试

运行测试前请先启动 MCP 服务：

```bash
python mcpserver.py --http -p 7777
```

```bash
python tests/test_google.py
python tests/test_mcp_tool.py -u http://127.0.0.1:7777/mcp/
python tests/test_stream_mcp.py -u http://127.0.0.1:7777/mcp/ -q "爱慕织姬"
```

使用 pytest 运行：

```bash
pytest -q
```
## 生成的示例

- [爱慕织姬](./examples/Admire_Vega.md)
- [里见光钻](./examples/Satono_Diamond.md)
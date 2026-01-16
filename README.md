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
|   |   |-- process.py          # MarkItDown/Docling 转换封装
|   |-- characters.py           # 角色映射读取/解析
|   |-- pipeline.py             # 两阶段流程
|   |-- cli.py                  # CLI 入口
|   |-- config.py               # 环境变量配置
|-- tests/
|   |-- test_google.py          # Google 搜索测试
|   |-- test_mcp_tool_crawler.py# MCP 抓取工具测试
|   |-- test_mcp_tool_crawler_moegirl.py # MCP 萌娘百科抓取测试
|   |-- test_mcp_tool_google.py # MCP 搜索工具测试
|   |-- test_stream_mcp.py      # Agent 调用 MCP 工具测试
|   |-- test_biligame_crawler.py# Bilibili Wiki 抓取测试
|   |-- test_moegirl_crawler.py # 萌娘百科抓取测试
|   |-- test_visual_capture_pdf.py      # 视觉抓取 PDF/PNG
|   |-- test_visual_crawler_bilibili.py # Bilibili 视觉抓取 + MarkItDown
|   |-- test_visual_parse_pdf.py        # PDF -> MarkItDown/Docling
|   |-- test_visual_parse_png.py        # PNG -> MarkItDown
|   |-- test_visual_docling_parse_png.py# PNG -> PDF -> Docling
|-- main.py                     # CLI 入口
|-- mcpserver.py                # MCP 入口
|-- download_models.py          # Docling 模型下载脚本
|-- umamusume_characters.json
|-- results/
|-- examples/
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
- `INFO_LLM_VISION_MODEL_NAME`（图片描述时使用的视觉模型，可选）
- `WRITER_LLM_MODEL_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID`
- `HTTP_PROXY` / `HTTPS_PROXY`（可选，如访问 google、萌娘百科需要代理时再设置；未设置则直接访问）

其中`INFO_LLM`负责工具调用，`WRITER_LLM`负责输出，这两个可以一样，但对于qwen来说，qwen-coder的工具调用更加稳定一点，qwen-long写作水平更好一点。

请在 [Google Cloud 凭证控制台](https://console.cloud.google.com/apis/credentials)中创建GOOGLE_API_KEY，并使用[可编程搜索引擎](https://programmablesearchengine.google.com/controlpanel/create)创建GOOGLE_CSE_ID。

## 爬虫流程（现行）

当前默认走“网页渲染 -> PDF -> MarkItDown”的视觉抓取流程，效果比纯 HTML 清洗更稳定：

1) Crawl4AI 以浏览器方式渲染页面，输出 PDF/PNG（可走代理）。
2) 使用 MarkItDown 将 PDF 转成 Markdown 文本。
3) MCP 工具 `crawl_biligame_wiki` / `crawl_moegirl_wiki` 返回这份 Markdown 作为抓取结果。

说明：
- 萌娘百科默认 `print_scale=0.65`，用于避免 PDF 被裁切。
- 萌娘百科对 headless 更敏感，默认走 headful；CI 可用 `xvfb-run` 或显式 `headless=true`。

## 探索经过（简述）

- 尝试过 HTML 清洗与结构化提取（去脚本、过滤噪声、分块等），但 Bwiki 页面噪声与动态结构导致效果不稳定。
- 引入 Pruning/LLM 抽取后仍有缺失与重复问题。
- 改为“截图成 PDF -> MarkItDown/Docling”后，PDF + MarkItDown 的正文提取更完整，作为当前主线路。

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
python tests/test_mcp_tool_crawler.py -u http://127.0.0.1:7777/mcp/
python tests/test_mcp_tool_crawler_moegirl.py -u http://127.0.0.1:7777/mcp/
python tests/test_stream_mcp.py -u http://127.0.0.1:7777/mcp/ -q "爱慕织姬"
```

使用 pytest 运行：

```bash
pytest -q
```
## 生成的示例

- [爱慕织姬](./examples/Admire_Vega.md)
- [米浴](./examples/Rice_Shower.md)
- [里见光钻](./examples/Satono_Diamond.md)
- [无声铃鹿](./examples/Silence_Suzuka.md)


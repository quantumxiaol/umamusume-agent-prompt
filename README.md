# Umamusume Agent Prompt

从角色名出发，通过 Web MCP 进行资料整理，并生成可用于角色扮演的 Prompt。

## 项目结构

```
umamusume-agent-prompt/
|-- umamusume_prompt/
|   |-- mcp/
|   |   |-- server.py           # Web MCP 服务（集成 umamusume-web-crawler）
|   |-- prompts/
|   |   |-- collect_web.md      # 阶段一：资料收集
|   |   |-- build_prompt.md     # 阶段二：Prompt 生成
|   |-- characters.py           # 角色映射读取/解析
|   |-- pipeline.py             # 两阶段流程
|   |-- cli.py                  # CLI 入口
|   |-- config.py               # 环境变量配置
|-- tests/
|   |-- test_google.py          # Google 搜索测试 (通过库封装)
|   |-- test_crawler.py         # 通用爬取测试
|   |-- test_mcp_tool_crawler.py# MCP 抓取工具测试
|   |-- test_mcp_tool_crawler_moegirl.py # MCP 萌娘百科抓取测试
|   |-- test_mcp_tool_google.py # MCP 搜索工具测试
|   |-- test_stream_mcp.py      # Agent 调用 MCP 工具测试
|   |-- test_biligame_crawler.py# Bilibili Wiki API 抓取测试
|   |-- test_moegirl_crawler.py # 萌娘百科 API 抓取测试
|-- main.py                     # CLI 入口
|-- mcpserver.py                # MCP 入口
|-- download_models.py          # Docling 模型下载脚本 (如需使用 Docling)
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

cat .env.example > .env
```

在 `.env` 中设置：
- `INFO_LLM_MODEL_API_KEY`
- `WRITER_LLM_MODEL_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID`
- `HTTP_PROXY` / `HTTPS_PROXY`（可选，如访问 google、萌娘百科需要代理时再设置；未设置则直接访问）

其中`INFO_LLM`负责工具调用，`WRITER_LLM`负责输出。

请在 [Google Cloud 凭证控制台](https://console.cloud.google.com/apis/credentials)中创建GOOGLE_API_KEY，并使用[可编程搜索引擎](https://programmablesearchengine.google.com/controlpanel/create)创建GOOGLE_CSE_ID。

## 爬虫流程（现行）

核心能力已迁移至 `umamusume-web-crawler` 库。

当前默认走 **MediaWiki API** 抓取流程，相比视觉抓取更稳定、高效：

1) **站内搜索**：通过 API 搜索 Bilibili Wiki / 萌娘百科，获取准确的页面标题。
2) **API 拉取**：直接调用 MediaWiki API 拉取 Wikitext。
3) **解析与清洗**：
   - 自动展开 Transclusion 子页面。
   - 解析 InfoBox 和关键章节。
   - 转换为 LLM 友好的 Markdown 格式。

MCP 工具 `crawl_biligame_wiki` / `crawl_moegirl_wiki` 返回这份经过清洗的 Markdown。

对于非 Wiki 页面，提供 `crawl_page` 工具使用 headless browser (MarkItDown/Crawl4AI) 进行通用抓取。

## 探索经过（简述）

- 早期尝试 HTML 清洗，Bwiki 动态结构处理困难。
- 中期使用“视觉抓取（截图转PDF转Markdown）”，效果不错但开销大且依赖浏览器环境。
- 最终方案：集成 `umamusume-web-crawler`，使用 MediaWiki API 进行结构化数据获取，辅以视觉爬虫处理通用网页。

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
- [大和赤骥](./examples/Daiwa_Scarlet.md)
- [美浦波旁](./examples/Mihono_Bourbon.md)
- [米浴](./examples/Rice_Shower.md)
- [里见光钻](./examples/Satono_Diamond.md)
- [无声铃鹿](./examples/Silence_Suzuka.md)


# MyAgentDemo 项目文档

## 项目简介

基于 LLM 的 ReAct 框架智能体，支持工具调用和推理执行。

## 核心功能

- **LLM 智能体**：支持 OpenAI 兼容接口（DeepSeek、OpenAI、Anthropic 等）
- **工具调用**：天气查询、景点推荐、网络搜索、文件读写、终端命令
- **ReAct 推理**：Thought-Action-Observation 循环执行

## 项目结构

```
MyAgentDemo/
├── main.py                      # 控制台应用主入口
├── .env.example                 # 环境变量配置模板
└── AgentDemo/                   # 核心包
    ├── __init__.py              # 包导出
    ├── agent_system_prompt.py   # 系统提示词
    ├── Agent.py                 # 智能体类（React 框架）
    ├── LLMClient.py             # LLM 客户端工厂
    └── Tools.py                 # 可用工具集合
```

## 环境配置

复制 `.env.example` 为 `.env`，配置以下变量：

```bash
# LLM 配置
```
LLM_API_TYPE=openai
LLM_MODEL=deepseek-chat
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com

# 搜索配置
TAVILY_API_KEY=your_tavily_api_key
```

## 依赖安装

```bash
pip install python-dotenv openai anthropic tavily-python requests
```

## 运行项目

```bash
python main.py
```

## 可用工具

| 工具名 | 功能 |
|--------|------|
| `get_weather(city)` | 查询城市天气 |
| `get_attraction(city, weather)` | 搜索旅游景点 |
| `search_web(query)` | 网络搜索 |
| `readFile(file_path)` | 读取文件 |
| `writeFile(file_path, content)` | 写入文件 |
| `runTerminalCommand(command)` | 执行终端命令 |

## 架构要点

### Agent 执行流程

1. 用户输入 → 构建 Prompt（包含历史对话）
2. LLM 思考 → 输出 `Thought:` 和 `Action:`
3. 解析 Action → 调用对应工具
4. 工具执行 → 返回 `Observation:`
5. 循环直到 `Finish` 或达到最大迭代次数（5次）

### Action 格式

```
Action: function_name(arg1="value1", arg2="value2")
Action: Finish[最终答案]
```

## 扩展开发

### 添加新工具

在 `AgentDemo/Tools.py` 中添加函数，并在 `available_tools` 字典中注册。

### 集成新 LLM

在 `LLMClient.py` 的 `LLMClientFactory` 中添加新的客户端类型。

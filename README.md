# 投研证据链 · Lite

用两份公司年报复算财务指标，或就一个行业问题检索公开资料。结果以 Excel 返回，可从工作表回到年报原页或查看本次检索的网页片段。

## 年报复算

深南电路将封装基板单列为一项产品业务。下面四个金额从两年年报「收入与成本」的分产品表中录入，单位均为元。可对照 [原始 CSV](data/shennan_substrates.csv) 检查。

| 年度 | 封装基板营业收入 | 封装基板营业成本 | 披露原表 |
| --- | ---: | ---: | --- |
| 2024 | 3,171,061,556.18 | 2,595,586,474.14 | [2024 年报，第 17 页](https://static.cninfo.com.cn/finalpage/2025-03-13/1222778134.PDF#page=17) |
| 2025 | 4,147,788,891.37 | 3,211,018,578.93 | [2025 年报，第 16 页](https://static.cninfo.com.cn/finalpage/2026-03-13/1225006760.PDF#page=16) |

用本年收入除以上年收入再减一，得到 2025 年营收同比 **30.80%**。用当年收入减成本，再除以收入，得到毛利率 **22.58%**。两项结果按百分数保留两位小数，与 2025 年报同一行相符。Excel「财务指标」每行的 `source` 都链接到对应年份的原表。

## 运行

使用 Python 3.11。在仓库根目录打开 PowerShell，首次运行先创建独立环境。

```powershell
python -m venv ..\research-env
& '..\research-env\Scripts\python.exe' -m pip install -r requirements.txt
& '..\research-env\Scripts\python.exe' -B -m uvicorn src.app:app --host 127.0.0.1 --port 8000
```

打开 [本地接口页面](http://127.0.0.1:8000/docs)，选 `POST /research → Try it out`。要查看上面的年报案例，提交以下内容，点 `Execute` 下载工作簿。此模式在本机计算，无需 API 密钥。

```json
{"question":"复算深南电路封装基板业务的营收同比和毛利率","dataset":"shennan"}
```

**查网页**时需要有额度的 DeepSeek API Key。将 [.env.example](.env.example) 复制到仓库外，在副本中填写密钥。启动服务时在上述 uvicorn 命令末尾加 `--env-file '配置文件的实际路径'`。请求只需传问题。

```json
{"question":"先进封装的上游设备厂商和封测厂分别做什么？"}
```

模型生成搜索词，程序并发读取最多三个网页，取每页正文前 5,000 个字符供模型引用。在 Excel「来源证据」中可查看编号、网址、抓取时间和正文。程序标记除空白外完全相同的片段。判断转载、日期和原文能否支持某条结论，仍需查看原文。例如，[行业综述](https://m.askci.com/news/chanye/20260615/092517278148671712017055.shtml#1)和[转载页](https://wap.seccw.com/index.php/Index/detail/id/46253.html)的产业链段落来自同一篇文章。

网页回答需带有本次检索的来源编号。若缺少编号或引用了不存在的编号，工作簿只显示核对提示，并保留原文。编号正确时，仍需人工判断原文是否支持结论。

工作簿和取证记录保存在仓库旁的 `research-evidence-agent-lite-outputs/`。年报模式还会保存统一单位后的 CSV。可用环境变量 `RESEARCH_OUTPUT_DIR` 指定其他保存位置。

## 代码

| 文件 | 职责 |
| --- | --- |
| [src/app.py](src/app.py) | FastAPI 接收请求并返回 Excel |
| [src/agent.py](src/agent.py) | 运行年报或网页流程，用 openpyxl 和 Pandas 写出工作簿 |
| [src/clients.py](src/clients.py) | 用 HTTPX 调用 DeepSeek 的对话、搜索和网页读取接口 |
| [src/mcp_server.py](src/mcp_server.py) | 本地 MCP 工具，通过标准输入输出与主程序通信，用 Pandas 复算年报数据 |

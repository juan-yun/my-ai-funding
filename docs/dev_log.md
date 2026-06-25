## 2025/05/20
- 完成基于AKShare的美股历史价格获取工具类
- 完成基于AKShare的美股名称获取工具类
- 部分完成UT


## 2025/08/20
- 找回项目原型，记录下来 https://github.com/virattt/ai-hedge-fund
- 数据来源 https://financialdatasets.ai/  maochang1981@gmail.com 
- fin key : be878bc3-08bc-40af-8fb5-c860b85578fd
- 进展1： 获取AkShare数据，测试验证Apple, MS, Nvidia的2025/01月的所有交易价格数据，但volume偏差较大，原因未知

## 2025/08/27
- 重新根据API文档，整理EdgarApiUtils https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- 三方库使用 https://edgartools.readthedocs.io/en/latest/quickstart/


## 2025/09/18
- 成功计算出公司的PE
- Todo: P/B 暂未完成, 加油


## 2025/09/22
- 完成AAPL的PB, PS, PE等，但MSFT，NVDA不准确
- Market Cap计算仍然存在不同公司字段表述不一致的问题

## 2025/09/23 Morning
- Market Cap 计算测试4家公司完成
- free cash flow仍存问题，没有统计完成, 需要核对数据


## 2026/04/17 要做就做到极致，做到能真的指导交易
- 优先看非notes数据，能否拿到关键指标


## 2026/05/09
- 现在看来没有捷径可走，尽量从作者的virattt的代码仓库和他的博客中找到line_item与set.gov的FinancialStatmentNotesDataset的映射关系
  - https://github.com/virattt/ai-hedge-fund
  - https://virattt.github.io/ai-hedge-fund/

## 2026/05/10
行业领域    免费访问的股票代码 (Ticker)                         公司名称
科技与通信  AAPL、MSFT、AMZN、CRM、CSCO、INTC、IBM             苹果、微软、亚马逊、赛富时、思科、英特尔、IBM
金融与服务  V、AXP、GS、JPM、TRV                               维萨、美国运通、高盛、摩根大通、旅行者保险
消费与零售  WMT、HD、NKE、DIS、MCD、KO、PG                      沃尔玛、家得宝、耐克、迪士尼、麦当劳、可口可乐、宝洁
医疗与健康  UNH、JNJ、MRK、AMGN                                联合健康、强生、默沙东、安进
工业与能源 BA、CAT、HON、MMM、CVX                               波音、卡特彼勒、霍尼韦尔、3M、雪佛龙

## 2026/05/11
- 优先完成对financial metrics的关联计算，此处应该使用小的计算引擎
- 调整edgar tools facade的接口和内部实现逻辑，保持和financials.ai提供的一致
- 跑通全流程
- 完成backtest

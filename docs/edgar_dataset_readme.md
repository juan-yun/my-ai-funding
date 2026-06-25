## 统计数据来源
- [sec.gov数据资源](httpshttps://www.sec.gov/data-research/sec-data-resources)

## Edgar Dataset数据集的异同- *豆包自动生成内容*

| 对比项 | Statement Dataset（主报表数据集） | Dimension Dataset（维度数据集） |
| ---- | ---- | ---- |
| 中文含义 | 财务主表、汇总事实数据 | 维度切片、分类标签数据 |
| 对应 SEC 表 | NUM、PRE | DIM |
| 核心内容 | 具体数值、金额 value | 维度 axis、成员 member |
| 是否有数值 | 有数值 | 无数值，仅标签 |
| 数据粒度 | 合并总数、整体报表 | 产品/地区/分部等明细 |
| 关键字段 | adsh, tag, value, context | adsh, tag, context, axis, member |
| 维度有无 | 无维度（axis 为空） | 有明确维度 |
| 主要作用 | 标准三大财务报表 | 数据拆分、下钻、归类 |
| 示例 | 总收入 383B | 收入按 iPhone、Mac 拆分 |
| 单独可用性 | 可直接分析 | 必须关联数值表才能用 |
| 数据量 | 小、干净 | 大、明细多、组合复杂 |
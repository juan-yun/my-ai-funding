我直接按这张 SEC 官方目录，给你一个**可落地的、从0到1的使用路线图**，让你知道 **SUB/TAG/NUM/PRE/CAL 每一个文件怎么配合使用，如何串起来完成你财报解析的目标**。

---

## 一、先把这8个文件的角色说清楚
这是 SEC EDGAR 的标准XBRL文件集合，对应关系：

| 文件 | 简称 | 核心角色 | 一句话作用 |
|---|---|---|---|
| SUB | Submissions | 元数据 | 公司+财报基本信息（谁、什么时候、报了什么表） |
| TAG | Tags | 标签字典 | 所有XBRL科目定义（名字、类型、单位、描述） |
| DIM | Dimensions | 维度 | 多维度数据定义（如分部、地区、业务线） |
| NUM | Numbers | 数值库 | 财务报表里的所有数字+期间+单位 |
| TXT | Plain Text | 文本 | 非结构化文本披露（MD&A、附注） |
| REN | Rendering | 展示 | 报表格式、样式定义 |
| PRE | Presentation | 报表结构 | 报表的层级、行号、顺序（长什么样） |
| CAL | Calculations | 公式关系 | 科目间的加减计算规则 |

你做**结构化财务数据解析**，核心只用 5 个：`SUB + TAG + NUM + PRE + CAL`。

---

## 二、按「数据处理流程」分步骤讲怎么用

### 1. 第一步：SUB → 定位你要的公司+财报
`submission.tsv` 是所有数据的入口。

- 字段：`adsh`（唯一ID）、`cik`、`name`、`form`、`period`、`fiscalYear`
- 用法：
  1. 按公司/财年筛选出你要的财报 `adsh`
  2. 后续所有文件，都必须按 `adsh` 过滤，避免跨财报污染

**例子：**
```python
# 选英伟达 FY2026 10-K
target_adsh = sub[(sub['cik'] == '1045810') & (sub['fiscalYear'] == '2026')]['adsh'].iloc[0]
```

---

### 2. 第二步：NUM → 拉取所有原始数值
`num.tsv` 是财务数据的“事实表”。

- 字段：`adsh`、`tag`、`value`、`period`、`units`、`qtrs`
- 用法：
  1. 按 `adsh` + `period` + `units` 过滤出你要的期间/币种数据
  2. 所有 `value` 字段必须转为数值类型
  3. 原始数据里：**汇总科目（父项）通常没有值，只有明细科目（子项）有值**

**例子：**
```python
# 取出目标财报所有年度USD数值
num_target = num[(num['adsh'] == target_adsh) & (num['period'] == 'Y') & (num['units'] == 'USD')]
```

---

### 3. 第三步：CAL → 自动推导所有汇总科目（最关键）
`cal.tsv` 是 SEC 给你写好的「财报公式说明书」。

- 字段：`ptag`（父项）、`ctag`（子项）、`negative`（+/-）
- 核心逻辑：
  `ptag = Σ(ctag × weight)`，其中 `weight = -1 if negative else 1`
- 用法：
  1. 按 `adsh` 过滤，构建 `(adsh, ptag) → 子项列表` 的公式映射
  2. 对没有 `value` 的汇总科目，用子项数值按公式自动计算
  3. 解决你之前的问题：
     - `business_acquisitions_and_disposals` 这类合并净额，必须用 `cal` 算，不能直接取 `num`

**例子：**
```python
# 构建公式映射
cal_map = {}
for (adsh, ptag), group in cal.groupby(['adsh', 'ptag']):
    cal_map[(adsh, ptag)] = [
        {'ctag': r['ctag'], 'w': -1 if r['negative'] else 1}
        for _, r in group.iterrows()
    ]

# 计算某个ptag的值
def compute_ptag(adsh, ptag, num_df):
    if (adsh, ptag) not in cal_map:
        return num_df[num_df['tag'] == ptag]['value'].sum()
    total = 0
    for item in cal_map[(adsh, ptag)]:
        val = num_df[num_df['tag'] == item['ctag']]['value'].sum()
        total += val * item['w']
    return total
```

---

### 4. 第四步：TAG → 给标签加上含义，解决自定义tag问题
`tag.tsv` 是科目“字典”。

- 字段：`tag`、`tlabel`（名称）、`version`、`datatype`
- 用法：
  1. 给所有 `num` 里的 `tag` 字段加上 `tlabel` 名称，方便人工核对
  2. 解决公司自定义扩展tag的识别问题（如 `tsla_xxx` / `nvda_xxx`）
  3. 用 `tlabel` 做**关键词匹配**，比如“Acquisition”、“Divestiture”，识别业务含义

**例子：**
```python
tag_map = dict(zip(tag['tag'], tag['tlabel']))
num_target['tlabel'] = num_target['tag'].map(tag_map)
```

---

### 5. 第五步：PRE → 报表结构与层级，做“展示顺序”和“科目分类”
`pre.tsv` 告诉你报表“长什么样”。

- 字段：`tag`、`level`（层级）、`line`（行号）、`statement`（所属报表：BS/IS/CF）
- 用法：
  1. 确定科目属于哪张表（现金流量表/资产负债表/利润表）
  2. 利用层级关系，构建报表树结构
  3. 做**关键词+层级**双重过滤，解决标签不统一问题
     - 比如：在现金流量表下，找所有含“Acquisition”的行

**例子：**
```python
# 找出现金流量表的所有科目
cf_tags = pre[pre['statement'] == 'CF']['tag'].unique()
```

---

## 三、把它们串起来：你做「7个现金流字段」的完整流程
1.  **SUB** → 拿到目标公司财报的 `adsh`
2.  **NUM** → 拉取该财报所有年度USD数值
3.  **CAL** → 用公式计算4个合并净额字段
4.  **TAG** → 给所有字段加上名称，核对含义
5.  **PRE** → 确认这些字段确实属于现金流量表

---

## 四、如何解决「每家公司tag不一样」的终极问题
利用这5个文件的组合，你可以构建三层“语义归一”方案：

1.  **顶层固定（CAL + PRE）**：只锁定现金流量表顶层的4个父tag（如 `NetCashProvidedByUsedInInvestingActivities`），这些几乎所有公司都统一。
2.  **自动拆解（CAL）**：通过每家自己的 `cal.tsv` 自动拿到父项的所有子项，不管子项叫什么名字。
3.  **业务分类（TAG + PRE）**：通过 `tlabel` 和报表层级，把这些子项按业务含义分类（收购/处置/投资/回购）。

这样，你就彻底不用管每家公司用了什么奇葩tag，完全依赖SEC官方定义的规则来解析。

---

## 五、给你一个极简版使用路线
1.  **SUB 找财报**
2.  **NUM 拉数据**
3.  **CAL 算净额**
4.  **TAG 看含义**
5.  **PRE 定报表**

---

如果你愿意，我可以把你之前的 `EdgarFullEngine` 升级成**按这个官方流程重构的、工业级版本**，把 SUB/TAG/NUM/PRE/CAL 都整合进去，要不要？
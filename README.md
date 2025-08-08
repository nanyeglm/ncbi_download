# Endolysin NCBI 数据库下载器

一个模块化的 Python 工具，用于在 NCBI 的多个数据库中搜索并下载与 endolysin（溶菌酶）相关的数据，覆盖蛋白质、核酸、文献、基因功能、项目/样本、变异、化学、结构/分类等。

---

## 功能概览

- **模块化下载器**：按数据库类别拆分（序列/文献/基因/项目样本/变异/化学/结构分类），可独立预览与下载
- **完整工作链路**：`预览（esearch/esummary） → 下载（efetch） → 文件落盘 → 统计输出`
- **路径与导入规范**：基于 `PROJECT_ROOT` + `pathlib` 构建路径，绝对导入自 `endolysin_ncbi`
- **环境变量可配置**：邮箱、API Key、批大小、延时、最大条数、重试与退避策略等
- **错误批次重试**：支持基于错误文件精准补回（无需全量重跑）
- **健壮与可观测**：详细错误日志、统计文件、测试覆盖（全部通过）

---

## 安装与环境

### 方式一：Conda（推荐）

```bash
conda create -n endolysin python=3.10 -y
conda activate endolysin
pip install -r endolysin_ncbi/requirements.txt
```

如有 `environment.yml`：

```bash
conda env create -f environment.yml
conda activate endolysin
```

### 方式二：pip（系统 Python）

```bash
pip install -r endolysin_ncbi/requirements.txt
```

验证解释器：

```bash
python -c "import sys; print(sys.executable)"
```

---

## 快速开始（命令行）

建议从仓库根目录执行，使用模块入口更稳健：

```bash
# 仅预览（不下载），遍历所有数据库
python -m endolysin_ncbi.main --preview-only

# 仅预览“序列”类别
python -m endolysin_ncbi.main --preview-only --category sequence

# 仅预览单一数据库（例如：pubmed）
python -m endolysin_ncbi.main --preview-only --database pubmed

# 指定输出目录（相对 PROJECT_ROOT）
python -m endolysin_ncbi.main --preview-only --output-dir endolysin_data

# 实际下载单库（例如：protein）
python -m endolysin_ncbi.main --database protein
```

可选项：

- `--preview-only`：只做搜索与预览，不进行下载
- `--category {sequence,literature,gene,project,variation,chemical,structure}`
- `--database <db_name>`（建议小写，如 `protein`/`pubmed`）
- `--output-dir <dir>`：输出目录（默认 `endolysin_data`，位于项目根）
- `--retry-batches <list>`：仅重试错误批次号（如 `--retry-batches 789 790`，需同时指定 `--database`）

### 参数详解（命令行）

- `--preview-only`
  - 作用：只执行检索与预览，不拉取完整记录，输出 `download_lists_preview.txt`
  - 场景：评估体量、确定下载策略和格式

- `--category`
  - 取值：`sequence`/`literature`/`gene`/`project`/`variation`/`chemical`/`structure`
  - 作用：限定只处理某一类数据库（仍会在该类中筛出实际可用的子库）

- `--database`
  - 取值：如 `protein`、`pubmed`、`gene` 等
  - 作用：只处理单一数据库（通常与全量下载、批次重试一起使用）

- `--output-dir`
  - 取值：目录名或路径（相对 `PROJECT_ROOT`）
  - 作用：调整输出位置，默认 `endolysin_data`

- `--retry-batches`
  - 取值：一个或多个批次号，如 `--retry-batches 789 790`
  - 作用：解析 `error_batch_*.txt` 的记录范围，按会话 `webenv/query_key` 精确补回；需指定 `--database`

典型组合：

```bash
# 仅预览序列类，写入默认目录
python -m endolysin_ncbi.main --preview-only --category sequence

# 仅预览 pubmed，指定输出目录
python -m endolysin_ncbi.main --preview-only --database pubmed --output-dir results

# 下载 protein，并限制每库最大 100 条（通过环境变量控制）
ENDOLYSIN_MAX_RECORDS_PER_DATABASE=100 \
python -m endolysin_ncbi.main --database protein

# 下载结束后，仅重试错误批次 789、790、861（无需重跑全量）
python -m endolysin_ncbi.main --database protein --retry-batches 789 790 861
```

---

## 数据库类别与名称

- **sequence（序列）**：`protein`, `nucleotide`, `nuccore`, `nucest`, `nucgss`, `genome`, `popset`
- **literature（文献）**：`pubmed`, `pmc`, `books`
- **gene（基因功能）**：`gene`, `homologene`, `cdd`, `proteinclusters`, `gds`, `geo`, `unigene`, `probe`
- **project（项目样本）**：`bioproject`, `biosample`, `sra`, `assembly`
- **variation（变异）**：`snp`, `dbvar`, `clinvar`, `gap`
- **chemical（化学）**：`pcassay`, `pccompound`, `pcsubstance`
- **structure（结构/分类）**：`structure`, `taxonomy`, `mesh`, `omim`

下载格式映射见 `endolysin_ncbi/config/settings.py` 的 `DATABASE_FORMATS`（序列类多为 GenBank 文本，其余多为 XML）。

---

## 各数据库说明（格式、解析及示例）

说明中的“默认格式”来自 `config/settings.py` → `DATABASE_FORMATS`；文件扩展名由 `get_file_extension()` 决定（`gb/text → .gbk`，`xml → .xml`，其余文本 → `.txt`）。

### 序列（sequence）

| 数据库 | 简述 | 默认格式 | 扩展名 | 解析要点 |
|---|---|---|---|---|
| protein | 蛋白质序列与注释 | gb/text | .gbk | GenBank 记录以 `//` 分隔；ID 来自 ACCESSION/LOCUS |
| nucleotide | 核酸序列（DNA/RNA） | gb/text | .gbk | 同上 |
| nuccore | 核心核酸集合 | gb/text | .gbk | 同上 |
| nucest | 表达序列标签 | gb/text | .gbk | 同上 |
| nucgss | 基因组调查序列 | gb/text | .gbk | 同上 |
| genome | 基因组序列 | gb/text | .gbk | 同上（体量大，先预览） |
| popset | 群体遗传学序列 | gb/text | .gbk | 同上 |

解析逻辑：`rettype == 'gb'` → `parse_genbank_records()`，按 `//` 切分；ID 使用 `extract_record_id()`（ACCESSION/LOCUS）。

示例：

```bash
# 预览序列类
python -m endolysin_ncbi.main --preview-only --category sequence
# 下载 protein（每库至多 100 条）
ENDOLYSIN_MAX_RECORDS_PER_DATABASE=100 \
python -m endolysin_ncbi.main --database protein
```

### 文献（literature）

| 数据库 | 简述 | 默认格式 | 扩展名 | 解析要点 |
|---|---|---|---|---|
| pubmed | 生物医学文献摘要 | xml/xml | .xml | 解析 `<PubmedArticle>`；ID 使用 PMID |
| pmc | PubMed Central 全文 | xml/xml | .xml | 同上（结构更大） |
| books | NCBI 图书/章节 | xml/xml | .xml | XML 元素结构化信息 |

解析逻辑：`retmode == 'xml'` → `parse_xml_records()`，针对 `pubmed/pmc` 优先 `<PubmedArticle>`，通用模式回退；ID 提取优先 PMID。

示例：

```bash
python -m endolysin_ncbi.main --preview-only --database pubmed
```

### 基因功能（gene + expression）

| 数据库 | 简述 | 默认格式 | 扩展名 | 解析要点 |
|---|---|---|---|---|
| gene | 基因信息与注释 | xml/xml | .xml | 常见 `<DocumentSummary>`；ID 来自 `uid` |
| homologene | 同源基因 | xml/xml | .xml | 同上 |
| cdd | 保守结构域 | xml/xml | .xml | 同上 |
| proteinclusters | 蛋白质簇 | xml/xml | .xml | 同上 |
| gds | 基因表达数据集 | xml/xml | .xml | 通用 XML 解析 |
| geo | 基因表达综合 | xml/xml | .xml | 通用 XML 解析 |
| unigene | UniGene | xml/xml | .xml | 通用 XML 解析 |
| probe | 探针 | xml/xml | .xml | 通用 XML 解析 |

解析逻辑：`retmode == 'xml'` → 优先匹配 `<DocumentSummary>`，并回退至通用顶级元素模式；ID 可从 `uid` 提取。

示例：

```bash
python -m endolysin_ncbi.main --preview-only --category gene
```

### 项目/样本（project）

| 数据库 | 简述 | 默认格式 | 扩展名 | 解析要点 |
|---|---|---|---|---|
| bioproject | 研究项目信息 | xml/xml | .xml | 常见 `<DocumentSummary>`；ID 来自 `uid` |
| biosample | 生物样本元数据 | xml/xml | .xml | 同上 |
| sra | 测序运行 | xml/xml | .xml | 通用 XML 解析（体量大，建议先预览） |
| assembly | 基因组组装 | xml/xml | .xml | 通用 XML 解析 |

解析逻辑：以 XML 为主，优先匹配 `<DocumentSummary>`；如无则回退通用模式。

示例：

```bash
python -m endolysin_ncbi.main --preview-only --database biosample
```

### 变异（variation）

| 数据库 | 简述 | 默认格式 | 扩展名 | 解析要点 |
|---|---|---|---|---|
| snp | 单核苷酸多态性 | xml/xml | .xml | 通用 XML 解析 |
| dbvar | 结构变异 | xml/xml | .xml | 通用 XML 解析 |
| clinvar | 临床变异 | xml/xml | .xml | 通用 XML 解析 |
| gap | 基因型-表型 | xml/xml | .xml | 通用 XML 解析 |

示例：

```bash
python -m endolysin_ncbi.main --preview-only --database clinvar
```

### 化学（chemical）

| 数据库 | 简述 | 默认格式 | 扩展名 | 解析要点 |
|---|---|---|---|---|
| pcassay | 生物活性测定 | xml/xml | .xml | 通用 XML 解析 |
| pccompound | 化合物 | xml/xml | .xml | 通用 XML 解析 |
| pcsubstance | 物质 | xml/xml | .xml | 通用 XML 解析 |

### 结构/分类（structure + taxonomy）

| 数据库 | 简述 | 默认格式 | 扩展名 | 解析要点 |
|---|---|---|---|---|
| structure | 蛋白质 3D 结构 | xml/xml | .xml | 通用 XML 解析 |
| taxonomy | 分类学信息 | xml/xml | .xml | 通用 XML 解析 |
| mesh | 医学主题词 | xml/xml | .xml | 通用 XML 解析 |
| omim | 遗传病/基因信息 | xml/xml | .xml | 通用 XML 解析 |

---

## 环境变量（覆盖配置）

以下变量覆盖 `endolysin_ncbi/config/settings.py` 的默认值：

- `ENDOLYSIN_NCBI_EMAIL`：邮箱（必填，默认 `nanyecpu@163.com`）
- `ENDOLYSIN_NCBI_TOOL`：工具标识（默认 `endolysin_search_script`）
- `ENDOLYSIN_NCBI_API_KEY`：API Key（可提升速率上限）
- `ENDOLYSIN_MAX_RECORDS_PER_DATABASE`：单库最大下载条数（默认 `500000`）
- `ENDOLYSIN_BATCH_SIZE`：每批下载条数（默认 `50`）
- `ENDOLYSIN_DOWNLOAD_DELAY`：批次间延时秒数（默认 `1.0`）
- `ENDOLYSIN_SAMPLE_SIZE`：预览阶段样本摘要条数（默认 `10`）
- `ENDOLYSIN_SEARCH_TERM`：检索关键词（默认 `endolysin`）
- `ENDOLYSIN_OUTPUT_DIR`：输出目录（默认 `endolysin_data`，相对 `PROJECT_ROOT`）
- `ENDOLYSIN_MAX_RETRIES`：失败重试次数（默认 `5`）
- `ENDOLYSIN_RETRY_BACKOFF_BASE`：指数退避底数（默认 `2.0`）
- `ENDOLYSIN_RETRY_JITTER_MAX`：重试抖动幅度（默认 `0.5`）

示例：

```bash
# 将单库下载限制为 100 条，实际下载 protein
ENDOLYSIN_MAX_RECORDS_PER_DATABASE=100 \
python -m endolysin_ncbi.main --database protein

# 仅预览，调整样本摘要数
ENDOLYSIN_SAMPLE_SIZE=5 \
python -m endolysin_ncbi.main --preview-only --database pubmed
```

---

## 参数的代码用法（Python API）

以下示例展示如何在代码中设置输出目录、限制下载条数、调整批大小/延时、修改检索关键词，以及重试错误批次。

```python
import os
from endolysin_ncbi.main import EndolysinDownloadManager
from endolysin_ncbi.core.database_manager import DatabaseManager
from endolysin_ncbi.core.downloader import DataDownloader
from endolysin_ncbi.config.settings import PROJECT_ROOT

# 1) 全局参数（通过环境变量在进程内生效）
os.environ['ENDOLYSIN_MAX_RECORDS_PER_DATABASE'] = '100'  # 限制单库 100 条
os.environ['ENDOLYSIN_BATCH_SIZE'] = '50'                  # 每批 50 条
os.environ['ENDOLYSIN_DOWNLOAD_DELAY'] = '1.5'            # 批间延时 1.5 秒
os.environ['ENDOLYSIN_SAMPLE_SIZE'] = '5'                 # 预览样本 5 条
os.environ['ENDOLYSIN_SEARCH_TERM'] = 'endolysin'         # 检索关键词（可改为更复杂表达式）

# 2) 指定输出目录并下载单库
output_dir = PROJECT_ROOT / 'endolysin_data'
manager = EndolysinDownloadManager(str(output_dir))
result = manager.process_single_database('protein', download_full_data=True)
print('protein: found=', result.get('found_records'), 'downloaded=', result.get('downloaded_records'))

# 3) 仅预览某一类别
manager.process_category('sequence', download_full_data=False)

# 4) 全库（体量大，谨慎）
# manager.process_all_databases(download_full_data=True)

# 5) 下载结束后，仅重试错误批次（无需全量重跑）
dm = DatabaseManager()
count, webenv, query_key = dm.search_database('protein')
repaired = DataDownloader(str(output_dir)).retry_failed_batches(
    'protein', webenv, query_key, specific_batches=[789, 790, 861]
)
print('repaired files:', repaired)
```

说明：

- 本项目的可调参数（批大小、延时、最大条数、关键词等）通过环境变量读取，适合在命令行或进程内统一控制。
- 代码层面可直接传递 `output_dir` 给 `EndolysinDownloadManager` 来改变输出路径。
- `retry_failed_batches()` 会自动解析错误文件中的记录范围，按当前会话的 `webenv/query_key` 精准补回。

---

## 合规速率与避险建议（避免被限/封）

- 设置有效邮箱，建议配置 `ENDOLYSIN_NCBI_API_KEY`
- 建议限速：
  - 无 API Key：≤ 3 请求/秒
  - 有 API Key：≤ 10 请求/秒
- 推荐参数起点：`ENDOLYSIN_BATCH_SIZE=50`，`ENDOLYSIN_DOWNLOAD_DELAY=1.0~2.0` 秒
- 先 `--preview-only` 评估体量，再分库/分时段下载，避免并发
- 对 429/5xx 启用指数退避 + 抖动（已内置）
- 网络不稳时提高延迟、减小批次；大体量原始数据优先 NCBI Datasets/SRA Toolkit/FTP

---

## 错误批次重试（精准补回）

下载结束后若出现 `error_batch_*.txt`（记录失败批次与记录范围），可仅重试这些批次，无需全量重跑：

```bash
# 仅重试特定批次（示例：789、790、861）
python -m endolysin_ncbi.main --database protein --retry-batches 789 790 861
```

说明：

- 程序会解析 `endolysin_data/<db>/error_batch_*.txt` 内的“记录范围”，使用当前会话的 `webenv/query_key` 精确拉取对应区间
- 成功补回后会删除对应错误文件
- 若遇到 "Search Backend failed" 或限流，请稍后重试，或调大退避参数后再试

---

## 输出目录与产物

默认输出目录：`PROJECT_ROOT/endolysin_data`

结构示例：

```text
endolysin_data/
├── download_lists_preview.txt     # 各库预览汇总（仅预览阶段）
├── search_summary.txt             # 全流程搜索/下载比例摘要
└── <database>/
    ├── <record_id>.gbk|xml|txt   # 单条记录文件（按记录ID命名）
    ├── <database>_statistics.txt # 统计信息（总量/批次/大小分布/文件清单）
    └── error_batch_*.txt         # 错误批次记录（如有）
```

---

## 程序化使用（Python API）

```python
from endolysin_ncbi.main import EndolysinDownloadManager
from endolysin_ncbi.config.settings import PROJECT_ROOT

output_dir = PROJECT_ROOT / 'endolysin_data'
manager = EndolysinDownloadManager(str(output_dir))

# 单库（可下载或仅预览）
res1 = manager.process_single_database('protein', download_full_data=True)

# 按类别（仅预览）
res2 = manager.process_category('sequence', download_full_data=False)

# 全库（谨慎，体量大）
res3 = manager.process_all_databases(download_full_data=True)
```

仅重试错误批次（程序化）：

```python
from endolysin_ncbi.core.database_manager import DatabaseManager
from endolysin_ncbi.core.downloader import DataDownloader
from endolysin_ncbi.config.settings import PROJECT_ROOT

count, webenv, query_key = DatabaseManager().search_database('protein')
DataDownloader(str(PROJECT_ROOT/'endolysin_data')).retry_failed_batches(
    'protein', webenv, query_key, specific_batches=[789, 790, 861]
)
```

---

## 目录结构（源码）

```
.
├── endolysin_ncbi/
│   ├── __init__.py                       # 顶层包
│   ├── main.py                           # 命令行/程序化入口（支持 --preview-only / --category / --database / --output-dir / --retry-batches）
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                   # PROJECT_ROOT、输出目录、NCBI_EMAIL/TOOL/API_KEY、限速/重试/退避、格式映射等
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database_manager.py          # Entrez 配置；einfo/esearch/esummary/efetch 封装；指数退避与抖动
│   │   └── downloader.py                # DataDownloader：下载/解析/落盘/统计；retry_failed_batches 精准补回
│   ├── databases/
│   │   ├── __init__.py
│   │   ├── base_downloader.py           # 抽象基类：统一“搜索→预览→（可选）下载”流程
│   │   ├── sequence_databases.py        # SequenceDatabaseDownloader（protein 等）
│   │   ├── literature_databases.py      # LiteratureDatabaseDownloader（pubmed/pmc/books）
│   │   ├── gene_databases.py            # GeneDatabaseDownloader（gene/cdd 等）
│   │   └── other_databases.py           # ProjectSample/Variation/Chemical/StructureTaxonomy 各下载器
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py                # 目录创建、文件保存、错误/摘要/预览输出、文件名清理
│   │   └── format_utils.py              # 记录解析（GenBank/XML/Text）、ID 提取、大小格式化
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_database_manager.py     # Entrez 封装的单元测试（mock）
│   │   ├── test_downloaders.py          # 各下载器能力测试
│   │   └── test_utils.py                # 工具函数测试
│   └── requirements.txt                 # 项目依赖
├── endolysin_database.py                # 旧版/示例脚本（已对齐路径策略，推荐使用包入口替代）
├── README.md                            # 本文件
└── endolysin_data/                      # 运行时输出目录（默认；可通过环境变量覆盖）
    └── <database>/                      # 各数据库子目录：记录文件、统计文件、error_batch_*.txt（如有）
```

### 关键文件说明

- `endolysin_ncbi/main.py`
  - 命令行入口：`--preview-only`、`--category`、`--database`、`--output-dir`、`--retry-batches`
  - 程序化入口：`EndolysinDownloadManager` 用于单库/分类/全库处理

- `endolysin_ncbi/config/settings.py`
  - 路径：`PROJECT_ROOT`、默认输出目录（支持 `ENDOLYSIN_OUTPUT_DIR` 覆盖）
  - NCBI 配置：`ENDOLYSIN_NCBI_EMAIL`、`ENDOLYSIN_NCBI_TOOL`、`ENDOLYSIN_NCBI_API_KEY`
  - 下载/检索参数：`ENDOLYSIN_MAX_RECORDS_PER_DATABASE`、`ENDOLYSIN_BATCH_SIZE`、`ENDOLYSIN_DOWNLOAD_DELAY`、`ENDOLYSIN_SAMPLE_SIZE`、`ENDOLYSIN_SEARCH_TERM`
  - 失败重试：`ENDOLYSIN_MAX_RETRIES`、`ENDOLYSIN_RETRY_BACKOFF_BASE`、`ENDOLYSIN_RETRY_JITTER_MAX`
  - 格式映射：`DATABASE_FORMATS`、`get_download_format()`、`get_file_extension()`

- `endolysin_ncbi/core/database_manager.py`
  - 统一设置 `Entrez.email/tool/api_key`
  - 方法：
    - `get_available_databases()` 获取库列表
    - `search_database()` 获取 `count/webenv/query_key`
    - `get_record_ids()`、`get_record_summaries()`
    - `fetch_records()` 批量拉取记录内容
    - `get_download_list_info()` 预览阶段样本摘要
  - 内置 `_with_retries()`：对 429/5xx 等错误进行指数退避与抖动

- `endolysin_ncbi/core/downloader.py`
  - `DataDownloader.download_database_data()`：分批下载 → 解析 → 单文件落盘 → 统计输出
  - `_parse_records()`：根据 rettype/retmode 调用 `format_utils`
  - `_generate_database_statistics()`：生成 `<db>_statistics.txt`
  - `retry_failed_batches()`：解析 `error_batch_*.txt` 的记录范围，仅补回失败批次

- `endolysin_ncbi/databases/*`
  - `base_downloader.py`：抽象基类（`get_supported_databases()`、`is_supported()`、`process_database()` 等）
  - `sequence_databases.py`：序列类（protein/nucleotide/…）
  - `literature_databases.py`：文献类（pubmed/pmc/books）
  - `gene_databases.py`：基因功能类（gene/cdd/proteinclusters/…）
  - `other_databases.py`：项目样本/变异/化学/结构分类等下载器集合

- `endolysin_ncbi/utils/file_utils.py`
  - 目录：`create_output_directory()`、`create_database_directory()`
  - 文件：`save_record_file()`、`save_error_file()`、`generate_safe_filename()`
  - 摘要：`save_download_list_preview()`、`save_search_summary()`

- `endolysin_ncbi/utils/format_utils.py`
  - 解析：`parse_genbank_records()`、`parse_xml_records()`、`parse_text_records()`
  - 提取：`extract_record_id()`（用于命名）
  - 格式化：`format_file_size()`

- `endolysin_ncbi/tests/*`
  - `test_database_manager.py`：Entrez 交互的 mock 测试
  - `test_downloaders.py`：各下载器能力/支持范围测试
  - `test_utils.py`：解析/文件工具等测试

---

## 测试

```bash
# 运行全部测试（已通过）
pytest endolysin_ncbi/tests -q
```

---

## 许可与贡献

- 许可：MIT
- 欢迎提交 Issue 与 PR，完善功能、修复缺陷或改进文档

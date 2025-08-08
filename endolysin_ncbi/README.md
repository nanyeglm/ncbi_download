# Endolysin NCBI数据库下载器

一个模块化的Python工具，用于从NCBI数据库中搜索和下载endolysin相关的生物学数据。

## 项目特点

- **模块化设计**: 按数据库类型拆分为独立的下载器模块
- **多数据库支持**: 支持NCBI的所有主要数据库
- **灵活配置**: 可配置的下载参数和输出格式
- **错误处理**: 完善的错误处理和日志记录
- **测试覆盖**: 包含完整的单元测试
- **conda环境**: 统一的conda环境管理

## 项目结构

```
endolysin_ncbi/
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py         # 配置参数
├── core/                   # 核心功能模块
│   ├── __init__.py
│   ├── database_manager.py # 数据库管理
│   └── downloader.py       # 下载核心功能
├── databases/              # 数据库下载器模块
│   ├── __init__.py
│   ├── base_downloader.py  # 基础下载器类
│   ├── sequence_databases.py    # 序列数据库
│   ├── literature_databases.py  # 文献数据库
│   ├── gene_databases.py        # 基因数据库
│   └── other_databases.py       # 其他数据库
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── file_utils.py       # 文件操作工具
│   └── format_utils.py     # 格式化工具
├── tests/                  # 测试模块
│   ├── __init__.py
│   ├── test_database_manager.py
│   ├── test_downloaders.py
│   └── test_utils.py
├── main.py                 # 主程序入口
├── requirements.txt        # Python依赖
├── environment.yml         # conda环境配置
└── README.md              # 项目说明
```

## 安装和环境配置

### 使用conda环境（推荐）

1. 创建conda环境：

```bash
conda env create -f environment.yml
```

2. 激活环境：

```bash
conda activate endolysin
```

### 使用pip安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
# 运行完整的数据下载流程
python main.py

# 仅获取预览信息，不下载完整数据
python main.py --preview-only

# 只处理特定类别的数据库
python main.py --category sequence

# 只处理特定数据库
python main.py --database pubmed

# 指定输出目录
python main.py --output-dir /path/to/output
```

### 支持的数据库类别

- **sequence**: 序列数据库 (protein, nucleotide, nuccore, genome等)
- **literature**: 文献数据库 (pubmed, pmc, books)
- **gene**: 基因功能数据库 (gene, cdd, homologene等)
- **project**: 项目样本数据库 (bioproject, biosample, sra等)
- **variation**: 变异数据库 (snp, clinvar, dbvar等)
- **chemical**: 化学数据库 (pcassay, pccompound等)
- **structure**: 结构分类数据库 (structure, taxonomy, mesh等)

### 程序化使用

```python
from endolysin_ncbi.main import EndolysinDownloadManager

# 创建下载管理器
manager = EndolysinDownloadManager("output_directory")

# 处理单个数据库
result = manager.process_single_database("pubmed", download_full_data=True)

# 处理特定类别
result = manager.process_category("sequence", download_full_data=False)

# 处理所有数据库
result = manager.process_all_databases(download_full_data=True)
```

## 配置说明

主要配置参数在 `config/settings.py` 中：

- `NCBI_EMAIL`: NCBI API所需的邮箱地址
- `MAX_RECORDS_PER_DATABASE`: 每个数据库最大下载记录数
- `BATCH_SIZE`: 每批下载的记录数
- `DOWNLOAD_DELAY`: 下载间隔时间（秒）
- `SEARCH_TERM`: 搜索关键词（默认为"endolysin"）

## 输出文件

程序会在指定的输出目录中创建以下文件：

- `数据库名/`: 每个数据库的独立目录
- `记录ID.格式`: 每条记录的独立文件
- `数据库名_statistics.txt`: 数据库下载统计信息
- `download_lists_preview.txt`: 下载列表预览
- `search_summary.txt`: 搜索结果摘要

## 测试

运行测试：

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_database_manager.py

# 运行测试并显示覆盖率
pytest tests/ --cov=.
```

## 开发指南

### 添加新的数据库支持

1. 在相应的数据库下载器类中添加数据库名称
2. 在 `config/settings.py` 中配置数据库格式
3. 添加相应的测试用例

### 代码风格

项目使用以下工具保证代码质量：

- `black`: 代码格式化
- `flake8`: 代码风格检查
- `pytest`: 单元测试

```bash
# 格式化代码
black .

# 检查代码风格
flake8 .

# 运行测试
pytest
```

## 注意事项

1. **NCBI API限制**: 请遵守NCBI的API使用限制，避免过于频繁的请求
2. **邮箱配置**: 必须在配置文件中设置有效的邮箱地址
3. **存储空间**: 某些数据库可能包含大量数据，请确保有足够的存储空间
4. **网络连接**: 需要稳定的网络连接来访问NCBI数据库

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

## 高级用法与完整指南

### 运行建议

- 从仓库根目录执行命令，使用模块入口更稳健：
  - `python -m endolysin_ncbi.main --preview-only`
  - 可避免因相对路径与工作目录变化导致的问题。

### 常用命令示例

```bash
# 1) 全量预览（不下载），遍历所有数据库
python -m endolysin_ncbi.main --preview-only

# 2) 仅预览“序列”类别
python -m endolysin_ncbi.main --preview-only --category sequence

# 3) 仅预览单一数据库（例：pubmed）
python -m endolysin_ncbi.main --preview-only --database pubmed

# 4) 指定输出目录（相对 PROJECT_ROOT 构建）
python -m endolysin_ncbi.main --preview-only --output-dir endolysin_data

# 5) 实际下载单库（例：protein）
python -m endolysin_ncbi.main --database protein

# 6) 限制单库最大下载条数（例：每库最多 100 条）
ENDOLYSIN_MAX_RECORDS_PER_DATABASE=100 \
python -m endolysin_ncbi.main --database protein
```

- **可选参数**：
  - `--preview-only`：只检索与预览，不执行下载
  - `--category {sequence,literature,gene,project,variation,chemical,structure}`
  - `--database <db_name>`（推荐小写，如 `protein`/`pubmed`）
  - `--output-dir <dir>` 输出目录，默认见配置

### 支持的数据库一览

- **sequence（序列）**：`protein`, `nucleotide`, `nuccore`, `nucest`, `nucgss`, `genome`, `popset`
- **literature（文献）**：`pubmed`, `pmc`, `books`
- **gene（基因功能）**：`gene`, `homologene`, `cdd`, `proteinclusters`, `gds`, `geo`, `unigene`, `probe`
- **project（项目样本）**：`bioproject`, `biosample`, `sra`, `assembly`
- **variation（变异）**：`snp`, `dbvar`, `clinvar`, `gap`
- **chemical（化学）**：`pcassay`, `pccompound`, `pcsubstance`
- **structure（结构/分类）**：`structure`, `taxonomy`, `mesh`, `omim`

各库下载格式见 `endolysin_ncbi/config/settings.py` 中 `DATABASE_FORMATS`（序列类多为 GenBank 文本，其余多为 XML）。

### 环境变量（覆盖配置）

以下变量覆盖 `endolysin_ncbi/config/settings.py` 中默认值：

- `ENDOLYSIN_NCBI_EMAIL`：NCBI E-utilities 要求邮箱（默认 `nanyecpu@163.com`）
- `ENDOLYSIN_NCBI_TOOL`：工具标识（默认 `endolysin_search_script`）
- `ENDOLYSIN_MAX_RECORDS_PER_DATABASE`：单库最大下载条数（默认 `500000`）
- `ENDOLYSIN_BATCH_SIZE`：每批下载条数（默认 `50`）
- `ENDOLYSIN_DOWNLOAD_DELAY`：批次间延迟秒数（默认 `1.0`）
- `ENDOLYSIN_SAMPLE_SIZE`：预览阶段样本摘要条数（默认 `10`）
- `ENDOLYSIN_SEARCH_TERM`：检索关键词（默认 `endolysin`）
- `ENDOLYSIN_OUTPUT_DIR`：输出目录相对路径（默认 `endolysin_data`，基于 `PROJECT_ROOT`）

如需代理（网络环境受限）：

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
```

### 输出目录结构与产物

```text
endolysin_data/
├── download_lists_preview.txt     # 各库预览汇总（仅预览阶段）
├── search_summary.txt             # 全流程搜索/下载比例摘要
└── <database>/
    ├── <record_id>.gbk|xml|txt   # 单条记录文件（按记录ID命名）
    └── <database>_statistics.txt # 统计信息（总量/批次/大小分布/文件清单）
```

### 程序化使用（Python API）

```python
from endolysin_ncbi.main import EndolysinDownloadManager
from endolysin_ncbi.config.settings import PROJECT_ROOT

output_dir = PROJECT_ROOT / 'endolysin_data'
manager = EndolysinDownloadManager(str(output_dir))

# 单库：可选择下载或仅预览
res1 = manager.process_single_database('protein', download_full_data=True)

# 按类别（仅预览）
res2 = manager.process_category('sequence', download_full_data=False)

# 全库（完整下载，谨慎使用）
res3 = manager.process_all_databases(download_full_data=True)
```

### 常见问题（FAQ）

- **为什么必须配置邮箱？** NCBI E-utilities 要求设置有效邮箱便于联系与限流识别。
- **429/限流怎么办？** 调大 `ENDOLYSIN_DOWNLOAD_DELAY`，或减小 `ENDOLYSIN_BATCH_SIZE`、`ENDOLYSIN_MAX_RECORDS_PER_DATABASE`。
- **网络不稳定？** 配置 HTTP/HTTPS 代理，适度增大延迟；失败批次会写入错误文件。
- **磁盘/内存压力大？** 先 `--preview-only` 评估体量；分库/分类分批下载；限制每库最大记录数。
- **断点续传？** 当前按记录ID命名、幂等保存，多次运行会跳过已存在文件（可扩展为跳过逻辑）。

### 扩展开发

- 新增数据库：
  1. 在对应下载器 `get_supported_databases` 中加入库名
  2. 在 `config/settings.py` 的 `DATABASE_FORMATS` 中配置格式
  3. 补充单元测试
- 路径与导入约束：
  - 所有路径以 `PROJECT_ROOT`（定义于 `config/settings.py`）为基，使用 `pathlib.Path`
  - 统一使用 `endolysin_ncbi` 顶层包的绝对导入

### 测试

```bash
pytest endolysin_ncbi/tests -q
```

> 当前版本：全部测试通过。

### 旧版脚本说明（可选）

`endolysin_database.py` 为保留示例脚本，已对齐 `PROJECT_ROOT` 路径策略，但不保证与包入口功能完全一致，推荐使用：

```bash
python -m endolysin_ncbi.main --preview-only --database protein
```

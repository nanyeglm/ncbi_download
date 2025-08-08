from Bio import Entrez, SeqIO
import os
import time
from datetime import datetime
from pathlib import Path
from endolysin_ncbi.config.settings import PROJECT_ROOT

# 1. 设置基本参数（必须包含 email）
Entrez.email = "nanyecpu@163.com"
Entrez.tool = "endolysin_search_script"

# 2. 配置下载参数
MAX_RECORDS_PER_DATABASE = 500000  # 每个数据库最大下载记录数（可根据需要调整）
BATCH_SIZE = 50                  # 每批下载的记录数
DOWNLOAD_DELAY = 1.0             # 下载间隔（秒），避免过于频繁请求

# 创建输出目录（基于项目根目录）
output_dir = PROJECT_ROOT / "endolysin_data"
output_dir.mkdir(parents=True, exist_ok=True)

print(f"开始检索 NCBI 所有数据库中的 endolysin 相关数据...")
print(f"数据将保存到: {output_dir}")
print(f"配置: 每个数据库最多下载 {MAX_RECORDS_PER_DATABASE} 条记录，批次大小 {BATCH_SIZE}")
print("=" * 60)

# 2. 获取所有可用的 NCBI 数据库
def get_available_databases():
    """获取 NCBI 所有可用数据库列表"""
    try:
        info_handle = Entrez.einfo()
        info_results = Entrez.read(info_handle)
        info_handle.close()
        return info_results["DbList"]
    except Exception as e:
        print(f"获取数据库列表时出错: {e}")
        return []

# 3. 在指定数据库中搜索 endolysin
def search_database(database, search_term="endolysin"):
    """在指定数据库中搜索关键词"""
    try:
        search_handle = Entrez.esearch(
            db=database,
            term=search_term,
            usehistory="y",
            retmax=0
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        count = int(search_results["Count"])
        webenv = search_results.get("WebEnv", "")
        query_key = search_results.get("QueryKey", "")
        
        return count, webenv, query_key
    except Exception as e:
        print(f"在数据库 {database} 中搜索时出错: {e}")
        return 0, "", ""

# 4. 根据数据库类型选择最适合的完整元数据格式
def get_download_format(database):
    """根据数据库类型确定下载格式 - 优化为获取完整元数据"""
    
    # 序列数据库 - 使用GenBank格式获取完整信息（包括LOCUS, DEFINITION, FEATURES等）
    sequence_databases = {
        'protein': ('gb', 'text'),          # GenBank格式，包含完整蛋白质信息
        'nucleotide': ('gb', 'text'),       # GenBank格式，包含完整核酸序列信息
        'nuccore': ('gb', 'text'),          # GenBank格式，核心核酸数据库
        'nucest': ('gb', 'text'),           # GenBank格式，EST序列
        'nucgss': ('gb', 'text'),           # GenBank格式，GSS序列
        'genome': ('gb', 'text'),           # GenBank格式，基因组序列
        'popset': ('gb', 'text'),           # GenBank格式，群体序列
    }
    
    # 文献数据库 - 使用XML格式获取完整bibliographic信息
    literature_databases = {
        'pubmed': ('xml', 'xml'),           # PubMed XML格式，包含完整文献信息
        'pmc': ('xml', 'xml'),              # PMC XML格式，包含全文信息
        'books': ('xml', 'xml'),            # 图书信息XML格式
    }
    
    # 基因和功能数据库 - 使用XML获取详细信息
    gene_function_databases = {
        'gene': ('xml', 'xml'),             # 基因XML格式，包含完整基因信息
        'homologene': ('xml', 'xml'),       # 同源基因XML格式
        'cdd': ('xml', 'xml'),              # 保守结构域XML格式
        'proteinclusters': ('xml', 'xml'),  # 蛋白质簇XML格式
    }
    
    # 生物项目和样本数据库
    project_sample_databases = {
        'bioproject': ('xml', 'xml'),       # 生物项目完整XML
        'biosample': ('xml', 'xml'),        # 生物样本完整XML
        'sra': ('xml', 'xml'),              # SRA完整XML元数据
        'assembly': ('xml', 'xml'),         # 基因组组装完整信息
    }
    
    # 变异和临床数据库
    variation_databases = {
        'snp': ('xml', 'xml'),              # SNP变异XML格式
        'dbvar': ('xml', 'xml'),            # 结构变异XML格式
        'clinvar': ('xml', 'xml'),          # 临床变异完整XML
        'gap': ('xml', 'xml'),              # 基因型-表型XML
    }
    
    # 化学和药物数据库
    chemical_databases = {
        'pcassay': ('xml', 'xml'),          # 生物测定完整XML
        'pccompound': ('xml', 'xml'),       # 化合物完整XML  
        'pcsubstance': ('xml', 'xml'),      # 物质完整XML
    }
    
    # 表达和功能数据库
    expression_databases = {
        'gds': ('xml', 'xml'),              # 基因表达XML格式
        'geo': ('xml', 'xml'),              # GEO完整XML
        'unigene': ('xml', 'xml'),          # UniGene XML格式
        'probe': ('xml', 'xml'),            # 探针XML格式
    }
    
    # 结构和分类数据库
    structure_taxonomy_databases = {
        'structure': ('xml', 'xml'),        # 蛋白质结构XML
        'taxonomy': ('xml', 'xml'),         # 分类学完整XML
        'mesh': ('xml', 'xml'),             # MeSH术语XML
        'omim': ('xml', 'xml'),             # OMIM完整XML
    }
    
    # 合并所有格式映射
    format_mapping = {}
    format_mapping.update(sequence_databases)
    format_mapping.update(literature_databases)
    format_mapping.update(gene_function_databases)
    format_mapping.update(project_sample_databases)
    format_mapping.update(variation_databases)
    format_mapping.update(chemical_databases)
    format_mapping.update(expression_databases)
    format_mapping.update(structure_taxonomy_databases)
    
    # 返回对应格式，默认使用XML获取最详细信息
    return format_mapping.get(database.lower(), ('xml', 'xml'))

# 5. 解析数据条目的辅助函数
def parse_genbank_records(data):
    """解析GenBank格式数据，返回单个记录列表"""
    # GenBank记录以//结尾分隔
    records = []
    current_record = []
    
    for line in data.split('\n'):
        current_record.append(line)
        if line.strip() == '//':
            if len(current_record) > 1:  # 确保不是空记录
                records.append('\n'.join(current_record))
            current_record = []
    
    # 处理最后一个记录（如果没有以//结尾）
    if current_record and any(line.strip() for line in current_record):
        records.append('\n'.join(current_record))
    
    return records

def parse_xml_records(data, database):
    """解析XML格式数据，返回单个记录列表"""
    import re
    records = []
    
    # 不同数据库的XML结构不同，需要分别处理
    if database in ['pubmed', 'pmc']:
        # PubMed记录通常在<PubmedArticle>标签内
        pattern = r'<PubmedArticle.*?</PubmedArticle>'
        matches = re.findall(pattern, data, re.DOTALL)
        records.extend(matches)
        
        # 也检查<Article>标签
        pattern = r'<Article.*?</Article>'
        matches = re.findall(pattern, data, re.DOTALL)
        records.extend(matches)
        
    elif database in ['gene', 'biosample', 'bioproject']:
        # 基因、样本、项目记录
        pattern = r'<DocumentSummary.*?</DocumentSummary>'
        matches = re.findall(pattern, data, re.DOTALL)
        records.extend(matches)
        
    else:
        # 通用XML记录解析
        # 尝试找到重复的顶级元素
        common_patterns = [
            r'<DocumentSummary.*?</DocumentSummary>',
            r'<record.*?</record>',
            r'<entry.*?</entry>',
            r'<item.*?</item>'
        ]
        
        for pattern in common_patterns:
            matches = re.findall(pattern, data, re.DOTALL | re.IGNORECASE)
            if matches:
                records.extend(matches)
                break
    
    # 如果没有找到明确的记录分隔，将整个内容作为一个记录
    if not records and data.strip():
        records.append(data)
    
    return records

def parse_text_records(data, database):
    """解析文本格式数据，返回单个记录列表"""
    records = []
    
    if database == 'sra':
        # SRA运行信息通常按行分隔
        lines = data.strip().split('\n')
        if len(lines) > 1:  # 跳过标题行
            for i, line in enumerate(lines[1:], 1):
                if line.strip():
                    records.append(f"# SRA Record {i}\n{lines[0]}\n{line}")
    else:
        # 其他文本格式，尝试按段落分隔
        paragraphs = data.split('\n\n')
        for i, paragraph in enumerate(paragraphs, 1):
            if paragraph.strip():
                records.append(paragraph)
    
    return records

def extract_record_id(record_content, database, rettype, record_index):
    """从记录内容中提取ID，用于文件命名"""
    import re
    
    if rettype == 'gb':
        # GenBank格式，查找ACCESSION行
        match = re.search(r'ACCESSION\s+(\S+)', record_content)
        if match:
            return match.group(1)
        # 查找LOCUS行
        match = re.search(r'LOCUS\s+(\S+)', record_content)
        if match:
            return match.group(1)
    
    elif database == 'pubmed':
        # PubMed ID
        match = re.search(r'<PMID.*?>(\d+)</PMID>', record_content)
        if match:
            return f"PMID_{match.group(1)}"
    
    elif database in ['gene', 'biosample', 'bioproject']:
        # DocumentSummary ID
        match = re.search(r'<DocumentSummary.*?uid="(\d+)"', record_content)
        if match:
            return f"{database}_{match.group(1)}"
    
    # 默认使用索引
    return f"{database}_record_{record_index:06d}"

# 6. 获取下载列表信息（不下载完整内容）
def get_download_list(database, count, webenv, query_key, sample_size=10):
    """获取指定数据库的下载列表信息，只获取基本信息而不下载完整内容"""
    if count == 0:
        return []
    
    print(f"正在获取 {database} 数据库的记录列表信息...")
    print(f"  总记录数: {count}")
    print(f"  获取样本数: {min(sample_size, count)}")
    
    # 获取记录ID列表
    try:
        # 获取所有记录的ID列表
        search_handle = Entrez.esearch(
            db=database,
            term="endolysin",
            usehistory="y",
            retmax=min(count, MAX_RECORDS_PER_DATABASE)  # 限制获取的ID数量
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        id_list = search_results.get("IdList", [])
        print(f"  获取到 {len(id_list)} 个记录ID")
        
        # 获取样本记录的摘要信息
        sample_records = []
        if id_list:
            sample_ids = id_list[:sample_size]  # 只取前几个作为样本
            
            try:
                # 获取摘要信息
                summary_handle = Entrez.esummary(
                    db=database,
                    id=','.join(sample_ids)
                )
                summaries = Entrez.read(summary_handle)
                summary_handle.close()
                
                # 处理摘要信息
                for i, summary in enumerate(summaries):
                    if isinstance(summary, dict):
                        record_info = {
                            'id': summary.get('Id', sample_ids[i] if i < len(sample_ids) else 'unknown'),
                            'title': summary.get('Title', summary.get('Caption', 'No title')),
                            'authors': summary.get('AuthorList', summary.get('Authors', 'No authors')),
                            'date': summary.get('PubDate', summary.get('CreateDate', 'No date')),
                            'database': database
                        }
                        sample_records.append(record_info)
                
            except Exception as e:
                print(f"  获取摘要信息时出错: {e}")
                # 如果获取摘要失败，至少返回ID信息
                for record_id in sample_ids:
                    sample_records.append({
                        'id': record_id,
                        'title': 'Title not available',
                        'authors': 'Authors not available',
                        'date': 'Date not available',
                        'database': database
                    })
        
        return {
            'database': database,
            'total_count': count,
            'available_ids': len(id_list),
            'sample_records': sample_records,
            'format_info': get_download_format(database)
        }
        
    except Exception as e:
        print(f"  获取 {database} 数据库列表时出错: {e}")
        return {
            'database': database,
            'total_count': count,
            'available_ids': 0,
            'sample_records': [],
            'format_info': get_download_format(database),
            'error': str(e)
        }

# 7. 增强的下载函数 - 按条目分别保存（保留原功能）
def download_database_data(database, count, webenv, query_key, batch_size=None):
    """下载指定数据库的完整元数据，每条记录保存为单独文件"""
    if count == 0:
        return 0
    
    # 使用全局配置或默认值
    if batch_size is None:
        batch_size = BATCH_SIZE
    
    rettype, retmode = get_download_format(database)
    
    # 根据格式选择合适的文件扩展名
    if rettype == 'gb':
        file_extension = 'gbk'  # GenBank格式
    elif retmode == 'xml':
        file_extension = 'xml'  # XML格式
    elif retmode == 'csv':
        file_extension = 'csv'  # CSV格式
    else:
        file_extension = 'txt'  # 其他文本格式
    
    # 创建数据库子文件夹
    database_dir = os.path.join(output_dir, database)
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
    
    print(f"正在下载 {database} 数据库的 {count} 条完整元数据记录...")
    print(f"  格式: {rettype} ({retmode})")
    print(f"  保存目录: {database_dir}")
    
    # 分批下载，使用全局配置的下载限制
    actual_download_count = min(count, MAX_RECORDS_PER_DATABASE)
    print(f"  计划下载: {actual_download_count} 条记录 (总共 {count} 条可用)")
    
    downloaded_records = []  # 用于统计
    total_file_size = 0
    record_counter = 0
    
    for start in range(0, actual_download_count, batch_size):
        end = min(start + batch_size, actual_download_count)
        print(f"  下载第 {start + 1} - {end} 条记录 (完整元数据)")
        
        try:
            fetch_handle = Entrez.efetch(
                db=database,
                rettype=rettype,
                retmode=retmode,
                retstart=start,
                retmax=batch_size,
                webenv=webenv,
                query_key=query_key
            )
            
            data = fetch_handle.read()
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
            
            fetch_handle.close()
            
            # 解析数据为单个记录
            if rettype == 'gb':
                records = parse_genbank_records(data)
            elif retmode == 'xml':
                records = parse_xml_records(data, database)
            else:
                records = parse_text_records(data, database)
            
            # 保存每个记录为单独文件
            for record in records:
                if record.strip():  # 确保记录不为空
                    record_counter += 1
                    record_id = extract_record_id(record, database, rettype, record_counter)
                    
                    filename = f"{record_id}.{file_extension}"
                    filepath = os.path.join(database_dir, filename)
                    
                    # 确保文件名是安全的（移除非法字符）
                    safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
                    safe_filepath = os.path.join(database_dir, safe_filename)
                    
                    with open(safe_filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# 数据库: {database}\n")
                        f.write(f"# 记录ID: {record_id}\n")
                        f.write(f"# 下载时间: {datetime.now()}\n")
                        f.write(f"# 格式: {rettype} ({retmode})\n")
                        f.write("# " + "="*50 + "\n\n")
                        f.write(record)
                        if not record.endswith('\n'):
                            f.write('\n')
                    
                    # 统计信息
                    file_size = os.path.getsize(safe_filepath)
                    total_file_size += file_size
                    downloaded_records.append({
                        'filename': safe_filename,
                        'record_id': record_id,
                        'file_size': file_size,
                        'batch': start//batch_size + 1
                    })
            
            time.sleep(DOWNLOAD_DELAY)  # 使用全局配置的延迟时间
            
        except Exception as e:
            error_msg = f"下载记录 {start+1}-{end} 时出错: {e}"
            print(f"  {error_msg}")
            
            # 记录错误信息
            error_file = os.path.join(database_dir, f"error_batch_{start//batch_size + 1}.txt")
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"# 错误信息\n")
                f.write(f"# 数据库: {database}\n")
                f.write(f"# 批次: {start//batch_size + 1}\n")
                f.write(f"# 记录范围: {start+1}-{end}\n")
                f.write(f"# 时间: {datetime.now()}\n")
                f.write("# " + "="*50 + "\n\n")
                f.write(error_msg)
            continue
    
    # 生成数据库统计信息文件
    generate_database_statistics(database, database_dir, downloaded_records, total_file_size, count, actual_download_count, rettype, retmode)
    
    print(f"  {database} 数据库下载完成:")
    print(f"    - 总共下载: {len(downloaded_records)} 个文件")
    print(f"    - 总大小: {format_file_size(total_file_size)}")
    print(f"    - 保存目录: {database_dir}")
    
    # 返回实际下载的记录数
    return len(downloaded_records)

# 7. 生成数据库统计信息
def generate_database_statistics(database, database_dir, downloaded_records, total_file_size, total_count, downloaded_count, rettype, retmode):
    """为每个数据库生成详细的统计信息文件"""
    
    stats_file = os.path.join(database_dir, f"{database}_statistics.txt")
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write(f"# {database.upper()} 数据库统计信息\n")
        f.write("=" * 60 + "\n\n")
        
        # 基本信息
        f.write("## 基本信息\n")
        f.write(f"数据库名称: {database}\n")
        f.write(f"搜索关键词: endolysin\n")
        f.write(f"下载时间: {datetime.now()}\n")
        f.write(f"数据格式: {rettype} ({retmode})\n")
        f.write(f"保存目录: {database_dir}\n\n")
        
        # 数量统计
        f.write("## 数量统计\n")
        f.write(f"总找到记录数: {total_count:,}\n")
        f.write(f"实际下载记录数: {downloaded_count:,}\n")
        f.write(f"成功保存文件数: {len(downloaded_records):,}\n")
        f.write(f"下载完成率: {(len(downloaded_records)/downloaded_count*100):.1f}%\n")
        f.write(f"总覆盖率: {(len(downloaded_records)/total_count*100):.1f}%\n\n")
        
        # 文件大小统计
        f.write("## 文件大小统计\n")
        f.write(f"总文件大小: {format_file_size(total_file_size)}\n")
        
        if downloaded_records:
            file_sizes = [record['file_size'] for record in downloaded_records]
            avg_size = total_file_size / len(downloaded_records)
            max_size = max(file_sizes)
            min_size = min(file_sizes)
            
            f.write(f"平均文件大小: {format_file_size(avg_size)}\n")
            f.write(f"最大文件大小: {format_file_size(max_size)}\n")
            f.write(f"最小文件大小: {format_file_size(min_size)}\n\n")
        
        # 批次统计
        if downloaded_records:
            batch_stats = {}
            for record in downloaded_records:
                batch = record['batch']
                if batch not in batch_stats:
                    batch_stats[batch] = []
                batch_stats[batch].append(record)
            
            f.write("## 批次下载统计\n")
            f.write(f"总批次数: {len(batch_stats)}\n")
            for batch_num in sorted(batch_stats.keys()):
                batch_records = batch_stats[batch_num]
                batch_size = sum(record['file_size'] for record in batch_records)
                f.write(f"批次 {batch_num}: {len(batch_records)} 个文件, {format_file_size(batch_size)}\n")
            f.write("\n")
        
        # 文件列表
        f.write("## 下载文件列表\n")
        f.write(f"{'序号':<6} {'文件名':<50} {'记录ID':<20} {'大小':<10} {'批次':<6}\n")
        f.write("-" * 92 + "\n")
        
        for i, record in enumerate(downloaded_records, 1):
            filename = record['filename'][:47] + "..." if len(record['filename']) > 50 else record['filename']
            record_id = record['record_id'][:17] + "..." if len(record['record_id']) > 20 else record['record_id']
            f.write(f"{i:<6} {filename:<50} {record_id:<20} {format_file_size(record['file_size']):<10} {record['batch']:<6}\n")
        
        f.write("\n# 统计信息生成完成\n")
    
    print(f"    - 统计信息已保存: {stats_file}")

# 8. 格式化文件大小显示
def format_file_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes >= 1024*1024*1024:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"
    elif size_bytes >= 1024*1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes/1024:.2f} KB"
    else:
        return f"{size_bytes} B"

# 6. 主程序：遍历所有数据库
def main():
    # 获取所有数据库
    databases = get_available_databases()
    if not databases:
        print("无法获取数据库列表")
        return
    
    print(f"找到 {len(databases)} 个 NCBI 数据库")
    print(f"数据库列表: {', '.join(databases)}")
    print("=" * 60)
    
    # 存储搜索结果统计
    search_summary = []
    download_lists = []  # 存储各数据库的下载列表信息
    
    print("\n第一阶段：获取各数据库的下载列表信息")
    print("=" * 60)
    
    # 遍历每个数据库，先获取下载列表
    for i, database in enumerate(databases, 1):
        print(f"\n[{i}/{len(databases)}] 正在检查数据库: {database}")
        
        # 搜索 endolysin
        count, webenv, query_key = search_database(database)
        
        if count > 0:
            print(f"  找到 {count} 条相关记录")
            
            # 获取下载列表信息（不下载完整内容）
            download_info = get_download_list(database, count, webenv, query_key, sample_size=5)
            download_lists.append(download_info)
            search_summary.append((database, count, 0))  # 暂时设置下载数为0
        else:
            print(f"  未找到相关记录")
        
        time.sleep(0.3)  # 避免请求过于频繁
    
    # 输出下载列表摘要
    print("\n" + "="*80)
    print("下载列表摘要 - 各数据库可下载内容预览")
    print("="*80)
    
    if download_lists:
        # 保存详细的下载列表信息
        list_file = os.path.join(output_dir, "download_lists_preview.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write("Endolysin 数据库下载列表预览\n")
            f.write(f"生成时间: {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            
            total_records = 0
            total_available = 0
            
            for download_info in download_lists:
                database = download_info['database']
                total_count = download_info['total_count']
                available_ids = download_info['available_ids']
                sample_records = download_info['sample_records']
                format_info = download_info['format_info']
                
                total_records += total_count
                total_available += available_ids
                
                print(f"\n数据库: {database.upper()}")
                print(f"  总记录数: {total_count:,}")
                print(f"  可获取ID数: {available_ids:,}")
                print(f"  下载格式: {format_info[0]} ({format_info[1]})")
                print(f"  样本记录数: {len(sample_records)}")
                
                f.write(f"数据库: {database.upper()}\n")
                f.write(f"总记录数: {total_count:,}\n")
                f.write(f"可获取ID数: {available_ids:,}\n")
                f.write(f"下载格式: {format_info[0]} ({format_info[1]})\n")
                f.write(f"样本记录数: {len(sample_records)}\n")
                
                if 'error' in download_info:
                    print(f"  错误: {download_info['error']}")
                    f.write(f"错误: {download_info['error']}\n")
                
                # 显示样本记录
                if sample_records:
                    print("  样本记录:")
                    f.write("样本记录:\n")
                    for j, record in enumerate(sample_records[:3], 1):  # 只显示前3个
                        title = record['title'][:60] + "..." if len(record['title']) > 60 else record['title']
                        print(f"    {j}. ID: {record['id']}")
                        print(f"       标题: {title}")
                        print(f"       作者: {record['authors']}")
                        print(f"       日期: {record['date']}")
                        
                        f.write(f"  {j}. ID: {record['id']}\n")
                        f.write(f"     标题: {record['title']}\n")
                        f.write(f"     作者: {record['authors']}\n")
                        f.write(f"     日期: {record['date']}\n")
                
                f.write("-" * 60 + "\n\n")
            
            print(f"\n总计:")
            print(f"  有数据的数据库: {len(download_lists)} 个")
            print(f"  总记录数: {total_records:,}")
            print(f"  总可获取数: {total_available:,}")
            
            f.write(f"总计:\n")
            f.write(f"有数据的数据库: {len(download_lists)} 个\n")
            f.write(f"总记录数: {total_records:,}\n")
            f.write(f"总可获取数: {total_available:,}\n")
        
        print(f"\n详细下载列表已保存到: {list_file}")
        
        # 询问用户是否继续下载
        print("\n" + "="*60)
        print("是否继续下载完整数据？")
        print("输入 'y' 或 'yes' 继续下载，其他任意键退出")
        user_input = input("请选择: ").strip().lower()
        
        if user_input in ['y', 'yes']:
            print("\n第二阶段：开始下载完整数据")
            print("=" * 60)
            
            # 重新遍历进行实际下载
            search_summary = []  # 重置统计
            for download_info in download_lists:
                database = download_info['database']
                total_count = download_info['total_count']
                
                print(f"\n正在下载数据库: {database}")
                
                # 重新搜索获取webenv和query_key（因为可能已过期）
                count, webenv, query_key = search_database(database)
                
                if count > 0 and webenv and query_key:
                    # 下载数据
                    downloaded_count = download_database_data(database, count, webenv, query_key)
                    search_summary.append((database, count, downloaded_count))
                else:
                    print(f"  重新搜索 {database} 失败，跳过下载")
                
                time.sleep(0.3)
        else:
            print("用户选择不下载完整数据，程序结束。")
            return
    
    # 7. 输出搜索摘要
    print("\n" + "="*60)
    print("搜索完成！汇总结果:")
    print("="*60)
    
    if search_summary:
        total_found = 0
        total_downloaded = 0
        print(f"{'数据库':20s} {'找到':>10s} {'下载':>10s}")
        print("-" * 45)
        
        for database, found_count, downloaded_count in search_summary:
            print(f"{database:20s}: {found_count:>8,} / {downloaded_count:>8,} 条记录")
            total_found += found_count
            total_downloaded += downloaded_count
        
        print("-" * 45)
        print(f"{'总计':20s}: {total_found:>8,} / {total_downloaded:>8,} 条记录")
        print(f"\n有数据的数据库数量: {len(search_summary)} 个")
        print(f"总共下载: {total_downloaded:,} 条记录，占找到记录的 {(total_downloaded/total_found*100):.1f}%")
        
        # 保存搜索摘要
        summary_file = os.path.join(output_dir, "search_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Endolysin 搜索结果摘要\n")
            f.write(f"搜索时间: {datetime.now()}\n")
            f.write(f"配置: 每个数据库最多下载 {MAX_RECORDS_PER_DATABASE} 条记录\n")
            f.write("="*60 + "\n\n")
            f.write(f"{'数据库':20s} {'找到记录数':>12s} {'下载记录数':>12s} {'下载比例':>10s}\n")
            f.write("-" * 60 + "\n")
            
            for database, found_count, downloaded_count in search_summary:
                percentage = (downloaded_count/found_count*100) if found_count > 0 else 0
                f.write(f"{database:20s}: {found_count:>10,} / {downloaded_count:>10,} ({percentage:>6.1f}%)\n")
            
            f.write("-" * 60 + "\n")
            f.write(f"{'总计':20s}: {total_found:>10,} / {total_downloaded:>10,} ({(total_downloaded/total_found*100):>6.1f}%)\n")
            f.write(f"\n有数据的数据库数量: {len(search_summary)} 个\n")
        
        print(f"\n搜索摘要已保存到: {summary_file}")
    else:
        print("所有数据库中都未找到 endolysin 相关数据")
    
    print(f"\n所有数据已保存到目录: {output_dir}")

if __name__ == "__main__":
    main()

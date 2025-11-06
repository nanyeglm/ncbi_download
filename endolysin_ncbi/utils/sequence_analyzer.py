"""
序列分析工具：从 GenBank 文件中提取序列、去重、生成分析报告
优化版本：先合并所有 .gbk 文件，再统一处理
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple, Iterator, Optional
import re
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
import math
import statistics
from tqdm import tqdm

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class SequenceAnalyzer:
    """序列分析器：提取、去重、统计（优化版本）"""

    def __init__(self, gbk_dir: Path, merged_file: Optional[Path] = None):
        """初始化分析器

        Args:
            gbk_dir: GenBank 文件目录
            merged_file: 合并后的文件路径（可选，默认在 gbk_dir 同级创建）
        """
        self.gbk_dir = Path(gbk_dir)
        if merged_file is None:
            self.merged_file = self.gbk_dir.parent / 'merged_protein_sequences.gbk'
        else:
            self.merged_file = Path(merged_file)

        # 序列 → [ACCESSION ID 列表]
        self.seq_to_accessions: Dict[str, List[str]] = defaultdict(list)
        # ACCESSION ID → 序列
        self.accession_to_seq: Dict[str, str] = {}
        # 统计信息
        self.stats = {
            'total_files': 0,
            'valid_files': 0,
            'unique_sequences': 0,
            'total_accessions': 0,
            'duplicated_sequences': 0,
            'max_duplicates': 0,
            'sequence_lengths': [],
            'merged_file_size': 0,
        }

    def merge_gbk_files(self) -> int:
        """将所有 .gbk 文件合并成一个文件

        Returns:
            合并的文件数量
        """
        gbk_files = list(self.gbk_dir.glob('*.gbk'))
        self.stats['total_files'] = len(gbk_files)

        if not gbk_files:
            print(f"警告：在 {self.gbk_dir} 中未找到 .gbk 文件")
            return 0

        print(f"开始合并 {len(gbk_files)} 个 .gbk 文件到 {self.merged_file}")

        merged_count = 0
        with open(self.merged_file, 'w', encoding='utf-8') as outfile:
            for gbk_file in tqdm(gbk_files, desc="合并文件", unit="file"):
                try:
                    with open(gbk_file, 'r', encoding='utf-8') as infile:
                        # 写入分隔符（便于后续解析）
                        if merged_count > 0:
                            outfile.write('\n//\n\n')
                        outfile.write(f"# MERGED_FROM: {gbk_file.name}\n")
                        outfile.write(infile.read())
                        merged_count += 1
                except Exception as e:
                    print(f"合并文件 {gbk_file.name} 时出错: {e}")

        self.stats['merged_file_size'] = self.merged_file.stat().st_size
        print(
            f"合并完成：{merged_count} 个文件，总大小: {self.stats['merged_file_size']} 字节")
        return merged_count

    def parse_merged_file(self) -> Iterator[Tuple[str, str]]:
        """从合并文件中解析每个记录的 ACCESSION 和序列

        Yields:
            (accession_id, sequence) 元组
        """
        if not self.merged_file.exists():
            raise FileNotFoundError(f"合并文件不存在: {self.merged_file}")

        current_accession = ''
        current_sequence = ''
        in_origin = False
        record_started = False

        with open(self.merged_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # 跳过合并标记行
                if line.startswith('# MERGED_FROM:'):
                    continue

                # 检测记录开始（LOCUS 行）
                if line.startswith('LOCUS'):
                    # 如果之前有完整记录，先yield
                    if record_started and current_accession and current_sequence:
                        yield current_accession, current_sequence.upper()

                    # 重置当前记录
                    current_accession = ''
                    current_sequence = ''
                    in_origin = False
                    record_started = True

                # 提取 ACCESSION
                elif line.startswith('ACCESSION'):
                    parts = line.split()
                    if len(parts) >= 2:
                        current_accession = parts[1].strip()

                # 检测 ORIGIN 开始
                elif line.startswith('ORIGIN'):
                    in_origin = True

                # 提取序列（在 ORIGIN 段内）
                elif in_origin and line and not line.startswith('//'):
                    # 移除行号和空格，只保留字母字符
                    seq_part = ''.join(c for c in line if c.isalpha())
                    current_sequence += seq_part

                # 检测记录结束
                elif line == '//':
                    in_origin = False
                    # 如果当前记录完整，yield
                    if current_accession and current_sequence:
                        yield current_accession, current_sequence.upper()
                        current_accession = ''
                        current_sequence = ''
                        record_started = False

        # 处理最后一个记录
        if current_accession and current_sequence:
            yield current_accession, current_sequence.upper()

    def process_merged_file(self):
        """处理合并文件中的所有记录"""
        if not self.merged_file.exists():
            print(f"合并文件不存在，先执行合并...")
            self.merge_gbk_files()

        print(f"开始解析合并文件: {self.merged_file}")

        # 先计算总记录数（用于进度条）
        total_records = 0
        with open(self.merged_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('LOCUS'):
                    total_records += 1

        valid_count = 0
        with tqdm(total=total_records, desc="解析记录", unit="record") as pbar:
            for accession, sequence in self.parse_merged_file():
                if accession and sequence:
                    self.stats['valid_files'] += 1
                    self.stats['sequence_lengths'].append(len(sequence))

                    # 记录序列与 ACCESSION 的对应关系
                    self.seq_to_accessions[sequence].append(accession)
                    self.accession_to_seq[accession] = sequence
                    valid_count += 1

                pbar.update(1)

        # 更新统计信息
        self.stats['unique_sequences'] = len(self.seq_to_accessions)
        self.stats['total_accessions'] = len(self.accession_to_seq)
        self.stats['duplicated_sequences'] = sum(
            1 for acc_list in self.seq_to_accessions.values() if len(acc_list) > 1)
        if self.seq_to_accessions:
            self.stats['max_duplicates'] = max(
                len(acc_list) for acc_list in self.seq_to_accessions.values())
        else:
            self.stats['max_duplicates'] = 0

        print(f"解析完成：{valid_count} 个有效记录")

    def split_merged_file(self, output_dir: Path) -> int:
        """将合并文件拆分成独立的 .gbk 文件

        Args:
            output_dir: 输出目录

        Returns:
            拆分的文件数量
        """
        if not self.merged_file.exists():
            print(f"合并文件不存在: {self.merged_file}")
            return 0

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"开始拆分合并文件到: {output_dir}")

        current_record = []
        current_filename = None
        split_count = 0

        with open(self.merged_file, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="拆分文件", unit="line"):
                # 跳过合并标记行
                if line.startswith('# MERGED_FROM:'):
                    continue

                # 检测记录开始（LOCUS 行）
                if line.startswith('LOCUS'):
                    # 如果之前有完整记录，保存文件
                    if current_record and current_filename:
                        output_file = output_dir / f"{current_filename}.gbk"
                        with open(output_file, 'w', encoding='utf-8') as outfile:
                            outfile.writelines(current_record)
                        split_count += 1

                    # 重置当前记录
                    current_record = [line]
                    current_filename = None

                # 提取 ACCESSION 用于文件名
                elif line.startswith('ACCESSION') and not current_filename:
                    parts = line.split()
                    if len(parts) >= 2:
                        current_filename = parts[1].strip()
                    current_record.append(line)

                # 检测记录结束
                elif line.strip() == '//':
                    current_record.append(line)
                    # 保存当前记录
                    if current_record and current_filename:
                        output_file = output_dir / f"{current_filename}.gbk"
                        with open(output_file, 'w', encoding='utf-8') as outfile:
                            outfile.writelines(current_record)
                        split_count += 1

                    # 重置
                    current_record = []
                    current_filename = None

                else:
                    # 添加到当前记录
                    if current_record:
                        current_record.append(line)

        # 处理最后一个记录
        if current_record and current_filename:
            output_file = output_dir / f"{current_filename}.gbk"
            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.writelines(current_record)
            split_count += 1

        print(f"拆分完成：{split_count} 个独立文件")
        return split_count

    @staticmethod
    def _percentiles(sorted_vals: List[int], probs: List[float]) -> List[float]:
        """计算给定有序数组的分位数（线性插值）。
        Args:
            sorted_vals: 已排序的数值列表
            probs: 介于 [0,1] 的分位点列表
        Returns:
            各分位数对应的数值列表
        """
        n = len(sorted_vals)
        if n == 0:
            return [float('nan')] * len(probs)
        results: List[float] = []
        for p in probs:
            if p <= 0:
                results.append(float(sorted_vals[0]))
                continue
            if p >= 1:
                results.append(float(sorted_vals[-1]))
                continue
            pos = (n - 1) * p
            lo = math.floor(pos)
            hi = math.ceil(pos)
            if lo == hi:
                results.append(float(sorted_vals[lo]))
            else:
                frac = pos - lo
                results.append(sorted_vals[lo] *
                               (1 - frac) + sorted_vals[hi] * frac)
        return results

    @staticmethod
    def _build_fixed_bins(lengths: List[int]) -> List[Tuple[str, int, float]]:
        """固定分箱直方图。
        返回 [区间标签, 计数, 占比] 列表。
        """
        if not lengths:
            return []
        bins = [0, 50, 100, 150, 200, 250, 300, 400,
                500, 750, 1000, 1500, 2000, 3000, 4000, 5000]
        labels: List[str] = []
        counts: List[int] = []
        total = len(lengths)
        for i in range(len(bins) - 1):
            start, end = bins[i], bins[i + 1]
            labels.append(f"[{start},{end})")
            c = sum(1 for x in lengths if start <= x < end)
            counts.append(c)
        # 5000+
        labels.append("[5000,+∞)")
        counts.append(sum(1 for x in lengths if x >= 5000))
        return [(labels[i], counts[i], counts[i] * 100.0 / total) for i in range(len(labels))]

    @staticmethod
    def _build_fd_bins(lengths: List[int], max_bins: int = 60) -> List[Tuple[int, int, int]]:
        """Freedman–Diaconis 规则自适应分箱，返回 [start, end, count] 列表。
        为避免报告过大，最多分为 max_bins 个箱。
        """
        if not lengths:
            return []
        sorted_vals = sorted(lengths)
        n = len(sorted_vals)
        q1, q3 = SequenceAnalyzer._percentiles(sorted_vals, [0.25, 0.75])
        iqr = max(q3 - q1, 0.0)
        data_min, data_max = sorted_vals[0], sorted_vals[-1]
        if iqr > 0:
            h = 2.0 * iqr / (n ** (1.0 / 3.0))
        else:
            # 回退：使用 sqrt(n) 箱数
            desired_bins = max(1, int(math.sqrt(n)))
            h = max(1.0, (data_max - data_min) /
                    desired_bins if data_max > data_min else 1.0)
        if h <= 0:
            h = 1.0
        bins_count = int(math.ceil((data_max - data_min) / h)
                         ) if data_max > data_min else 1
        if bins_count > max_bins:
            bins_count = max_bins
            h = max(1.0, (data_max - data_min) /
                    bins_count if data_max > data_min else 1.0)
        edges = [int(math.floor(data_min + i * h)) for i in range(bins_count)]
        edges.append(int(math.ceil(data_max)))
        # 统计计数
        counts = [0] * bins_count
        j = 0
        for x in sorted_vals:
            # 找到 x 所属的 bin（线性推进）
            while j < bins_count - 1 and x >= edges[j + 1]:
                j += 1
            counts[j] += 1
        return [(edges[i], edges[i + 1], counts[i]) for i in range(bins_count)]

    def _write_length_stats(self, f, lengths: List[int]):
        """写入序列长度的统计学分析到打开的文件对象 f。"""
        if not lengths:
            f.write("无序列长度数据\n")
            return
        n = len(lengths)
        sorted_vals = sorted(lengths)
        mean_val = sum(lengths) / n
        median_val = statistics.median(sorted_vals)
        var_val = statistics.variance(lengths) if n > 1 else 0.0
        std_val = math.sqrt(var_val)
        p5, p10, p25, p50, p75, p90, p95, p99 = self._percentiles(
            sorted_vals, [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
        )
        iqr = p75 - p25
        mild_low, mild_high = p25 - 1.5 * iqr, p75 + 1.5 * iqr
        extreme_low, extreme_high = p25 - 3 * iqr, p75 + 3 * iqr
        mild_outliers = sum(1 for x in lengths if x <
                            mild_low or x > mild_high)
        extreme_outliers = sum(1 for x in lengths if x <
                               extreme_low or x > extreme_high)
        # 去除温和异常值后的均值/标准差
        trimmed = [x for x in lengths if mild_low <=
                   x <= mild_high] if iqr > 0 else lengths
        trimmed_mean = (sum(trimmed) / len(trimmed)) if trimmed else mean_val
        trimmed_std = (statistics.stdev(trimmed) if len(
            trimmed) > 1 else 0.0) if trimmed else std_val
        # 95% 置信区间（均值）
        se = std_val / math.sqrt(n) if n > 0 else 0.0
        ci_low = mean_val - 1.96 * se
        ci_high = mean_val + 1.96 * se

        f.write("## 序列长度分布（统计学分析）\n\n")
        f.write(f"- 样本量 n: {n}\n")
        f.write(f"- 均值: {mean_val:.3f} aa\n")
        f.write(f"- 中位数: {median_val:.3f} aa\n")
        f.write(f"- 方差: {var_val:.3f}\n")
        f.write(f"- 标准差: {std_val:.3f}\n")
        f.write(f"- 95% 置信区间(均值): [{ci_low:.3f}, {ci_high:.3f}]\n")
        f.write(
            f"- 分位数: P5={p5:.1f}, P10={p10:.1f}, P25(Q1)={p25:.1f}, P50(Q2)={p50:.1f}, P75(Q3)={p75:.1f}, P90={p90:.1f}, P95={p95:.1f}, P99={p99:.1f}\n")
        f.write(
            f"- 四分位距(IQR): {iqr:.1f} (Tukey篱笆: mild [{mild_low:.1f}, {mild_high:.1f}], extreme [{extreme_low:.1f}, {extreme_high:.1f}])\n")
        f.write(f"- 温和异常值数: {mild_outliers} ({mild_outliers*100.0/n:.2f}%)\n")
        f.write(
            f"- 极端异常值数: {extreme_outliers} ({extreme_outliers*100.0/n:.2f}%)\n")
        f.write(
            f"- 去除温和异常值后的均值: {trimmed_mean:.3f} aa, 标准差: {trimmed_std:.3f}\n\n")

        # 固定分箱直方图
        f.write("### 长度直方图（固定分箱）\n\n")
        fixed_bins = self._build_fixed_bins(lengths)
        f.write("区间\t数量\t占比(%)\n")
        for label, count, pct in fixed_bins:
            f.write(f"{label}\t{count}\t{pct:.2f}\n")
        f.write("\n")

        # 自适应分箱直方图（FD）
        f.write("### 长度直方图（Freedman–Diaconis 自适应分箱，最多 60 箱）\n\n")
        fd_bins = self._build_fd_bins(lengths, max_bins=60)
        f.write("区间\t数量\n")
        for start, end, count in fd_bins:
            f.write(f"[{start},{end})\t{count}\n")
        f.write("\n")

    def save_sequence_mapping(self, output_file: Path):
        """保存序列与 ACCESSION 的对应关系到 CSV

        Args:
            output_file: 输出 CSV 文件路径
        """
        # 找出最大重复数，用于确定 CSV 列数
        max_duplicates = self.stats['max_duplicates']
        headers = ['Sequence'] + \
            [f'ACCESSION_{i+1}' for i in range(max_duplicates)]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for sequence, accessions in self.seq_to_accessions.items():
                # 序列写成 FASTA 格式（每60个字符换行）
                fasta_seq = '\n'.join(sequence[i:i+60]
                                      for i in range(0, len(sequence), 60))
                # 补齐 ACCESSION 列（可能有些序列的重复数少于最大值）
                row = [fasta_seq] + accessions + [''] * \
                    (max_duplicates - len(accessions))
                writer.writerow(row)

    def save_statistics(self, output_file: Path):
        """保存统计报告

        Args:
            output_file: 输出报告文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Endolysin 序列分析报告\n")
            f.write(f"生成时间: {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")

            f.write("## 基本统计\n\n")
            f.write(f"- 总文件数: {self.stats['total_files']}\n")
            f.write(f"- 有效文件数: {self.stats['valid_files']}\n")
            f.write(f"- 合并文件大小: {self.stats['merged_file_size']} 字节\n")
            f.write(f"- 唯一序列数: {self.stats['unique_sequences']}\n")
            f.write(f"- 总 ACCESSION 数: {self.stats['total_accessions']}\n")
            f.write(f"- 重复序列数: {self.stats['duplicated_sequences']}\n")
            f.write(f"- 最大重复数: {self.stats['max_duplicates']}\n\n")

            if self.stats['sequence_lengths']:
                lengths = self.stats['sequence_lengths']
                f.write("## 序列长度统计\n\n")
                f.write(f"- 最短序列: {min(lengths)} aa\n")
                f.write(f"- 最长序列: {max(lengths)} aa\n")
                f.write(f"- 平均长度: {sum(lengths)/len(lengths):.1f} aa\n\n")
                # 追加详细统计分析
                self._write_length_stats(f, lengths)

            if self.stats['duplicated_sequences'] > 0:
                f.write("## 重复序列分布\n\n")
                duplicates_count = defaultdict(int)
                for accessions in self.seq_to_accessions.values():
                    duplicates_count[len(accessions)] += 1

                f.write("重复数\t序列数\n")
                for dup_count in sorted(duplicates_count.keys()):
                    f.write(f"{dup_count}\t{duplicates_count[dup_count]}\n")


def main():
    """主函数"""
    # 输入输出路径（相对项目根目录）
    protein_dir = PROJECT_ROOT / 'endolysin_data' / 'protein'
    output_dir = PROJECT_ROOT / 'endolysin_data' / 'analysis'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"输入目录: {protein_dir}")
    print(f"输出目录: {output_dir}")

    # 创建分析器并处理
    analyzer = SequenceAnalyzer(protein_dir)
    print("\n开始分析序列...")

    # 步骤1：合并所有 .gbk 文件
    print("\n步骤1：合并 .gbk 文件...")
    merged_count = analyzer.merge_gbk_files()

    # 步骤2：从合并文件解析序列
    print("\n步骤2：解析合并文件...")
    analyzer.process_merged_file()

    # 保存结果
    analyzer.save_sequence_mapping(output_dir / 'sequence_mapping.csv')
    analyzer.save_statistics(output_dir / 'sequence_statistics.txt')
    print(f"\n分析完成。结果已保存到: {output_dir}")
    print(f"合并文件位置: {analyzer.merged_file}")

    # 步骤3：询问是否需要拆分文件
    print("\n" + "="*60)
    print("分析完成！")
    print("="*60)

    while True:
        user_input = input("\n是否需要将合并文件拆分成独立的 .gbk 文件？(y/n): ").strip().lower()
        if user_input in ['y', 'yes', '是']:
            split_dir = PROJECT_ROOT / 'endolysin_data' / 'split_proteins'
            split_count = analyzer.split_merged_file(split_dir)
            print(f"拆分完成！{split_count} 个独立文件已保存到: {split_dir}")
            break
        elif user_input in ['n', 'no', '否']:
            print("跳过文件拆分。")
            break
        else:
            print("请输入 y/yes/是 或 n/no/否")


if __name__ == '__main__':
    main()

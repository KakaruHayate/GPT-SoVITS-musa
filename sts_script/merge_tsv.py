import sys

def merge_tsv(output_path, input_paths):
    """
    按顺序合并多个TSV文件到输出文件
    :param output_path: 输出文件路径
    :param input_paths: 输入文件路径列表（按合并顺序）
    """
    header_written = False
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for i, path in enumerate(input_paths):
            try:
                with open(path, 'r', encoding='utf-8') as infile:
                    # 读取首行作为表头
                    header = next(infile, None)
                    
                    if header is None:
                        print(f"跳过空文件: {path}")
                        continue
                    
                    # 如果是第一个文件，写入表头
                    if not header_written:
                        outfile.write(header)
                        header_written = True
                    
                    # 写入文件内容（如果是后续文件则跳过表头）
                    for line in infile:
                        outfile.write(line)
                    
                    print(f"已合并: {path} ({'包含表头' if i == 0 else '跳过表头'})")
            
            except FileNotFoundError:
                print(f"错误: 文件未找到 - {path}")
                sys.exit(1)
    
    print(f"\n合并完成! 共处理 {len(input_paths)} 个文件")
    print(f"输出文件: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python merge_tsv.py 输出文件.tsv 输入文件1.tsv [输入文件2.tsv ...]")
        print("示例: python merge_tsv.py merged.tsv data1.tsv data2.tsv data3.tsv")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    merge_tsv(output_file, input_files)
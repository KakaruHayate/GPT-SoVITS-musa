import csv
import os

# --- 配置区 ---

# 输入文件名
input_file = 'G:\\GPT-SoVITS-v2-240821\\logs\\data_transfer_ja\\6-name2semantic.tsv'
# 输出文件名
output_file = 'G:\\GPT-SoVITS-v2-240821\\logs\\data_transfer_ja\\pair_6-name2semantic.tsv'

# 用于标识“源”语义的关键字
SOURCE_IDENTIFIER = 'Paired_Speech_Group'

# 文件名中可能出现的所有“组类型”标识符
# !!重要!!: 如果您的数据中还有其他类似的组类型 (如 'Normal_Group', 'Whisper_Group' 等),
# 请务必将它们也添加到这个列表中，以便脚本能够正确识别配对。
POSSIBLE_GROUP_TYPES = [
    'Paired_Speech_Group',
    'Breathy_Group',
    'Control_Group',
    'Glissando_Group',
    'Falsetto_Group',
    'Mixed_Voice_Group',
    'Pharyngeal_Group',
    'Vibrato_Group'
]

# --- 脚本区 ---

def get_pair_key(filename, group_types):
    """
    通过移除文件名中的组类型部分来生成一个唯一的配对键。
    例如:
    'file_Paired_Speech_Group_01.wav' -> 'file_###PLACEHOLDER###_01.wav'
    'file_Breathy_Group_01.wav'       -> 'file_###PLACEHOLDER###_01.wav'
    这样它们就有了相同的键。
    """
    for group_type in group_types:
        if group_type in filename:
            # 用一个固定的占位符替换组类型，得到唯一的key
            return filename.replace(group_type, '###PLACEHOLDER###')
    # 如果文件名中不包含任何已知的组类型，则它不成对
    return None

def process_semantic_data(input_path, output_path):
    """
    处理语义数据，用源语义覆盖配对的目标语义。
    """
    if not os.path.exists(input_path):
        print(f"错误：输入文件 '{input_path}' 不存在。")
        return

    # 1. 第一遍：读取所有数据，并建立源语义的映射
    print("第一步：读取数据并寻找源语义...")
    source_semantics = {}
    all_data = []

    with open(input_path, 'r', encoding='utf-8') as infile:
        # 使用 csv.reader 并指定制表符为分隔符
        reader = csv.reader(infile, delimiter='\t')
        
        # 读取表头
        header = next(reader)
        all_data.append(header)

        # 临时存储数据行
        data_rows = list(reader)

    for row in data_rows:
        if len(row) < 2:
            continue # 跳过格式不正确的行
        item_name, semantic_audio = row
        
        # 将原始数据行（文件名和语义）添加到 all_data 供后续处理
        all_data.append([item_name, semantic_audio])
        
        # 如果这是源文件 (Paired_Speech_Group)
        if SOURCE_IDENTIFIER in item_name:
            pair_key = get_pair_key(item_name, POSSIBLE_GROUP_TYPES)
            if pair_key:
                source_semantics[pair_key] = semantic_audio
                print(f"  找到源: {item_name[:30]}... -> key: {pair_key[:30]}...")

    print(f"\n找到了 {len(source_semantics)} 个源语义。")

    # 2. 第二遍：遍历所有数据，用源语义进行覆盖
    print("\n第二步：用源语义覆盖配对数据...")
    processed_count = 0
    final_data = []
    final_data.append(all_data[0]) # 添加表头

    # 从第二行开始遍历 (跳过表头)
    for i in range(1, len(all_data)):
        item_name, original_semantic = all_data[i]
        
        pair_key = get_pair_key(item_name, POSSIBLE_GROUP_TYPES)
        
        # 如果该文件的配对键在我们的源语义字典中
        if pair_key and pair_key in source_semantics:
            # 使用源语义替换当前语义
            new_semantic = source_semantics[pair_key]
            final_data.append([item_name, new_semantic])
            if original_semantic != new_semantic:
                processed_count += 1
                print(f"  已处理: {item_name[:40]}...")
        else:
            # 如果没有找到配对，或者它本身就是不成对的文件，则保留原样
            final_data.append([item_name, original_semantic])

    print(f"\n总共覆盖了 {processed_count} 行数据的语义。")

    # 3. 写入新文件
    print(f"\n第三步：将结果写入 '{output_path}'...")
    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        writer.writerows(final_data)

    print("\n处理完成！")


# --- 主程序入口 ---
if __name__ == '__main__':
    # 确保输入文件存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 未找到。")
        print("请创建一个名为 'your_data.tsv' 的文件，并将您的数据粘贴进去，或者修改脚本中的 `input_file`变量。")
        # 为方便测试，创建一个示例文件
        print("正在为您创建一个示例输入文件 'your_data.tsv'...")
        sample_data = """item_name	semantic_audio
Korean_KO-Soprano-1_Breathy_all about you_Breathy_Group_0000.wav	582 515 752 509 404 404 509 515 404 404 278 748 203 260 29 739 33 807 228 159 484 484 866 352 235 888 249 241 241 241 866 698 988 800 84 1010 1010 968 990 968 968 968 816 931 585 888 888 888 888 996 209 495 495 495 685 703 896 159 791 291 865 791 865 109 239 405 33 905 882 755 586 86 534 1023 835 954 108 108 901 519 564 564 564 564 108 822 766 21 901 822 822 21 374 658 564 564 564 577 294 577 500 441 967 921 748 748 366 366 544 634 278 127 52 80 184 541 17 1001 946 692 712 710 952 303 2 669 613 613 563 480 569 538 608 1014 826 256 756 698 888 383 484 150 528 176 590 710 789 790 84 84 564 502 779 285 881 881 983 965 178 724 744 989 285 630 903 832 630 630 630 630 630 630 630 883 835 835 835 106 106 835 835 100 881 630 955 244 832 832 832 646 832 832 516 75 668 729 475 475 475 145 638
Korean_KO-Soprano-1_Breathy_all about you_Paired_Speech_Group_0000.wav	194 760 162 507 507 441 65 32 32 32 515 509 404 404 382 463 930 243 930 581 581 581 565 103 574 98 937 146 340 762 291 922 215 454 322 971 922 922 922 922 174 674 726 29 148 390 1007 97 219 659 152 905 466 983 246 438 438 1003 513 363 759 759 632 111 1023 387 700 777 777 478 910 916 775 967 804 17 804 242 451 714 540 277 740 846 987 987 851 679 992 462 932 481 984 126 682 521 328 856 690 229 742 533 148 442 935 374 439 1013 649 439 439 411 151 970 659 700 777 777 948 623 530 930 593 5 910 142 357 214 54 875 357 405 260 357 524 214 318
"""
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(sample_data)
    else:
        process_semantic_data(input_file, output_file)
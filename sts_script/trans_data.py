# -*- coding: utf-8 -*-

import os
import json
import shutil
from pathlib import Path
import argparse
from tqdm import tqdm

# --- 配置区 ---

# 定义语言名称到语言标签的映射关系
LANG_MAP = {
    'Chinese': 'ZH',
    'English': 'EN',
    'Japanese': 'JA',
    'Korean': 'KR'
}

# 定义包含源文本信息的特定组名
TEXT_SOURCE_GROUP = 'Paired_Speech_Group'

# 定义需要从文本中过滤掉的特殊标记
SPECIAL_TOKENS = {"<SP>", "<AP>"}

# --- 核心功能函数 ---

def extract_text_from_json(json_path, lang_name):
    """
    从给定的 JSON 文件中读取内容，并根据语言规则提取拼接好的文本。

    Args:
        json_path (Path): JSON 文件的路径对象。
        lang_name (str): 语言名称，如 'English', 'Chinese'。

    Returns:
        str: 拼接好的文本字符串。如果文件不存在或解析失败，返回 None。
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        words = []
        for item in data:
            word = item.get('word', '')
            if word not in SPECIAL_TOKENS:
                words.append(word)
        
        separator = " " if lang_name == 'English' else ""
        return separator.join(words)
        
    except FileNotFoundError:
        # 这个警告现在很重要，因为每个文件都可能缺少对应的json
        # print(f"警告：未找到对应的 JSON 文件：{json_path}") # 在主循环中处理警告信息更清晰
        return None
    except json.JSONDecodeError:
        print(f"警告：JSON 文件格式错误，无法解析：{json_path}")
        return None
    except Exception as e:
        print(f"警告：处理 JSON 文件 {json_path} 时发生未知错误：{e}")
        return None


def process_files(input_path, output_path):
    """
    主处理函数，执行文件整理和 .list 文件生成。

    Args:
        input_path (str): 输入目录的路径。
        output_path (str): 输出目录的路径。
    """
    input_dir = Path(input_path)
    output_dir = Path(output_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"输出目录 '{output_dir.resolve()}' 已准备就绪。")

    print("正在扫描输入目录以查找 .wav 文件...")
    wav_files = list(input_dir.rglob('*.wav'))
    
    if not wav_files:
        print("错误：在输入目录中没有找到任何 .wav 文件。请检查路径和文件结构。")
        return

    print(f"扫描完成，共找到 {len(wav_files)} 个 .wav 文件。")

    list_file_content = []

    for wav_path in tqdm(wav_files, desc="正在处理文件"):
        try:
            # --- 1. 解析路径，提取信息 ---
            parts = wav_path.parts
            base_parts = input_dir.parts
            relative_parts = parts[len(base_parts):]

            lang_name, spk_name, tech_name, song_name, group_name = relative_parts[:-1]
            original_file_name = wav_path.stem

            # --- 2. 复制并重命名 WAV 文件 ---
            new_file_name = f"{lang_name}_{spk_name}_{tech_name}_{song_name}_{group_name}_{original_file_name}.wav"
            destination_path = output_dir / new_file_name
            shutil.copy2(wav_path, destination_path)

            # --- 3. 【修正逻辑】为每个 WAV 文件独立查找其对应的 JSON 文件 ---
            # 移除了错误的缓存机制。
            
            # 构造包含源文本的 JSON 文件所在的目录
            # 例如: G:/input/Chinese/ZH-Alto-1/Breathy/不再见/Paired_Speech_Group
            text_source_dir = wav_path.parent.parent / TEXT_SOURCE_GROUP
            
            # 构造对应的 JSON 文件路径，文件名与当前处理的 wav 文件名相同
            # 例如: .../Paired_Speech_Group/0001.json
            json_path_for_text = text_source_dir / f"{original_file_name}.json"

            # 从对应的 JSON 文件中提取文本
            text = extract_text_from_json(json_path_for_text, lang_name)
            
            # 如果提取失败（例如，json文件不存在），则文本为空字符串
            if text is None:
                text = ""
                # 打印一个更精确的警告
                tqdm.write(f"警告：未找到文件 '{wav_path.name}' 对应的JSON '{json_path_for_text.name}'。将在list文件中使用空文本。")

            # --- 4. 准备 .list 文件的一行 ---
            lang_tag = LANG_MAP.get(lang_name, "UNKNOWN")
            if lang_tag == "UNKNOWN":
                tqdm.write(f"警告：在 LANG_MAP 中未找到语言 '{lang_name}' 的映射，将使用 'UNKNOWN'。")

            abs_wav_path = destination_path.resolve().as_posix()
            line = f"{abs_wav_path}|{spk_name}|{lang_tag}|{text}"
            list_file_content.append(line)

        except (ValueError, IndexError):
            tqdm.write(f"\n警告：文件路径 '{wav_path}' 的结构不符合预期。已跳过此文件。")
            tqdm.write("预期结构: .../<lang_name>/<spk_name>/<tech_name>/<song_name>/<group_name>/*.wav")
            continue

    if list_file_content:
        list_file_path = output_dir / 'output.list'
        print(f"\n正在生成 list 文件到: {list_file_path.resolve()}")
        
        list_file_content.sort()
        
        with open(list_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(list_file_content))
        
        print("处理完成！")
    else:
        print("\n没有成功处理任何文件，未生成 .list 文件。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="整理音频文件并生成一个符合规则的 .list 文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_path", 
        type=str, 
        help="包含源文件的根目录路径。\n"
             "例如: G:\\data\\input"
    )
    parser.add_argument(
        "output_path", 
        type=str, 
        help="用于存放重命名后的 .wav 文件和 output.list 文件的目录路径。\n"
             "例如: D:\\processed_audio"
    )

    args = parser.parse_args()
    process_files(args.input_path, args.output_path)
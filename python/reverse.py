#!/usr/bin/env python3
"""
脚本用于处理包含5x5数据块的文件。
当匹配到template_5x5时，会查找values块，并对5x5矩阵进行翻转处理。
"""

import sys
import re

def flip_7x7_data(data_lines):
    """
    翻转7x7数据矩阵
    输入: 包含7行数据的列表，每行格式如: "0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7"
    输出: 翻转后的7行数据列表
    """
    # 清理每行数据：去除引号、空格等
    cleaned_data = []
    for line in data_lines:
        # 去除行首尾的引号、反斜杠、空格等
        line = line.replace(');', '')  # 去除反斜杠
        clean_line = line.strip().strip('", \\')
        # 分割数字
        numbers = [num.strip() for num in clean_line.split(',')]
        cleaned_data.append(numbers)
    
    # 1. 上下翻转行
    flipped_rows = cleaned_data[::-1]
    
    # 2. 左右翻转每行的数字
    fully_flipped = []
    for row in flipped_rows:
        fully_flipped.append(row[::-1])
    
    # 构建输出行
    output_lines = []
    for i, row in enumerate(fully_flipped):
        line_content = '"' + ', '.join(row) + '"'
        if i < 6:  # 前6行
            line_content += ', \\'
        else:      # 最后一行
            line_content += ');'
        output_lines.append(line_content)
    
    return output_lines

def process_file(input_file):
    """
    处理文件的主要函数
    """
    mode = "normal"  # normal, waiting, flip
    template_found = False
    values_found = False
    values_indent = ""
    data_lines = []
    line_count = 0
    
    for line in input_file:
        line = line.rstrip('\n')
        
        if mode == "normal":
            # 检查是否匹配到template_5x5
            if "template_7x7" in line:
                template_found = True
                mode = "waiting"
                print(line)
                continue
            
            print(line)
        
        elif mode == "waiting":
            # 输出当前行
            print(line)
            
            # 检查是否匹配到values行
            values_match = re.match(r'^(\s*)values\s*\(', line)
            if values_match:
                values_found = True
                values_indent = values_match.group(1)
                mode = "flip"
                line_count = 0
        
        elif mode == "flip":
            # 收集数据行
            line_count += 1
            
            # 检查是否是数据行（包含引号和逗号）
            if '"' in line and ',' in line:
                data_lines.append(line)

            # 如果收集了7行，进行处理
            if line_count >= 7 and len(data_lines) == 7:
                # 翻转数据
                flipped_lines = flip_7x7_data(data_lines)
                
                # 输出翻转后的数据行
                for i, flipped_line in enumerate(flipped_lines):
                    # 保持原始缩进
                    print(f"{values_indent}  {flipped_line}")
                
                # 重置状态
                mode = "normal"
                template_found = False
                values_found = False
                data_lines = []
                line_count = 0

def main():
    """
    主函数
    """
    # 从标准输入读取
    if len(sys.argv) > 1:
        # 从文件读取
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                process_file(f)
        except FileNotFoundError:
            print(f"错误: 文件 '{sys.argv[1]}' 未找到", file=sys.stderr)
            sys.exit(1)
    else:
        # 从标准输入读取
        process_file(sys.stdin)

if __name__ == "__main__":
    main()
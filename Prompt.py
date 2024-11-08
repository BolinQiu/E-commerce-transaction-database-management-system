import os

def collect_code_files(directory, output_file, extensions=None):
    """
    Collects all code files in a directory and writes their content to a single .txt file.

    Parameters:
    - directory (str): The directory to search for code files.
    - output_file (str): The output .txt file to save all code content.
    - extensions (list): List of file extensions to include (e.g., ['.py', '.js']). If None, all files are included.
    """
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Check file extension
                if extensions is None or os.path.splitext(file)[1] in extensions:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        outfile.write(f"===== {file_path} =====\n")
                        outfile.write(infile.read())
                        outfile.write("\n\n")  # Add space between files for readability

    print(f"All code files have been collected in {output_file}")

# 使用示例
directory = "./backend_manage"  # 替换为你的项目路径
output_file = "all_code_files.txt"
extensions = ['.py', '.js', '.html', '.css']  # 设置需要收集的文件类型
collect_code_files(directory, output_file, extensions)

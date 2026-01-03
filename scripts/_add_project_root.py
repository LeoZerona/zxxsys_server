"""
通用工具：添加项目根目录到 Python 路径
在所有脚本的开头导入此模块即可

使用方法：
    from scripts._add_project_root import add_project_root
    add_project_root()
"""
import sys
from pathlib import Path

def add_project_root():
    """添加项目根目录到 Python 路径"""
    # 获取项目根目录（scripts 的父目录）
    project_root = Path(__file__).parent.parent
    project_root_str = str(project_root)
    
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root

# 自动添加（如果直接导入此模块）
if __name__ != '__main__':
    add_project_root()


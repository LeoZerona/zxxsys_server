"""运行测试脚本"""
import subprocess
import sys

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行测试...")
    print("=" * 60)
    
    # 运行 pytest
    result = subprocess.run(
        ['pytest', '-v', '--tb=short'],
        cwd='.',
        capture_output=False
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())


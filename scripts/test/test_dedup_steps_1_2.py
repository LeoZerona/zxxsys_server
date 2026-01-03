"""
测试题目去重服务的步骤1和步骤2
验证清洗题干和秒筛完全一样的题功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.services.question_dedup_service import QuestionDedupService


def test_clean_content():
    """测试清洗题干功能"""
    print("=" * 60)
    print("测试：清洗题干功能")
    print("=" * 60)
    
    test_cases = [
        ("原始内容", "预期结果"),
        ("  ABC  ", "ABC"),  # 去除首尾空格
        ("A  B   C", "A B C"),  # 多个空格合并
        ("[图片1]内容[图片2]", "[IMG]内容[IMG]"),  # 图片占位符标准化
        ("[公式1]内容[公式2]", "[FORMULA]内容[FORMULA]"),  # 公式占位符标准化
        ("<p>HTML标签</p>", "HTML标签"),  # 去除HTML标签
        ("全角ＡＢＣ", "半角ABC"),  # 全角转半角
        ("  [图片1]  测试  ", "[IMG] 测试"),  # 组合测试
    ]
    
    print("\n测试用例：")
    print("-" * 60)
    for original, expected in test_cases[1:]:  # 跳过表头
        cleaned = QuestionDedupService._clean_question_content(original)
        status = "✓" if cleaned == expected else "✗"
        print(f"{status} 原始: {repr(original)}")
        print(f"   清洗: {repr(cleaned)}")
        if cleaned != expected:
            print(f"   预期: {repr(expected)}")
        print()


def test_find_exact_duplicates():
    """测试秒筛完全一样的题功能"""
    print("\n" + "=" * 60)
    print("测试：秒筛完全一样的题功能")
    print("=" * 60)
    
    # 创建测试数据
    from src.models.question import Question
    
    test_questions = [
        {"question_id": 1, "content": "题目A"},
        {"question_id": 2, "content": "题目A"},  # 与1重复
        {"question_id": 3, "content": "  题目A  "},  # 与1重复（空格）
        {"question_id": 4, "content": "题目B"},
        {"question_id": 5, "content": "题目C"},
        {"question_id": 6, "content": "题目C"},  # 与5重复
        {"question_id": 7, "content": "[图片1]题目D"},
        {"question_id": 8, "content": "[图片2]题目D"},  # 与7重复（图片占位符不同）
    ]
    
    # 模拟Question对象
    class MockQuestion:
        def __init__(self, qid, content):
            self.question_id = qid
            self.content = content
    
    mock_questions = [MockQuestion(q['question_id'], q['content']) for q in test_questions]
    
    # 清洗题目
    cleaned = QuestionDedupService._clean_questions(mock_questions)
    print(f"\n清洗后题目数: {len(cleaned)}")
    
    # 查找完全重复
    duplicates = QuestionDedupService._find_exact_duplicates(cleaned)
    print(f"找到完全重复组: {len(duplicates)} 组")
    
    for dup in duplicates:
        print(f"\n重复组 (共 {dup['count']} 题):")
        print(f"  题目ID: {dup['question_ids']}")
        print(f"  相似度: {dup['similarity']}")


def test_process_single_group():
    """测试处理单个分组（使用真实数据）"""
    print("\n" + "=" * 60)
    print("测试：处理单个分组（真实数据）")
    print("=" * 60)
    
    with app.app_context():
        # 重置进度
        QuestionDedupService.reset_progress()
        
        # 处理第一个分组
        results = QuestionDedupService.process_next_group()
        
        if results:
            print(f"\n处理结果:")
            print(f"  分组: {results['group']['type_name']} - {results['group']['subject_name']}")
            print(f"  总题目数: {results['total_questions']}")
            print(f"  完全重复组数: {len(results['exact_duplicates'])}")
            
            # 显示前5个完全重复组
            if results['exact_duplicates']:
                print(f"\n前5个完全重复组:")
                for i, dup in enumerate(results['exact_duplicates'][:5], 1):
                    print(f"  组 {i}: {dup['count']} 题, ID: {dup['question_ids'][:5]}...")
            
            print(f"\n相似重复对数: {len(results['similar_duplicates'])} (待实现)")
        else:
            print("没有找到分组")


if __name__ == '__main__':
    try:
        # 测试清洗功能
        test_clean_content()
        
        # 测试完全重复检测
        test_find_exact_duplicates()
        
        # 测试真实数据处理
        # test_process_single_group()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()


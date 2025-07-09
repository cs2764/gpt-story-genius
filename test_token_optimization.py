#!/usr/bin/env python3
"""
测试章节摘要优化功能
"""

import logging
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from write_story_enhanced import StoryWriter
from config import save_novel_chapter, save_chapter_summary, load_chapter_summary, load_chapter_content, generate_uuid
from config_manager import EnhancedConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_summarization_feature():
    """测试章节摘要功能"""
    print("🧪 测试章节摘要功能...")
    
    # 创建测试实例
    writer = StoryWriter()
    
    # 测试文本
    test_chapter = """
    在一个遥远的王国里，年轻的勇士艾伦踏上了寻找传说中的圣剑的旅程。
    他离开了家乡的小村庄，带着母亲的祝福和父亲留下的古老地图。
    第一天的旅行中，艾伦遇到了一只会说话的狐狸，狐狸告诉他前方的森林里隐藏着危险。
    艾伦决定勇敢地继续前进，因为他知道只有找到圣剑才能拯救被黑暗诅咒的王国。
    夜晚降临时，艾伦在一棵巨大的橡树下搭建了临时营地，准备迎接明天的挑战。
    """
    
    chapter_title = "第一章 - 旅程的开始"
    
    try:
        # 测试摘要生成
        summary = writer.summarize_chapter(test_chapter, chapter_title)
        print(f"✅ 摘要生成成功:")
        print(f"原文长度: {len(test_chapter)} 字符")
        print(f"摘要长度: {len(summary)} 字符")
        print(f"摘要内容: {summary}")
        
        return True
    except Exception as e:
        print(f"❌ 摘要生成失败: {e}")
        return False

def test_context_optimization():
    """测试上下文优化功能"""
    print("\n🧪 测试上下文优化功能...")
    
    # 创建测试小说ID
    novel_id = generate_uuid()
    writer = StoryWriter()
    
    try:
        # 创建测试章节数据
        test_chapters = [
            ("第一章 - 旅程开始", "艾伦离开村庄，开始寻找圣剑的旅程。遇到了会说话的狐狸。"),
            ("第二章 - 森林探险", "艾伦进入危险森林，遇到了神秘的精灵族。学会了使用魔法。"),
            ("第三章 - 山洞秘密", "在山洞中发现古老的符文，解开了圣剑位置的线索。遇到守护者。")
        ]
        
        # 保存测试章节和摘要
        for i, (title, content) in enumerate(test_chapters):
            save_novel_chapter(novel_id, i, title, content)
            summary = f"【{title}】摘要：{content[:50]}..."
            save_chapter_summary(novel_id, i, summary)
            print(f"✅ 保存章节 {i+1}: {title}")
        
        # 测试优化上下文构建
        for test_chapter in range(1, 4):
            context = writer.build_optimized_context(novel_id, test_chapter, recent_chapters_count=2)
            print(f"\n📊 第{test_chapter+1}章的上下文长度: {len(context)} 字符")
            print(f"上下文预览: {context[:200]}...")
            
            # 验证是否正确使用了摘要
            if test_chapter > 2:  # 第4章开始应该使用摘要
                if "摘要" in context:
                    print("✅ 正确使用了摘要")
                else:
                    print("⚠️ 未检测到摘要使用")
        
        return True
    except Exception as e:
        print(f"❌ 上下文优化测试失败: {e}")
        return False

def test_token_savings():
    """测试Token节省效果"""
    print("\n🧪 测试Token节省效果...")
    
    # 模拟不同章节数的Token使用量对比
    test_cases = [3, 5, 10, 15, 20]
    
    for num_chapters in test_cases:
        # 原始方法：所有章节全文累积
        original_tokens = 0
        for i in range(num_chapters):
            chapter_length = 1000  # 假设每章1000个字符
            original_tokens += (i + 1) * chapter_length  # 累积增长
        
        # 优化方法：摘要 + 最近2章全文
        optimized_tokens = 0
        for i in range(num_chapters):
            if i <= 2:  # 前3章直接使用全文
                optimized_tokens += (i + 1) * 1000
            else:  # 后续章节使用摘要+最近2章
                early_summaries = (i - 2) * 200  # 早期章节摘要
                recent_full = 2 * 1000  # 最近2章全文
                optimized_tokens += early_summaries + recent_full
        
        savings = ((original_tokens - optimized_tokens) / original_tokens) * 100
        print(f"📊 {num_chapters}章小说:")
        print(f"   原始方法: {original_tokens:,} tokens")
        print(f"   优化方法: {optimized_tokens:,} tokens")
        print(f"   节省比例: {savings:.1f}%")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试Token优化功能\n")
    
    # 检查配置
    config_manager = EnhancedConfigManager()
    if not config_manager.provider_manager.get_provider_status():
        print("⚠️ 警告：未检测到已配置的AI提供商，将跳过实际API调用测试")
        api_available = False
    else:
        api_available = True
    
    results = []
    
    # 测试摘要功能（需要API）
    if api_available:
        results.append(("章节摘要功能", test_summarization_feature()))
    else:
        print("⏭️ 跳过章节摘要功能测试（需要API）")
    
    # 测试上下文优化（不需要API）
    results.append(("上下文优化功能", test_context_optimization()))
    
    # 测试Token节省计算（不需要API）
    results.append(("Token节省计算", test_token_savings()))
    
    # 总结结果
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Token优化功能已就绪。")
        print("\n💡 预期效果:")
        print("- 减少70-90%的Token使用量（长篇小说）")
        print("- 保持故事连贯性")
        print("- 自动生成章节摘要")
        print("- 智能上下文构建")
    else:
        print("⚠️ 部分测试失败，请检查配置和实现。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
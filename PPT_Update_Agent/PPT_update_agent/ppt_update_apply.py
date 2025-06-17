import json
import argparse
import os
import re
import time
import sys
import win32com.client
import win32com.client.dynamic
import pythoncom
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage

def load_report(report_path):
    """加载更新报告"""
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    return report

def update_ppt(ppt_path, report, model_name="deepseek-reasoner"):
    """根据报告更新PPT
    
    使用PowerPoint COM接口更新PPT内容
    """
    # 初始化COM
    pythoncom.CoInitialize()
    
    try:
        # 初始化大模型
        llm = ChatDeepSeek(model=model_name)
        
        # 创建PowerPoint应用实例
        print("正在启动PowerPoint...")
        ppt_app = win32com.client.Dispatch("PowerPoint.Application")
        # 不设置可见性，保持默认值（PowerPoint不允许隐藏窗口）
        print("PowerPoint已启动，正在进行PPT更新...")
        
        # 打开演示文稿
        print(f"正在打开演示文稿: {ppt_path}")
        presentation = ppt_app.Presentations.Open(os.path.abspath(ppt_path), WithWindow=True)
        
        # 获取需要更新的幻灯片列表
        slides_to_update = report.get('处理的幻灯片', [])
        print(f"将更新以下幻灯片: {slides_to_update}")
        
        # 创建幻灯片编号偏移量字典，用于跟踪幻灯片编号变化
        # 键：原始幻灯片编号，值：偏移量（有多少张幻灯片被添加在此幻灯片之前）
        slide_offset = {slide_num: 0 for slide_num in slides_to_update}
        
        # 按照幻灯片编号排序，确保从前往后处理
        results_by_slide = []
        for result in report.get('结果', []):
            slide_num = result.get('幻灯片')
            if slide_num is not None:
                results_by_slide.append((slide_num, result))
        
        # 按幻灯片编号排序
        results_by_slide.sort(key=lambda x: x[0])
        
        # 处理每个幻灯片
        added_slides = 0  # 跟踪总共添加了多少张幻灯片
        
        for original_slide_num, result in results_by_slide:
            # 计算当前幻灯片的实际编号（考虑之前添加的幻灯片数）
            current_slide_num = original_slide_num + slide_offset[original_slide_num]
            print(f"处理幻灯片 {original_slide_num}（当前实际位置: {current_slide_num}）")
            
            try:
                slide = presentation.Slides(current_slide_num)  # PowerPoint中幻灯片索引从1开始
            except Exception as e:
                print(f"获取幻灯片失败: {e}")
                continue
            
            # 获取更新内容
            updates = result.get('更新内容', [])
            
            # 记录这个幻灯片添加了多少新幻灯片
            slides_added_for_current = 0
            
            for update in updates:
                original_text = update.get('原内容', '')
                new_text = update.get('更新内容', '')
                
                # 提取更新内容的第一段作为实际更新文本
                # 我们会跳过前面的说明部分，找到实际内容部分
                actual_content = extract_actual_content(new_text)
                
                if not actual_content:
                    print(f"警告: 无法从更新内容中提取实际文本")
                    continue
                
                # 在幻灯片中查找并替换文本，可能会创建新幻灯片
                # 传递当前幻灯片的原始编号，以便函数可以返回是否添加了新幻灯片
                slides_added = replace_text_with_llm(
                    ppt_app, 
                    presentation, 
                    slide, 
                    current_slide_num, 
                    original_text, 
                    actual_content, 
                    llm
                )
                
                # 更新幻灯片偏移计数
                if slides_added > 0:
                    slides_added_for_current += slides_added
                    print(f"为幻灯片 {original_slide_num} 添加了 {slides_added} 张新幻灯片")
            
            # 更新后续幻灯片的偏移量
            if slides_added_for_current > 0:
                added_slides += slides_added_for_current
                # 更新所有后续幻灯片的偏移量
                for slide_n in slide_offset:
                    if slide_n > original_slide_num:
                        slide_offset[slide_n] += slides_added_for_current
                
                print(f"更新后的幻灯片偏移量: {slide_offset}")
        
        # 保存更新后的PPT
        output_path = os.path.splitext(ppt_path)[0] + '_updated.pptx'
        output_path = os.path.abspath(output_path)
        print(f"正在保存更新后的演示文稿: {output_path}")
        
        # 使用另存为功能
        try:
            # 尝试直接保存
            presentation.SaveAs(output_path)
        except Exception as e:
            print(f"保存遇到问题: {e}，尝试使用另一种方法保存...")
            # 如果失败，尝试另一种保存方式
            presentation.SaveCopyAs(output_path)
            
        print(f"关闭演示文稿...")
        presentation.Close()
        
        print(f"更新完成，共添加了 {added_slides} 张新幻灯片，已保存至: {output_path}")
        return output_path
    except Exception as e:
        print(f"更新PPT时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 确保关闭PowerPoint应用
        try:
            ppt_app.Quit()
            print("PowerPoint应用已关闭")
        except Exception as e:
            print(f"关闭PowerPoint时发生错误: {e}")
        
        # 释放COM
        pythoncom.CoUninitialize()

def extract_actual_content(text):
    """从更新文本中提取实际内容"""
    # 删除Markdown引用标记
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 删除Markdown粗体标记
    
    if "以下是适合在PPT中展示的更新内容" in text:
        # 跳过介绍部分
        try:
            content_start = text.index("---")
            # 找到第一个分隔符后的内容
            content_after_first = text[content_start+3:]
            
            # 查找下一个分隔符
            if "---" in content_after_first:
                end_index = content_after_first.index("---")
                return content_after_first[:end_index].strip()
            else:
                # 如果没有下一个分隔符，返回第一个分隔符后的所有内容
                return content_after_first.strip()
        except ValueError:
            # 如果没有找到分隔符，返回原始文本
            pass
    
    # 尝试找到分隔符"---"后的内容
    if "---" in text:
        parts = text.split("---")
        # 取第一个分隔符后的内容
        for i, part in enumerate(parts[1:], 1):
            if part.strip():
                # 如果是最后一部分或者下一部分包含"设计建议"/"注释"/"设计说明"等，则返回当前部分
                next_part_keywords = ["设计建议", "注释", "设计说明", "调整说明"]
                if i == len(parts) - 1 or any(keyword in parts[i+1] for keyword in next_part_keywords):
                    return part.strip()
                else:
                    # 如果当前部分包含实质性内容而非设计说明，返回它
                    if not any(keyword in part for keyword in next_part_keywords):
                        return part.strip()
    
    # 如果上述方法都失败，尝试更简单的方法
    # 通常GPT生成的内容会在第一个"---"后给出实际内容
    if "---" in text:
        first_content = text.split("---")[1].strip()
        return first_content
    
    # 最后手段，返回原始文本
    return text

def optimize_content_with_llm(llm, original_text, new_text, text_frame_content, char_count):
    """使用大模型优化内容，使其与原文本框内容融合并符合长度限制
    
    Args:
        llm: 大语言模型实例
        original_text: 原始需要更新的文本片段
        new_text: 更新后的文本
        text_frame_content: 文本框完整内容
        char_count: 文本框字符数量
        
    Returns:
        优化后的内容
    """
    system_message = "你是PPT内容优化专家，擅长制作简洁、有吸引力且保持一致性的PPT内容。"
    
    prompt = f"""请优化以下PPT更新内容，使其与原有文本框内容融合，形成连贯、通顺的表达：

## 原文本框完整内容:
```
{text_frame_content}
```

## 其中需要更新的部分:
```
{original_text}
```

## 更新后的内容:
```
{new_text}
```

## 优化要求:
1. 将更新内容与原文本框其他内容自然融合，形成连贯的表达
2. 保持PPT风格的简洁性和清晰度
3. 不允许有'更新后的PPT内容'等介绍内容，只能输出实质性内容！！不允许有任何符号、换行符等  
4. 优化后的完整内容最好控制在{char_count}字符左右
5. 如果无法保持在字符限制内，请创建一个最合理的分割点，以便内容可以分到两张幻灯片上

请直接返回优化后的完整内容，不需要任何解释。如果内容太长需要分割，请在需要分割的位置标记【分割点】。"""

    try:
        response = llm.invoke([
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ])
        
        return response.content
    except Exception as e:
        print(f"调用大模型时出错: {str(e)}")
        # 失败时返回简单合并的内容作为后备方案
        return text_frame_content.replace(original_text, new_text)

def find_text_in_shapes(shapes, text_to_find):
    """在形状集合中查找包含指定文本的形状"""
    for i in range(1, shapes.Count + 1):
        shape = shapes.Item(i)
        # 如果是文本框或形状包含文本
        if shape.HasTextFrame:
            try:
                if text_to_find in shape.TextFrame.TextRange.Text:
                    return shape, i
            except Exception as e:
                print(f"读取形状 {i} 的文本时出错: {e}")
        
        # 安全地检查是否是组合形状
        try:
            # 检查形状类型，GroupShape的类型值是6
            if shape.Type == 6:  # msoGroup
                # 递归查找组内形状
                for j in range(1, shape.GroupItems.Count + 1):
                    try:
                        group_item = shape.GroupItems.Item(j)
                        if group_item.HasTextFrame:
                            if text_to_find in group_item.TextFrame.TextRange.Text:
                                return group_item, i
                    except Exception as inner_e:
                        print(f"访问组内形状 {j} 时出错: {inner_e}")
        except Exception as e:
            # 忽略不支持组操作的形状
            pass
    
    return None, -1

def clean_format_text(text):
    """清理文本格式，移除Markdown和特殊符号"""
    # 移除Markdown标题符号
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # 移除Markdown列表符号，但保留项目符号
    text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
    
    # 移除粗体/斜体标记
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # 移除链接格式，保留链接文本
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    # 移除脚注引用
    text = re.sub(r'\[\^.*?\]', '', text)
    
    # 保留简单的列表格式，但统一符号
    text = re.sub(r'^(\s*)\d+\.\s+', r'\1• ', text, flags=re.MULTILINE)
    
    return text

def update_slide_text(shape, new_text):
    """更新形状中的文本"""
    try:
        # 使用TextRange更新文本
        shape.TextFrame.TextRange.Text = new_text
        return True
    except Exception as e:
        print(f"更新文本时出错: {str(e)}")
        return False

def create_continuation_slide(ppt_app, presentation, original_slide, slide_num, content, target_shape_index=None):
    """创建内容延续的新幻灯片
    
    使用COM接口复制幻灯片并更新目标形状的文本
    
    Args:
        ppt_app: PowerPoint应用实例
        presentation: 演示文稿对象
        original_slide: 原始幻灯片
        slide_num: 原始幻灯片编号
        content: 要添加到新幻灯片的内容
        target_shape_index: 目标形状的索引
    """
    try:
        # 复制原始幻灯片
        original_slide.Copy()
        
        # 确定要粘贴的位置（在原始幻灯片之后）
        insert_position = slide_num + 1
        
        # 粘贴幻灯片 - 使用简单的粘贴方法
        try:
            new_slide_idx = presentation.Slides.Paste().SlideIndex
            print(f"已粘贴新幻灯片，索引为 {new_slide_idx}")
            # 获取新创建的幻灯片
            new_slide = presentation.Slides(new_slide_idx)
        except Exception as e:
            print(f"粘贴幻灯片时出错: {e}")
            print("尝试不带位置的粘贴方法...")
            presentation.Slides.Paste()
            # 假设最后一张就是新创建的
            new_slide = presentation.Slides(presentation.Slides.Count)
        
        # 如果插入位置不是最后，且新幻灯片不在正确位置，则尝试移动幻灯片
        try:
            if insert_position != new_slide.SlideIndex and insert_position <= presentation.Slides.Count - 1:
                print(f"尝试将幻灯片从位置 {new_slide.SlideIndex} 移动到位置 {insert_position}")
                new_slide.MoveTo(insert_position)
        except Exception as e:
            print(f"移动幻灯片时出错: {e}，继续处理...")
        
        print(f"已创建幻灯片副本，紧随在幻灯片 {slide_num} 之后")
        
        # 如果知道目标形状的索引，直接更新该形状
        if target_shape_index and target_shape_index > 0:
            try:
                # 遍历新幻灯片中的所有形状，找到对应索引的形状
                if target_shape_index <= new_slide.Shapes.Count:
                    target_shape = new_slide.Shapes.Item(target_shape_index)
                    if target_shape.HasTextFrame:
                        update_slide_text(target_shape, content)
                        print(f"已更新幻灯片副本中的目标文本框 (索引: {target_shape_index})")
                        
                        # 如果是标题形状，添加"(续)"
                        if target_shape_index == 1 and not target_shape.TextFrame.TextRange.Text.endswith("(续)"):
                            target_shape.TextFrame.TextRange.Text += " (续)"
                        return
            except Exception as e:
                print(f"更新目标形状时出错: {e}，尝试其他方法...")
        
        # 否则，搜索包含原文本的形状
        try:
            target_shape, found_index = find_text_in_shapes(new_slide.Shapes, content[:30])
            
            if target_shape and target_shape.HasTextFrame:
                update_slide_text(target_shape, content)
                print("已更新幻灯片副本中的匹配文本框")
                return
        except Exception as e:
            print(f"查找和更新匹配文本框时出错: {e}，尝试其他方法...")
        
        # 如果未找到匹配的形状，寻找最大的文本框
        try:
            max_area = 0
            largest_shape = None
            
            for i in range(1, new_slide.Shapes.Count + 1):
                shape = new_slide.Shapes.Item(i)
                if shape.HasTextFrame:
                    # 计算形状面积
                    shape_area = shape.Width * shape.Height
                    if shape_area > max_area:
                        largest_shape = shape
                        max_area = shape_area
            
            if largest_shape:
                update_slide_text(largest_shape, content)
                print("已将延续内容添加到幻灯片副本的最大文本框中")
                return
        except Exception as e:
            print(f"寻找和更新最大文本框时出错: {e}，尝试创建新文本框...")
        
        # 如果所有尝试都失败，创建新的文本框
        try:
            # 如果没有找到合适的文本框，创建新的
            left = presentation.PageSetup.SlideWidth * 0.1
            top = presentation.PageSetup.SlideHeight * 0.2
            width = presentation.PageSetup.SlideWidth * 0.8
            height = presentation.PageSetup.SlideHeight * 0.5
            
            new_shape = new_slide.Shapes.AddTextbox(1, left, top, width, height)
            update_slide_text(new_shape, content)
            print("在幻灯片副本上创建了新文本框并添加了内容")
        except Exception as e:
            print(f"创建新文本框时出错: {e}")
            
        # 尝试为标题添加"(续)"标记
        try:
            # 通常标题是第一个形状或位于顶部的形状
            for i in range(1, new_slide.Shapes.Count + 1):
                shape = new_slide.Shapes.Item(i)
                if shape.HasTextFrame:
                    text = shape.TextFrame.TextRange.Text
                    # 检查是否是标题（第一个形状或位于顶部的形状）
                    if i == 1 or shape.Top < presentation.PageSetup.SlideHeight * 0.2:
                        if not text.endswith("(续)"):
                            shape.TextFrame.TextRange.Text = text + " (续)"
                        break
        except Exception as e:
            print(f"添加'(续)'标记时出错: {e}")
                    
    except Exception as e:
        print(f"创建幻灯片副本时出错: {str(e)}")
        import traceback
        # 通常标题是第一个形状或位于顶部的形状
        for i in range(1, new_slide.Shapes.Count + 1):
            shape = new_slide.Shapes.Item(i)
            if shape.HasTextFrame:
                text = shape.TextFrame.TextRange.Text
                # 检查是否是标题（第一个形状或位于顶部的形状）
                if i == 1 or shape.Top < presentation.PageSetup.SlideHeight * 0.2:
                    if not text.endswith("(续)"):
                        shape.TextFrame.TextRange.Text = text + " (续)"
                    break
                    
    except Exception as e:
        print(f"创建幻灯片副本时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def get_shape_text_length(shape):
    """获取形状中文本的长度"""
    if shape.HasTextFrame:
        return len(shape.TextFrame.TextRange.Text)
    return 0

def replace_text_with_llm(ppt_app, presentation, slide, slide_num, original_text, new_text, llm):
    """使用大模型优化内容并替换文本，如需要则创建新幻灯片
    
    Args:
        ppt_app: PowerPoint应用实例
        presentation: 演示文稿对象
        slide: 当前幻灯片
        slide_num: 当前幻灯片编号
        original_text: 原始文本
        new_text: 新文本
        llm: 大语言模型实例
        
    Returns:
        int: 添加的幻灯片数量
    """
    found = False
    target_shape = None
    target_shape_index = -1
    slides_added = 0  # 记录添加的幻灯片数量
    
    # 清理原始文本，移除多余空格和换行符以便更好地匹配
    original_text = original_text.strip()
    
    # 处理新文本中的格式
    new_text = clean_format_text(new_text)
    
    # 在幻灯片中查找包含原始文本的形状
    print(f"正在搜索包含文本的形状: '{original_text[:30]}...'")
    
    try:
        # 首先尝试搜索幻灯片中所有形状的文本
        all_text_found = False
        
        # 手动遍历所有形状查找文本
        for i in range(1, slide.Shapes.Count + 1):
            try:
                shape = slide.Shapes.Item(i)
                if shape.HasTextFrame:
                    try:
                        shape_text = shape.TextFrame.TextRange.Text
                        if original_text in shape_text:
                            target_shape = shape
                            target_shape_index = i
                            all_text_found = True
                            print(f"找到匹配文本在形状 {i}")
                            break
                    except Exception as e:
                        print(f"读取形状 {i} 的文本时出错: {e}")
            except Exception as e:
                print(f"访问形状 {i} 时出错: {e}")
        
        # 如果未找到，尝试使用find_text_in_shapes函数
        if not all_text_found:
            target_shape, target_shape_index = find_text_in_shapes(slide.Shapes, original_text)
    except Exception as e:
        print(f"搜索文本时出错: {e}")
    
    if target_shape:
        print(f"找到匹配文本: '{original_text[:30]}...'")
        found = True
        
        try:
            # 获取文本框的字符数量
            char_count = get_shape_text_length(target_shape)
            print(f"原文本框字符数量: {char_count}")
            
            # 获取文本框完整内容
            text_frame_content = target_shape.TextFrame.TextRange.Text
            
            # 使用大模型优化并融合内容
            optimized_content = optimize_content_with_llm(
                llm, 
                original_text, 
                new_text, 
                text_frame_content,
                char_count
            )
            
            # 检查是否需要分割内容到新幻灯片
            if "【分割点】" in optimized_content:
                first_part, second_part = optimized_content.split("【分割点】", 1)
                print(f"内容太长，将分割到两张幻灯片。第一部分长度: {len(first_part)}")
                
                # 更新当前幻灯片
                update_slide_text(target_shape, first_part)
                
                # 创建新幻灯片并添加剩余内容
                create_continuation_slide(ppt_app, presentation, slide, slide_num, second_part, target_shape_index)
                
                # 增加幻灯片计数
                slides_added += 1
            else:
                # 内容在字符限制内，直接更新
                update_slide_text(target_shape, optimized_content)
        except Exception as e:
            print(f"处理和更新文本时出错: {e}")
    
    if not found:
        print(f"警告: 无法在幻灯片中找到文本 '{original_text[:30]}...'")
        
        # 如果找不到精确匹配，尝试查找部分匹配
        try:
            best_match = None
            best_match_index = -1
            highest_similarity = 0
            
            # 遍历所有形状查找相似文本
            for i in range(1, slide.Shapes.Count + 1):
                try:
                    shape = slide.Shapes.Item(i)
                    if shape.HasTextFrame:
                        shape_text = shape.TextFrame.TextRange.Text
                        # 计算相似度 (简单的共同子串长度比例)
                        if len(shape_text) > 0:
                            common_chars = sum(1 for c in original_text if c in shape_text)
                            similarity = common_chars / len(original_text)
                            if similarity > highest_similarity and similarity > 0.5:  # 设置最小相似度阈值
                                best_match = shape
                                best_match_index = i
                                highest_similarity = similarity
                except Exception as e:
                    continue
            
            if best_match:
                print(f"找到最佳匹配文本框，相似度: {highest_similarity:.2f}")
                # 获取文本框的字符数量
                char_count = get_shape_text_length(best_match)
                
                # 获取文本框完整内容
                text_frame_content = best_match.TextFrame.TextRange.Text
                
                # 直接使用新文本替换整个文本框内容
                update_slide_text(best_match, new_text)
                print("已使用新内容更新最佳匹配的文本框")
        except Exception as e:
            print(f"尝试查找相似文本时出错: {e}")
    
    # 返回添加的幻灯片数量
    return slides_added

def print_report_summary(report):
    """打印报告摘要，方便了解更新内容"""
    print("\n===== 报告摘要 =====")
    print(f"文件: {report.get('文件', '未指定')}")
    print(f"处理的幻灯片: {', '.join(map(str, report.get('处理的幻灯片', [])))} 页")
    
    # 打印各幻灯片更新内容摘要
    print("\n--- 更新内容摘要 ---")
    for result in report.get('结果', []):
        slide_num = result.get('幻灯片')
        updates = result.get('更新内容', [])
        
        print(f"\n[幻灯片 {slide_num}] 更新项目: {len(updates)} 个")
        for i, update in enumerate(updates, 1):
            original = update.get('原内容', '')
            if len(original) > 50:
                original = original[:47] + "..."
            print(f"  {i}. 原内容: {original}")

def main():
    parser = argparse.ArgumentParser(description='根据JSON报告更新PPT')
    parser.add_argument('--report', required=True, help='更新报告的JSON文件路径')
    parser.add_argument('--ppt', help='要更新的PPT文件路径')
    parser.add_argument('--view', action='store_true', help='仅查看报告内容，不更新PPT')
    parser.add_argument('--model', default='deepseek-reasoner', help='使用的大模型名称')
    
    args = parser.parse_args()
    
    # 确保运行在Windows平台上
    if sys.platform != 'win32':
        print("错误: 该程序只能在Windows平台上运行，因为它依赖PowerPoint COM接口")
        sys.exit(1)
    
    # 检查是否安装了win32com
    try:
        import win32com.client
    except ImportError:
        print("错误: 请先安装pywin32库。运行: pip install pywin32")
        sys.exit(1)
    
    # 配置环境变量
    os.environ["DEEPSEEK_API_KEY"] = ""
    
    # 加载报告
    report = load_report(args.report)
    
    # 如果仅查看报告
    if args.view:
        print_report_summary(report)
        return
    
    # 如果要更新PPT但未提供PPT路径
    if not args.ppt:
        # 尝试从报告中获取PPT路径
        ppt_path = report.get('文件')
        if not ppt_path:
            print("错误: 未提供PPT文件路径，请使用--ppt参数指定")
            return
    else:
        ppt_path = args.ppt
    
    # 打印报告摘要
    print_report_summary(report)
    
    # 确认是否继续
    response = input("\n是否继续更新PPT? (y/n): ")
    if response.lower() != 'y':
        print("已取消更新")
        return
    
    # 更新PPT
    update_ppt(ppt_path, report, args.model)

if __name__ == "__main__":
    main() 
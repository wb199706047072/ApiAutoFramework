# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : case_fun_generate.py
# @Desc: 动态生成测试用例的核心模块

import os
import re
from loguru import logger
from string import Template
from datetime import datetime
from utils.files_utils.files_handle import load_yaml_file, get_files, get_relative_path
from utils.files_utils.excel_handle import ExcelHandle
from config.settings import CASE_FILE_TYPE, CUSTOM_MARKERS, AUTO_CASE_DIR, INTERFACE_DIR, AUTO_CASE_YAML_DIR, AUTO_CASE_EXCEL_DIR
from core.case_generate_utils.case_data_analysis import CaseDataCheck, CaseCheckException

"""
核心逻辑说明：
本模块负责将 YAML/Excel 格式的测试用例数据转换为可执行的 Python 测试代码（.py文件）。
流程如下：
1. 扫描 `INTERFACE_DIR` 目录下的所有测试用例文件（.yaml/.yml）。
2. 解析文件内容，区分是普通测试用例文件还是初始化文件（init_data.yaml）。
3. 如果是 `init_data.yaml`，则生成 `conftest.py`，用于 Pytest 的 fixture 初始化。
4. 如果是普通测试用例文件（以 test_ 开头），则验证数据格式，并根据 `case_template.txt` 模板生成对应的 Python 测试脚本。
5. 生成的 Python 文件会被放置在 `AUTO_CASE_DIR` 目录下，保持与原 YAML 文件相同的目录结构。
"""

CASE_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "case_template.txt")
CONFTEST_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "conftest_template.txt")


import json

def try_parse_json(value):
    """尝试将字符串解析为JSON对象"""
    if isinstance(value, str):
        value = value.strip()
        if (value.startswith('{') and value.endswith('}')) or \
           (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except:
                pass
    return value


def clean_case_data(data):
    """
    清洗测试数据，解决常见的类型转换问题
    例如：password, mobile 等字段如果是数字，强制转换为字符串，避免后端接口报错
    """
    # 需要强制转为字符串的敏感字段(不区分大小写)
    SENSITIVE_FIELDS = ['password', 'pwd', 'mobile', 'phone', 'id_card', 'account', 'card_no']
    
    if isinstance(data, dict):
        for k, v in data.items():
            # 1. 递归处理
            if isinstance(v, (dict, list)):
                clean_case_data(v)
            # 2. 敏感字段类型转换
            elif k.lower() in SENSITIVE_FIELDS:
                # 处理 int/float
                if isinstance(v, (int, float)):
                    if isinstance(v, float) and v.is_integer():
                        v = int(v)
                    # 强制包裹引号，确保 eval_data 解析后仍为字符串
                    data[k] = f"'{v}'"
                elif isinstance(v, str):
                    # 如果是变量引用 ${...}，跳过，交给后续 data_handle 处理
                    if v.strip().startswith("${") and v.strip().endswith("}"):
                        continue
                    
                    # 其他情况（数字字符串、普通字符串），强制包裹引号
                    # 避免 eval_data 将 "123" 转为 123，或 "True" 转为 True
                    data[k] = f"'{v}'"

    elif isinstance(data, list):
        for item in data:
            clean_case_data(item)
    return data



def __load_case_file(file):
    """
    读取用例数据(yaml/excel)并生成对应的测试用例文件 (.py)
    
    Args:
        file (str): 文件的绝对路径
        
    Returns:
        bool: 处理成功返回 True，失败或非文件路径返回 False
    """
    if os.path.isfile(file):
        try:
            # 读取文件中的用例数据，存储到data中
            if file.endswith(('.yaml', '.yml')):
                yaml_data = load_yaml_file(file)
            elif file.endswith(('.xlsx', '.xls')):
                excel = ExcelHandle(file)
                sheets = excel.read()
                yaml_data = {}
                case_list = []
                for sheet in sheets:
                    if sheet['sheet_name'] == "case_common":
                        if sheet['data']:
                            common_data = sheet['data'][0]
                            # 处理 case_common 中的 json 字段
                            for k, v in common_data.items():
                                common_data[k] = try_parse_json(v)
                                
                            yaml_data["case_common"] = common_data
                            # 特殊处理 case_markers，如果解析后仍是字符串，按逗号分隔
                            if "case_markers" in yaml_data["case_common"]:
                                markers = yaml_data["case_common"]["case_markers"]
                                if isinstance(markers, str):
                                    yaml_data["case_common"]["case_markers"] = [m.strip() for m in markers.split(',')]
                    else:
                        # 处理用例数据中的 JSON 字段
                        valid_rows = []
                        for row in sheet['data']:
                            # 过滤掉 ID 为空的行（可能是空行或注释行）
                            if not row.get('id'):
                                continue
                                
                            for k, v in row.items():
                                row[k] = try_parse_json(v)
                            
                            # 数据清洗：处理 password 等敏感字段的类型转换
                            clean_case_data(row)
                            
                            valid_rows.append(row)
                        case_list.extend(valid_rows)
                
                # 如果没有找到 case_common，尝试使用默认值或报错
                # 为了兼容性，如果没有 case_common，可能在 case_list 中
                
                # 将收集到的所有 case 放入 case_info
                yaml_data["case_info"] = case_list
                
                # 确保 case_common 存在，防止后续处理报错
                if "case_common" not in yaml_data:
                    yaml_data["case_common"] = {}
                    
                # 兼容 common_dependence
                yaml_data["common_dependence"] = None 
            else:
                logger.error(f"不支持的文件类型: {file}")
                return False

            logger.trace(f"需要处理的文件：{file}")
        except Exception as e:
            logger.error(f"读取文件 {file} 失败: {str(e)}")
            raise
            
        # 确定基础目标目录
        if file.endswith(('.yaml', '.yml')):
            base_target_dir = AUTO_CASE_YAML_DIR
        elif file.endswith(('.xlsx', '.xls')):
            base_target_dir = AUTO_CASE_EXCEL_DIR
        else:
            base_target_dir = AUTO_CASE_DIR

        # 判断文件是否在根目录（INTERFACE_DIR）下
        # os.path.samefile 用于检查两个路径是否指向同一个文件/目录（处理软链接等情况）
        if os.path.samefile(INTERFACE_DIR, os.path.dirname(file)):
            
            # 情况1：根目录下的初始化文件
            if os.path.basename(file) == "init_data.yaml" or os.path.basename(file) == "init_data.yml":
                """识别到init_data.yaml或者init_data.yml文件，自动生成conftest.py文件"""
                # 确保目标目录存在
                os.makedirs(os.path.dirname(file), exist_ok=True)
                logger.trace(f"识别到init_data.yaml或者init_data.yml文件，自动生成conftest.py文件")
                # 生成 conftest.py
                generate_conftest_file(
                    template_path=CONFTEST_TEMPLATE_DIR,
                    init_data=yaml_data,
                    target_path=base_target_dir
                )
                
            # 情况2：根目录下的测试用例文件（以 test 开头）
            elif os.path.basename(file).startswith("test"):
                try:
                    # 检查用例数据是否符合规范（字段检查等）
                    tested_case = CaseDataCheck().case_process(yaml_data)
                    # 调用核心生成函数
                    gen_case_file(
                        # 此时用例文件的直接父级目录是INTERFACE_DIR，则直接在AUTO_CASE_DIR下生成测试用例方法
                        filename=os.path.splitext(os.path.basename(file))[0], # 去掉扩展名作为文件名
                        case_template_path=CASE_TEMPLATE_DIR,
                        case_info=yaml_data.get("case_common", yaml_data.get("case_info")),
                        common_dependence=yaml_data.get("common_dependence", None),
                        case_data=tested_case,
                        target_case_path=base_target_dir
                    )
                except CaseCheckException as e:
                    logger.error(f"用例检查失败：{str(e)}")
                    raise  # 继续向上传递异常
            else:
                logger.error(f"{file}不是以init_data或者test开头的文件，跳过生成")
        else:
            # 情况3：子目录下的文件
            # 如果用例文件在子目录中，我们需要在生成目标目录中保持相同的子目录结构
            
            # 子目录下的初始化文件
            if os.path.basename(file) == "init_data.yaml" or os.path.basename(file) == "init_data.yml":
                """识别到init_data.yaml或者init_data.yml文件，自动生成conftest.py文件"""
                os.makedirs(os.path.dirname(file), exist_ok=True)
                logger.trace(f"识别到init_data.yaml或者init_data.yml文件，自动生成conftest.py文件")
                generate_conftest_file(
                    template_path=CONFTEST_TEMPLATE_DIR,
                    init_data=yaml_data,
                    # 计算相对路径，拼接目标路径
                    target_path=os.path.join(base_target_dir,
                                             get_relative_path(file_path=file, directory_path=INTERFACE_DIR))
                )

            # 子目录下的测试用例文件
            elif os.path.basename(file).startswith("test"):
                # 检查用例数据是否符合规范
                tested_case = CaseDataCheck().case_process(yaml_data)
                os.makedirs(os.path.dirname(file), exist_ok=True)
                gen_case_file(
                    filename=os.path.splitext(os.path.basename(file))[0],
                    case_template_path=CASE_TEMPLATE_DIR,
                    case_info=yaml_data.get("case_common", yaml_data.get("case_info")),
                    common_dependence=yaml_data.get("common_dependence", None),
                    case_data=tested_case,
                    target_case_path=os.path.join(base_target_dir,
                                                  get_relative_path(file_path=file, directory_path=INTERFACE_DIR))
                )
            else:
                logger.error(f"{file}不是以init_data或者test开头的文件")
        return True
    else:
        logger.error(f"{file}不是一个正确的文件路径！")
        return False


def generate_cases():
    """
    入口函数：根据配置文件，从指定类型文件中读取所有用例数据，并自动生成测试用例
    """
    files = []
    try:
        # CASE_FILE_TYPE 控制是用 YAML 还是 Excel
        if CASE_FILE_TYPE == 1:
            # 在用例数据"INTERFACE_DIR"目录中寻找后缀是yaml, yml的文件
            # get_files 是递归查找工具
            files = get_files(target=INTERFACE_DIR, start="test_", end=".yaml") \
                         + get_files(target=INTERFACE_DIR, start="test_", end=".yml") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".yml") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".yaml")
        elif CASE_FILE_TYPE == 2:
            files = get_files(target=INTERFACE_DIR, start="test_", end=".xlsx") \
                         + get_files(target=INTERFACE_DIR, start="test_", end=".xls") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".xlsx") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".xls")
        elif CASE_FILE_TYPE == 3:
            files = get_files(target=INTERFACE_DIR, start="test_", end=".yaml") \
                         + get_files(target=INTERFACE_DIR, start="test_", end=".yml") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".yml") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".yaml") \
                         + get_files(target=INTERFACE_DIR, start="test_", end=".xlsx") \
                         + get_files(target=INTERFACE_DIR, start="test_", end=".xls") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".xlsx") \
                         + get_files(target=INTERFACE_DIR, start="init_data", end=".xls")
        else:
            logger.error(f"{CASE_FILE_TYPE}不在CaseFileType内，不能自动生成用例！")
            
        # 遍历所有找到的文件，逐个处理
        for file in files:
            try:
                logger.trace(f"正在处理文件: {file}")
                __load_case_file(file=file)
            except Exception as e:
                logger.error(f"自动生成测试用例时发生错误, 用例文件：{file} | 错误信息: {str(e)}")
    except Exception as e:
        logger.error(f"获取文件列表时发生错误: {str(e)}")


def generate_conftest_file(init_data, template_path, target_path):
    """
    生成 conftest.py 文件
    
    Args:
        init_data (dict): 需要注入到 conftest 的初始化数据
        template_path (str): conftest 模板文件的路径
        target_path (str): 生成文件的目标目录
    """
    try:
        # 如果目标目录不存在则自动创建一个
        # exist_ok=True: 如果目录已存在不报错
        os.makedirs(target_path, exist_ok=True)
        
        # 读取模板内容
        with open(file=template_path, mode="r", encoding="utf-8") as f:
            current_template = ''.join(f.readlines())

        # 使用 string.Template 进行变量替换
        # safe_substitute: 如果模板中有变量未在字典中提供，不会报错，而是保留原样
        conftest_content = Template(current_template).safe_substitute(
            {
                "init_data": init_data,
            }
        )
        # 写入文件
        filepath = os.path.join(target_path, 'conftest.py')
        with open(filepath, "w", encoding="utf-8") as fp:
            fp.write(conftest_content)
            logger.trace(f"conftest.py文件创建成功:{filepath}")
    except Exception as e:
        logger.error(f"生成conftest.py文件时发生错误: {e}")


def gen_case_file(filename, case_template_path, case_info, common_dependence, case_data, target_case_path):
    """
    核心生成逻辑：根据测试用例数据生成 Python 测试文件
    
    Args:
        filename (str): 生成的 Python 文件名（不含后缀），通常与 YAML 文件名对应
        case_template_path (str): 测试用例模板文件的路径
        case_info (dict): 用例公共信息（Epic, Feature, Story 等 Allure 标签）
        common_dependence (dict): 公共依赖配置
        case_data (list): 具体的测试步骤列表
        target_case_path (str): 生成文件的目标目录
    """
    logger.trace(f"开始处理用例: {filename}")
    try:
        # 1. 验证必要的配置项
        if case_info is None:
            raise ValueError(f"用例 {filename} 缺少case_common/case_info配置")
        # 为 allure 字段提供默认值
        case_info.setdefault('allure_epic', 'Default Epic')
        case_info.setdefault('allure_feature', filename)
        case_info.setdefault('allure_story', 'Default Story')
            
        # 2. 确保目标目录存在
        if not os.path.exists(target_case_path):
            os.makedirs(target_case_path, exist_ok=True)
            
        # 3. 获取并处理 Pytest 标记（markers）
        pytest_markers = case_info.get("case_markers", []) or []
        
        # 3.1 自动添加基于目录名称的标记
        # 获取相对于 INTERFACE_DIR 的路径
        relative_path = get_relative_path(file_path=os.path.join(target_case_path, filename), directory_path=AUTO_CASE_DIR)
        
        # 优化：添加路径中的所有目录作为标记
        rel_dir = os.path.relpath(target_case_path, AUTO_CASE_DIR)
        if rel_dir != ".":
            # 将路径分隔符统一处理，分割出每一级目录
            path_parts = rel_dir.split(os.sep)
            for part in path_parts:
                if part and part != ".":
                     if part not in pytest_markers:
                         # 避免重复添加
                         is_duplicate = False
                         for m in pytest_markers:
                             if isinstance(m, str) and m == part:
                                 is_duplicate = True
                                 break
                         if not is_duplicate:
                            pytest_markers.append(part)

        logger.trace(f"用例 {filename} 的标记: {pytest_markers}")

        # 3.2 将标记转换为装饰器字符串
        marker_decorators = []
        for marker in pytest_markers:
            if isinstance(marker, str):
                marker_decorators.append(f"@pytest.mark.{marker}")
            elif isinstance(marker, dict):
                for name, args in marker.items():
                    if isinstance(args, str):
                        marker_decorators.append(f"@pytest.mark.{name}('{args}')")
                    elif isinstance(args, dict):
                         # 如果是字典，可能是参数
                         # 暂不支持复杂参数，需根据实际需求扩展
                         pass
                    else:
                        marker_decorators.append(f"@pytest.mark.{name}({args})")
        
        markers_str = "\n".join(marker_decorators)

        try:
            # 4. 读取模板文件 (使用 read 获取整个字符串以便 Template 使用)
            with open(file=case_template_path, mode="r", encoding="utf-8") as f:
                case_template = f.read()
        except Exception as e:
            logger.error(f"读取模板文件 {case_template_path} 失败: {str(e)}")
            raise

        # 5. 准备替换数据
        current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
        
        # 构造替换字典
        # 处理函数名，替换非法字符
        func_title = filename.replace("-", "_")

        mapping = {
            "DATE": current_time.split(" ")[0],
            "TIME": current_time.split(" ")[1],
            "NAME": filename,
            "PRODUCT_NAME": "PyCharm", # 默认值
            "case_data": str(case_data), # 将列表转为字符串注入到 Python 代码中
            "epic": case_info.get("allure_epic", "Unknown Epic"),
            "feature": case_info.get("allure_feature", "Unknown Feature"),
            "story": case_info.get("allure_story", "Unknown Story"),
            "func_title": func_title,  # 函数名通常用 test_xxx
            "markers": markers_str   # 注入标记装饰器
        }
        
        # 6. 替换模板内容
        content = Template(case_template).safe_substitute(mapping)
        
        # 7. 写入 Python 文件
        file_path = os.path.join(target_case_path, f"{filename}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.trace(f"生成用例文件成功: {file_path}")
        
    except Exception as e:
        logger.error(f"生成用例文件失败: {str(e)}")
        raise

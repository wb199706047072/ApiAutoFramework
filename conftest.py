# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : conftest.py
# @Desc: 全局配置文件

import time
import os
from datetime import datetime
from loguru import logger
from config.settings import REPORT_DIR, CUSTOM_MARKERS, ENV_DIR, GLOBAL_VARS
from utils.files_utils.files_handle import load_yaml_file


# ------------------------------------- START: pytest钩子函数处理---------------------------------------#
def pytest_addoption(parser):
    """
    注册自定义命令行参数
    """
    parser.addoption("--env", action="store", default="test", help="run env: test or live")


def pytest_configure(config):
    """
    1. 加载环境配置到全局变量
    2. 注册自定义标记
    """
    # 加载环境配置
    env = config.getoption("--env")
    if env:
        env_path = os.path.join(ENV_DIR, f"{env}.yml")
        if not os.path.exists(env_path):
            env_path = os.path.join(ENV_DIR, f"{env}.yaml")
        
        if os.path.exists(env_path):
            logger.info(f"Loading environment config from: {env_path}")
            __env = load_yaml_file(env_path)
            GLOBAL_VARS.update(__env)
        else:
            logger.warning(f"Environment config file not found: {env}")

    # 注册自定义标记
    logger.debug(f"需要注册的标记：{CUSTOM_MARKERS}")
    # 对标记进行去重处理
    unique_markers = []
    for item in CUSTOM_MARKERS:
        if item not in unique_markers:
            unique_markers.append(item)
    # 注册标记
    for custom_marker in unique_markers:
        if isinstance(custom_marker, str):
            config.addinivalue_line('markers', f'{custom_marker}')
        elif isinstance(custom_marker, dict):
            for k, v in custom_marker.items():
                config.addinivalue_line('markers', f'{k}:{v}')


def pytest_terminal_summary(terminalreporter, config):
    """
    收集测试结果
    """

    _RERUN = len([i for i in terminalreporter.stats.get('rerun', []) if i.when != 'teardown'])
    try:
        # 获取pytest传参--reruns的值
        reruns_value = int(config.getoption("--reruns"))
        _RERUN = int(_RERUN / reruns_value)
    except Exception:
        reruns_value = "未配置--reruns参数"
        _RERUN = len([i for i in terminalreporter.stats.get('rerun', []) if i.when != 'teardown'])

    _PASSED = len([i for i in terminalreporter.stats.get('passed', []) if i.when != 'teardown'])
    _ERROR = len([i for i in terminalreporter.stats.get('error', []) if i.when != 'teardown'])
    _FAILED = len([i for i in terminalreporter.stats.get('failed', []) if i.when != 'teardown'])
    _SKIPPED = len([i for i in terminalreporter.stats.get('skipped', []) if i.when != 'teardown'])
    _XPASSED = len([i for i in terminalreporter.stats.get('xpassed', []) if i.when != 'teardown'])
    _XFAILED = len([i for i in terminalreporter.stats.get('xfailed', []) if i.when != 'teardown'])
    _DESELECTED = len(terminalreporter.stats.get('deselected', []))
    deselected_cases = "\n".join(list(map(str, terminalreporter.stats.get("deselected", []))))

    _TOTAL = _PASSED + _ERROR + _FAILED + _SKIPPED + _XPASSED + _XFAILED + _DESELECTED

    # 兼容处理开始时间
    _sessionstarttime = getattr(config, "_sessionstarttime", time.time())

    _DURATION = time.time() - _sessionstarttime

    session_start_time = datetime.fromtimestamp(_sessionstarttime)
    _START_TIME = f"{session_start_time.year}年{session_start_time.month}月{session_start_time.day}日 " \
                  f"{session_start_time.hour}:{session_start_time.minute}:{session_start_time.second}"

    test_info = f"各位同事, 大家好:\n" \
                f"自动化用例于 {_START_TIME}- 开始运行，运行时长：{_DURATION:.2f} s， 目前已执行完成。\n" \
                f"--------------------------------------\n" \
                f"#### 执行结果如下:\n" \
                f"- 测试用例总数: {_TOTAL} 个\n" \
                f"- 跳过用例个数（skipped+deselected）: {_SKIPPED + _DESELECTED} 个\n" \
                f"- 实际执行用例总数: {_PASSED + _FAILED + _XPASSED + _XFAILED} 个\n" \
                f"--------------------------------------------------------------\n" \
                f"- 通过用例个数（passed）: {_PASSED} 个\n" \
                f"- 失败用例个数（failed）: {_FAILED} 个\n" \
                f"- 异常用例个数（error）: {_ERROR} 个\n" \
                f"- 重跑的用例数(--reruns的值): {_RERUN} 个 ({reruns_value})\n" \
                f"--------------------------------------------------------------\n" \
                f"- 忽略(deselected)的用例:\n{deselected_cases}\n" \
                f"--------------------------------------------------------------\n"

    try:
        _RATE = (_PASSED + _XPASSED) / (_PASSED + _FAILED + _XPASSED + _XFAILED) * 100
        test_result = f"- 用例成功率: {_RATE:.2f} %\n"
        logger.success(f"{test_info}{test_result}")
    except ZeroDivisionError:
        test_result = "- 用例成功率: 0.00 %\n"
        logger.critical(f"{test_info}{test_result}")

    # 这里是方便在流水线里面发送测试结果到钉钉/企业微信的
    with open(file=os.path.join(REPORT_DIR, "test_result.txt"), mode="w", encoding="utf-8") as f:
        f.write(f"{test_info}{test_result}")

# ------------------------------------- END: pytest钩子函数处理---------------------------------------#

# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : conftest.py
# @Desc: 

import os
import pytest
import allure
from loguru import logger
from config.settings import GLOBAL_VARS, PROJECT_DIR
from core.report_utils.allure_handle import allure_title
from core.requests_utils.request_control import RequestControl


@pytest.fixture(scope="function", autouse=True)
def case_control(request):
    """用例控制"""
    # 使用 request.getfixturevalue() 方法来获取测试用例函数的参数值
    # 注意这里的"case"需要与@pytest.mark.parametrize("case", cases)中传递的保持一致
    case = request.getfixturevalue("case")
    logger.info(f'\n-----------------------------START-开始执行用例- {case.get("id")} || {case.get("title")}-----------------------------')
    # 添加用例标题作为allure中显示的用例标题
    allure_title(case.get("title", ""))
    if case.get("run") is None or case.get("run") is False:
        reason = f"{case.get('id')} || {case.get('title')}: 标记了该用例不执行（run=False）。"
        logger.warning(f"{reason}")
        pytest.skip(reason)
    yield
    logger.info("-----------------------------END-用例执行完成-----------------------------")


def pytest_collection_modifyitems(config, items):
    for item in items:
        # 注意这里的"case"需要与@pytest.mark.parametrize("case", cases)中传递的保持一致
        parameters = item.callspec.params["case"]
        # print(f"测试参数：{type(parameters)}     {parameters}")
        if parameters.get("severity"):
            if parameters["severity"].upper() == "TRIVIAL":
                item.add_marker(allure.severity(allure.severity_level.TRIVIAL))
            elif parameters["severity"].upper() == "MINOR":
                item.add_marker(allure.severity(allure.severity_level.MINOR))
            elif parameters["severity"].upper() == "CRITICAL":
                item.add_marker(allure.severity(allure.severity_level.CRITICAL))
            elif parameters["severity"].upper() == "BLOCKER":
                item.add_marker(allure.severity(allure.severity_level.BLOCKER))
            else:
                item.add_marker(allure.severity(allure.severity_level.NORMAL))
        else:
            item.add_marker(allure.severity(allure.severity_level.NORMAL))


@pytest.fixture(scope="session")
def gitlink_login():
    """
    获取登录的token
    :return:
    """
    # 请求登录接口
    res = RequestControl().api_request_flow(api_file_path=os.path.join(PROJECT_DIR, "test_login.yaml"),
                                            key="login_01", global_var=GLOBAL_VARS)
    GLOBAL_VARS.update(res)

# -*- coding: utf-8 -*-
# @Time    : 2026/02/10 14:03
# @Author  : 会飞的🐟
# @File    : test_workspace_multi.py
# @Software: PyCharm
# @Desc: 

import pytest
import allure
from loguru import logger
from config.settings import GLOBAL_VARS
from core.requests_utils.request_control import RequestControl
from core.requests_utils.case_dependence import CaseDependenceHandler
# 公共依赖
dependence_handler = CaseDependenceHandler(GLOBAL_VARS)

# 用例数据
cases = [{'id': 'case_login_excel_01', 'title': '用户名密码正确，登录成功', 'severity': 'NORMAL', 'url': '/api/crm/v4/user/login', 'run': True, 'method': 'POST', 'headers': "{'Content-Type': 'application/json; charset=utf-8;'}", 'cookies': None, 'request_type': 'JSON', 'payload': {'username': 'admin', 'password': "'123123'", 'appPlatform': 'work-space', 'appVersion': '1.0.1'}, 'files': None, 'wait_seconds': None, 'validate': {'status_code': 200, 'assert_ret': {'type_jsonpath': '$.ret', 'expect_value': 0, 'assert_type': '=='}, 'assert_user': {'type_jsonpath': '$.data.user.username', 'expect_value': 'admin', 'assert_type': '=='}}, 'extract': {'token': '$.data.token', 'username': '$.data.user.username'}, 'case_dependence': None}, {'id': 'case_login_excel_02', 'title': '用户名正确，密码错误，登录失败', 'severity': 'TRIVIAL', 'url': '/api/crm/v4/user/login', 'run': False, 'method': 'POST', 'headers': "{'Content-Type': 'application/json; charset=utf-8;'}", 'cookies': None, 'request_type': 'JSON', 'payload': {'username': 'admin', 'password': "'12313'", 'appPlatform': 'work-space', 'appVersion': '1.0.1'}, 'files': None, 'wait_seconds': None, 'validate': {'eq': {'http_code': 200, '$.ret': -2}}, 'extract': {}, 'case_dependence': None}]
@allure.epic("统一工作台")
@allure.feature("用户登录模块")
@allure.story("登录与校验")
@pytest.mark.auto
@pytest.mark.auto
@pytest.mark.excel_case
@pytest.mark.smoke
@pytest.mark.projects
@pytest.mark.workspace
@pytest.mark.parametrize("case", cases, ids=lambda x: x["title"])
def test_workspace_multi_auto(case):
    # 前置依赖处理
    if case.get("case_dependence") and case["case_dependence"].get("setup"):
        dependence_results = dependence_handler.case_dependence_handle(
            case_dependence=case["case_dependence"]["setup"],
            db_info=GLOBAL_VARS["db_info"])
        GLOBAL_VARS.update(dependence_results if dependence_results else {})
    # 处理请求前的用例数据 -> 发送请求 -> 响应/数据库断言 -> 断言成功后进行参数提取
    if GLOBAL_VARS.get("db_info"):
        res = RequestControl().api_request_flow(request_data=case, global_var=GLOBAL_VARS, db_info=GLOBAL_VARS["db_info"])
    else:
        res = RequestControl().api_request_flow(request_data=case, global_var=GLOBAL_VARS)
    GLOBAL_VARS.update(res)
    # 后置依赖处理
    if case.get("case_dependence") and case["case_dependence"].get("teardown"):
        dependence_results = dependence_handler.case_dependence_handle(
            case_dependence=case["case_dependence"]["teardown"],
            db_info=GLOBAL_VARS["db_info"])
        GLOBAL_VARS.update(dependence_results if dependence_results else {})

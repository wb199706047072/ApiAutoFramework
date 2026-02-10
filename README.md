# API 自动化测试框架

## 一、框架介绍
本框架是基于 Python + Pytest + Allure + Loguru实现的接口自动化测试框架，支持 YAML/Excel 用例管理、多环境切换、多项目复用、敏感信息加密管理以及丰富的通知机制。

## 二、核心功能

*   配置分离与安全管理:
    *   使用 `.env` 文件统一管理账号、密码、密钥等敏感信息，杜绝代码硬编码。
    *   支持多项目/多环境配置 (`config/*.yaml`)，通过 `${VAR}` 动态引用环境变量。
*   多源用例生成与隔离:
    *   支持同时从 YAML 和 Excel 生成测试用例。
    *   **生成隔离**: YAML 用例生成至 `testcases/test_auto_case/yaml_case/`，Excel 用例生成至 `testcases/test_auto_case/excel_case/`，便于分类管理。
*   **多项目与多环境支持**:
    *   通过 `-env <project_name>` 参数一键切换项目/环境配置。
*   **其他特性**:
    *   Session 会话自动关联
    *   动态参数提取与依赖注入 (JSONPath/Regex)
    *   Allure 定制化报告
    *   Loguru 优雅日志
    *   多渠道通知 (邮件/钉钉/企业微信)

## 三、项目结构

```text
ApiAutotest/
├── config/                  # 配置文件目录
│   ├── settings.py          # 全局配置文件
│   ├── test.yaml            # 测试环境配置
│   └── prod.yaml            # 生产/正式环境配置
├── core/                    # 核心逻辑目录
│   ├── assertion_utils/     # 断言工具
│   ├── case_generate_utils/ # 用例自动生成工具
│   ├── data_utils/          # 数据处理工具
│   ├── report_utils/        # 报告生成与发送工具
│   └── requests_utils/      # 请求封装工具
├── files/                   # 测试数据文件 (上传下载等)
├── interfaces/              # 接口定义目录 (YAML/Excel 用例源文件)
│   ├── projects/            # 按项目分类的接口定义
│   └── ...
├── lib/                     # 第三方库或工具 (如 Allure 命令行工具)
├── outputs/                 # 输出产物目录
│   ├── log/                 # 运行日志
│   └── report/              # 测试报告
├── testcases/               # 测试用例目录
│   ├── test_auto_case/      # 自动生成的测试用例
│   │   ├── excel_case/      # Excel 生成的用例
│   │   └── yaml_case/       # YAML 生成的用例
│   └── test_manual_case/    # 手动编写的测试用例
├── utils/                   # 通用工具类
├── .env                     # 环境变量配置文件 (敏感信息)
├── .env.example             # 环境变量示例文件
├── conftest.py              # Pytest 全局配置钩子
├── pytest.ini               # Pytest 配置文件
├── requirements.txt         # 项目依赖文件
└── run.py                   # 项目启动入口
```

## 四、快速开始

### 1. 安装依赖（推荐使用虚拟环境）
macOS 环境的系统 Python 受外部管理，建议使用虚拟环境隔离依赖：
```bash
# 创建并启用虚拟环境
python3 -m venv venv
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境 (.env)
复制模板文件并配置您的敏感信息：
```bash
cp .env.example .env
```
在 `.env` 中填入真实的数据库密码、API Key 等信息：
```properties
# .env 示例
TEST_DB_HOST=127.0.0.1
TEST_DB_PWD=secret_password
DEMO_HOST=https://demo.api.com
```

### 3. 配置项目 (config/*.yaml / *.yml)
在 `config/` 目录下创建项目配置文件（如 `prod.yaml` 或 `test.yaml`），支持引用 `.env` 变量：
```yaml
# config/prod.yaml
host: ${PROD_HOST}
username: "admin"
db_info:
  db_host: ${PROD_DB_HOST}
```

### 4. 运行测试
详细运行方式请参考 **[五、运行参数与方式](#五运行参数与方式)** 章节。

```bash
# 运行默认测试环境（已激活虚拟环境）
python3 run.py
# 或未激活时使用虚拟环境中的解释器
./venv/bin/python3 run.py
```

## 五、运行参数与方式

本项目统一通过 `run.py` 入口文件执行测试，支持多种参数组合以满足不同场景需求。

### 1. 命令行参数说明
| 参数 | 缩写 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `--env` | `-env` | `test` | 指定运行环境，对应 `config/{env}.yaml` 配置文件 | `python3 run.py -env live` |
| `--m` | `-m` | `None` | 运行指定标记 (Marker) 的用例 (需在 pytest.ini 中定义) | `python3 run.py -m smoke` |
| `--report` | `-report` | `yes` | 是否生成 Allure HTML 报告 (yes/no) | `python3 run.py -report no` |
| `--cron` | `-cron` | `False` | 是否开启定时任务模式 | `python3 run.py -cron` |

### 2. 常见运行场景

**场景一：切换测试环境**
```bash
# 运行 live 环境 (加载 config/live.yaml)
python3 run.py -env live
```

**场景二：只运行冒烟测试用例**
```bash
# 仅运行被标记为 smoke 的用例
python3 run.py -m smoke
# 如需运行 Excel 自动生成的用例，可使用其已有标记：
# 运行 auto 标记的用例
python3 run.py -m auto
# 运行 excel_case 标记的用例
python3 run.py -m excel_case
```

**场景三：CI/CD 流水线集成**
在流水线中通常不需要本地生成 HTML 报告 (由 Jenkins/GitLab CI 插件生成)，且需要非交互模式：
```bash
python3 run.py -env test -report no
```

**场景四：开启定时任务**
```bash
# 开启定时任务执行
python3 run.py -cron
```

## 六、用例编写指南

### 1. 目录结构
```text
interfaces/
  ├── project_a/         # 项目 A 的接口定义
  │     ├── test_login.yaml
  │     └── test_pay.xlsx
  └── project_b/         # 项目 B 的接口定义
        └── test_order.yaml
```

### 2. YAML 用例示例
文件名必须以 `test_` 开头（如 `test_demo.yaml`）。

```yaml
case_common:
  allure_epic: 电商平台          # Allure 报告的一级目录
  allure_feature: 用户管理模块    # Allure 报告的二级目录
  allure_story: 用户登录与验证    # Allure 报告的三级目录
  case_markers: ['smoke', 'p0'] # Pytest 标记

case_info:
  # 场景一：登录并提取 Token
  - id: login_01
    title: 用户登录
    url: /api/user/login
    method: POST
    headers:
      Content-Type: application/json
    payload:
      username: ${username}      # 引用全局变量/环境变量
      password: ${password}
    # 数据提取：从响应中提取数据供后续使用
    extract:
      token: $.data.token        # 使用 JSONPath 提取 token
      user_id: $.data.id         # 提取用户 ID
    # 响应断言
    assert_response:
      status_code: 200           # 校验 HTTP 状态码
      assert_msg:
        type_jsonpath: "$.msg"   # 校验响应体字段
        expect_value: "login success"
        assert_type: "=="        # 断言类型：==, !=, in, not_in 等

  # 场景二：查询用户信息（依赖登录 Token，并校验数据库）
  - id: get_user_info_01
    title: 查询用户信息
    url: /api/user/info
    method: GET
    headers:
      Authorization: Bearer ${token}  # 使用上一步提取的 token
    # 用例依赖：确保前置条件满足
    case_dependence:
      setup:
        interface: login_01      # 依赖登录接口，自动执行并获取变量
    # 响应断言
    assert_response:
      status_code: 200
      assert_code:
        type_jsonpath: "$.code"
        expect_value: 0
        assert_type: "=="
    # 数据库断言：校验数据持久化是否正确
    assert_sql:
      - sql: "SELECT username FROM users WHERE id='${user_id}'" # 使用提取的变量
        expect_value: "test_user"
        assert_type: "=="
```

### 3. 自动生成说明
*   运行 `run.py` 时，框架会自动扫描 `interfaces/` 下的文件。
*   **YAML 文件**生成的测试代码存放于：`testcases/test_auto_case/yaml_case/`
*   **Excel 文件**生成的测试代码存放于：`testcases/test_auto_case/excel_case/`

## 八、Excel 模板与示例

### 1. 字段规范（列名）
- id：用例唯一标识，必须以非空字符串填写
- title：用例标题（展示与报告）
- severity：用例等级，支持 NORMAL/TRIVIAL/MINOR/CRITICAL/BLOCKER
- url：接口路径，如 /api/crm/v4/user/login
- run：是否执行，True/False（为 False 时将被跳过）
- method：请求方法，GET/POST/PUT/DELETE 等
- headers：请求头，建议 JSON 字符串或字典字面量
- cookies：Cookie 配置（可空）
- request_type：请求体类型，JSON/FORM/FILE 等
- payload：请求体，支持字典或 JSON 字符串；保留字符串请使用引号（示例：手机号前加单引号）
- files：文件上传（可空）
- wait_seconds：请求前等待时间（秒）（可空）
- validate：断言规则，支持如 {'eq': {'http_code': 200, '$.status': 0}}
- extract：参数提取，支持如 {'token': '$.data.token'}
- case_dependence：用例依赖，包含 setup/teardown（可空）

### 1.1 断言写法规范（validate）
- 支持同时配置多个断言，使用字典按键区分；status_code 为特殊键，直接断言 HTTP 状态码
- assert_type 必须使用枚举值：`==, not_eq, gt, ge, lt, le, contains, str_eq, len_eq, len_gt, len_ge, len_lt, len_le, contained_by, startswith, endswith`
- 示例：
```json
{
  "status_code": 200,
  "assert_ret": { "type_jsonpath": "$.ret", "expect_value": 0, "assert_type": "==" },
  "assert_user": { "type_jsonpath": "$.data.user.username", "expect_value": "admin", "assert_type": "==" }
}
```

### 1.2 依赖场景示例（登录→查询）
- 在 Excel 的 cases 表中，使用 case_dependence 配置前后置依赖：
```json
{
  "setup": { "interface": "login_01" },
  "teardown": null
}
```
- 查询用例 headers 可引用上一步提取的 token，例如：
```json
{ "Authorization": "Bearer ${token}" }
```

### 2. 最小可运行示例
示例文件位置（workspace 项目）：
- [test_crm.xlsx](file:///Users/nidaye/DevolFiles/PythonProject/ApiAutotest/interfaces/projects/workspace/test_crm.xlsx)
- [test_workspace_multi.xlsx](file:///Users/nidaye/DevolFiles/PythonProject/ApiAutotest/interfaces/projects/workspace/test_workspace_multi.xlsx)
运行后会在 [excel_case](file:///Users/nidaye/DevolFiles/PythonProject/ApiAutotest/testcases/test_auto_case/excel_case) 生成对应测试代码（如 test_workspace_multi.py）。

示例用例的标记：
- 自动生成的测试函数默认带有 `@pytest.mark.auto` 与 `@pytest.mark.excel_case`
- 可通过 `-m auto` 或 `-m excel_case` 进行筛选运行

### 3. 运行步骤
```bash
# 激活虚拟环境后，生成并运行所有用例（含 Excel）
run.py -env test

# 仅运行 Excel 生成的用例
run.py -env test -m excel_case
# 或
run.py -env test -m auto
```

### 4. 常见写法提示
- 数字字符串需保留原样时，在 Excel 单元格前加单引号，例如：'13800138000
- headers/payload 等结构化字段推荐使用字典字面量或 JSON 字符串
- 需要前后置依赖时，在 case_dependence 中使用 setup/teardown 配置

## 八、常见问题与排查

1.  忽略（deselected）与跳过（skipped）的区别
    - deselected：因 `-m/-k` 等筛选条件不匹配被收集阶段排除；不会执行
    - skipped：在执行阶段被显式跳过；本框架当用例数据 `run=False` 时会跳过
2.  标记筛选建议
    - 若看到大量 `deselected`，请确认所用标记与用例实际标记一致（如 `auto`/`excel_case`）
    - 可在 YAML 的 `case_common.case_markers` 中维护统一标记策略（如加上 `smoke`）
3.  Allure 报告查看
    - 结果目录：`outputs/report/allure_results`，HTML 报告：`outputs/report/allure_html`
    - 图形界面打开：`allure open outputs/report/allure_results` 或使用框架内置打开逻辑
    - 无头/CI 环境可能无法自动在浏览器中展示，可改用 `allure generate` 生成静态报告

4.  导入冲突（import file mismatch）
    - 同名 Excel 可能生成同名 .py，导致 Pytest 在不同目录发现两个模块；请确保同目录内文件名唯一或清理 `testcases/test_auto_case/excel_case` 后再生成

## 九、依赖库
核心依赖如下，详细列表请见 `requirements.txt`：
*   pytest
*   allure-pytest
*   requests
*   loguru
*   pyyaml
*   openpyxl
*   **python-dotenv**（用于环境变量管理）
*   yagmail

## 十、注意事项

1.  **用例文件命名规范**:
    *   **必须**以 `test` 开头（例如 `test_login.yaml`），否则框架无法自动识别并生成测试代码。
    *   文件名建议使用下划线 `_` 分隔（例如 `test_user_info.yaml`）。如果包含连字符 `-`，框架会自动替换为 `_` 以符合 Python 命名规范。

2.  **配置与安全**:
    *   **环境配置文件**: 使用 `-env abc` 运行时，必须确保 `config/abc.yaml` 或 `config/abc.yml` 文件存在。
    *   **敏感信息**: `.env` 文件包含数据库密码等敏感信息，**严禁提交到代码仓库**（`.gitignore` 已默认忽略）。请使用 `.env.example` 作为模板分发。
    *   **不要在代码中硬编码密钥**（如 `settings.py` 中的账号/令牌），统一改用环境变量（`.env`）并在代码中读取。

### 10.1 敏感信息迁移到 .env（推荐）
- 建议将通知与账号配置统一迁移到环境变量：
```properties
# 邮件
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_app_password
EMAIL_HOST=smtp.163.com
EMAIL_TO=someone@example.com,other@example.com

# 钉钉
DING_TALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=...
DING_TALK_SECRET=SECxxxxxxxx

# 企业微信
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...
```
- 使用时通过 `os.getenv()` 读取，避免在 `settings.py` 硬编码；`.env.example` 仅保留键名与示例占位值

3.  Excel 用例编写:
    *   数字类型: Excel 中的数字（如 `123`, `18600000000`）在读取时可能会被自动转换为整数或浮点数。对于手机号、身份证号等必须保持字符串格式的字段，建议在 Excel 中加单引号 `'`（如 `'13800138000`）或在代码层做强制类型转换。
    *   空行处理: 框架会自动忽略 `id` 为空的行，可利用此特性在 Excel 中添加注释行或分隔行。

4.  Allure 报告:
    *   本地查看报告需要使用 `allure open` 命令（框架运行结束后会自动尝试打开）。直接浏览器打开 HTML 文件通常无法加载数据（因浏览器安全策略限制 AJAX 请求）。
    *   如果未安装 Allure 命令行工具，只能生成 JSON 结果，无法生成 HTML 报告。

5.  依赖安装:
    *   确保 `requirements.txt` 中的所有依赖均已正确安装；在 macOS 上推荐使用虚拟环境（`python3 -m venv venv && source venv/bin/activate`）避免系统环境限制。

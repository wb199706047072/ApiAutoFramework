# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : base_request.py
# @Desc: 请求操作封装模块

import os
import time
import requests
from loguru import logger
from config.settings import OUT_DIR
from typing import Optional, Union, Dict, Text
from requests_toolbelt import MultipartEncoder

class BaseRequest:
    """
    Request操作封装
    """

    TIMEOUT = 30

    @classmethod
    def send_request(cls, req_data):
        """
        处理请求数据，转换成可用数据发送请求
        :param req_data: 请求数据
        :return: 响应对象
        """
        try:
            request_type = req_data.get("request_type", None)
            url = req_data.get("url", "")
            method = req_data.get("method").lower()
            headers = req_data.get("headers", {})
            payload = req_data.get("payload", None)
            files = req_data.get("files", None)
            cookies = req_data.get("cookies", None)

            if request_type and request_type.lower() == "json":
                return cls.request_type_for_json(method=method, url=url, headers=headers, json=payload, cookies=cookies)
            elif request_type and request_type.lower() == "data":
                return cls.request_type_for_data(method=method, url=url, headers=headers, data=payload, cookies=cookies)
            elif request_type and request_type.lower() == "file":
                return cls.request_type_for_file(method=method, url=url, headers=headers, files=files,
                                                 fields=payload, cookies=cookies)
            elif request_type and request_type.lower() == "params":
                return cls.request_type_for_params(method=method, url=url, headers=headers, params=payload,
                                                   cookies=cookies)
            # todo 待后续补充
            # elif request_type and request_type.lower() == "export":
            #     return cls.request_type_for_export(method=method, url=url, headers=headers, **req_data)
            else:
                return cls.request_type_for_none(method=method, url=url, headers=headers, cookies=cookies)

        except requests.exceptions.RequestException as e:
            logger.error(f"请求出错，{str(e)}")
            raise

    @classmethod
    def request_type_for_json(cls, method: Text, url: Text, headers: Optional[Dict], json: Optional[Dict], **kwargs):
        """
        处理 requestType 为json格式
        json: 通过这种方式传递的参数会出现在请求体中，并且需要设置Content-Type为application/json。
        所有传递的参数都需要被编码为JSON格式。在Python中，可以使用内置的json模块来编码数据。
        传递的参数会被编码为JSON格式并包含在请求体中。
        需要注意的是，使用这种方式传递的参数必须是可序列化为JSON的数据类型（如字典、列表、整数、浮点数、布尔值或None）。对于不可序列化的数据类型（如文件或其他自定义对象），需要先进行序列化。
        """
        logger.trace("发送请求：\n"
                     "request_type=json\n"
                     f"method={method}\n"
                     f"url={url}\n"
                     f"headers={headers}\n"
                     f"json={json}\n"
                     f"其他参数：{kwargs}\n")
        return requests.request(
            method=method,
            url=url,
            json=json,
            headers=headers,
            timeout=cls.TIMEOUT,
            **kwargs
        )

    @classmethod
    def request_type_for_params(cls, method: Text, url: Text, headers: Optional[Dict], params: Dict, **kwargs):
        """
        处理 requestType 为 params
        params: 这是通过URL传递参数的方式。所有传递的参数都会被编码到URL中。requests库会自动处理这些参数的编码。
        需要注意的是，这种方式只适用于简单的键值对，对于复杂的数据结构，如列表或字典，需要先进行序列化。
        """
        logger.trace("发送请求：\n"
                     "request_type=params\n"
                     f"method={method}\n"
                     f"url={url}\n"
                     f"headers={headers}\n"
                     f"params={params}\n"
                     f"其他参数：{kwargs}\n")
        return requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            timeout=cls.TIMEOUT,
            **kwargs
        )

    @classmethod
    def request_type_for_data(cls, method: Text, url: Text, headers: Optional[Dict], data: Optional[Dict], **kwargs):
        """
        处理 requestType 为 data 类型
        data: 通过这种方式传递的参数会出现在请求体中。
        这些参数通常需要通过requests库提供的data参数来传递，并且在发送请求时，需要设置Content-Type为application/x-www-form-urlencoded或multipart/form-data。
        对于简单的键值对，可以直接将它们作为字典传递给data参数；对于复杂的数据结构，需要先进行序列化。
        """
        logger.trace("发送请求：\n"
                     "request_type=data\n"
                     f"method={method}\n"
                     f"url={url}\n"
                     f"headers={headers}\n"
                     f"data={data}\n"
                     f"其他参数：{kwargs}\n")
        return requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=cls.TIMEOUT,
            **kwargs
        )

    @classmethod
    def request_type_for_file(cls, method: Text, url: Text, headers: Optional[Dict],
                              fields: Union[Dict, Text, None],
                              files: Text, **kwargs):
        """
        处理 requestType 为 file 类型

        本方法用于构建和发送包含文件上传的 HTTP 请求。它通过多部分表单数据格式来上传文件，
        这是HTTP协议中用于上传文件的标准方法。

        参数:
        - method (Text): HTTP 方法，如 'POST'。
        - url (Text): 请求的URL。
        - headers (Dict): 请求的HTTP头。
        - fields (Dict): 请求的表单字段。通常包含文件字段的信息。
        - files: 要上传的文件路径。
        - cookies (Optional): 请求的cookies。
        - **kwargs: 其他请求参数，如标签和回调函数等。

        返回:
        - requests.Response: 发送请求后的响应对象。
        """
        logger.trace("发送请求：\n"
                     "request_type=file\n"
                     f"method={method}\n"
                     f"url={url}\n"
                     f"headers={headers}\n"
                     f"fields={fields}\n"
                     f"files={files}\n"
                     f"其他参数：{kwargs}\n")
        # 如果fields没有指定，则默认使用 "file" 作为字段名
        _fields = fields or "file"

        # 构建多部分表单数据的编码器，设置边界参数为当前时间戳
        encoder = MultipartEncoder(
            fields={
                _fields: (
                    os.path.basename(files),  # 使用文件的基名作为文件名
                    open(files, "rb")  # 打开文件以二进制读取模式
                )
            },
            boundary='------------------------' + str(time.time())  # 生成唯一的边界标记
        )

        # 设置Content-Type头为multipart/form-data，这是文件上传所需的
        headers['Content-Type'] = encoder.content_type

        # 发送请求，使用multipart/form-data编码的数据
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=encoder.to_string(),  # 将编码数据转换为字符串形式
            timeout=cls.TIMEOUT,  # 使用类定义的超时时间
            **kwargs  # 传递其他请求参数
        )

        return response

    @classmethod
    def request_type_for_none(cls, method: Text, url: Text, headers: Optional[Dict], **kwargs):
        """处理 requestType 为 None"""
        logger.trace("发送请求：\n"
                     "request_type=none\n"
                     f"method={method}\n"
                     f"url={url}\n"
                     f"headers={headers}\n"
                     f"其他参数：{kwargs}\n")
        return requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=cls.TIMEOUT,
            **kwargs
        )

    @classmethod
    def request_type_for_export(cls, method: Text, url: str, headers: Optional[Dict], payload: Optional[Dict] = None,
                                **kwargs):
        """
        判断 requestType 为 export 导出类型
        :param method: 请求方法
        :param url: 请求地址
        :param headers: 请求头
        :param payload: 请求参数
        :param kwargs: 其他参数
        """
        logger.trace(f"requestType 为 export 类型, method={method}, url={url}")

        # 默认下载路径
        download_dir = os.path.join(OUT_DIR, "download_files")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # 准备请求参数
        request_kwargs = {
            "method": method,
            "url": url,
            "headers": headers,
            "timeout": cls.TIMEOUT,
            "stream": True,  # 开启流式下载
            **kwargs
        }

        # 根据请求方法设置参数
        if method.upper() == "GET":
            request_kwargs["params"] = payload
        else:
            # POST等方法通常使用json传递参数，如果需要data格式，可以在kwargs中指定或根据header判断
            # 这里默认 export 类型 POST 请求使用 json
            request_kwargs["json"] = payload

        try:
            response = requests.request(**request_kwargs)
            logger.debug(f"Export请求响应状态码: {response.status_code}")

            if response.status_code == 200:
                # 获取文件名
                # 尝试从 Content-Disposition 获取文件名
                content_disposition = response.headers.get("Content-Disposition")
                filename = None
                if content_disposition:
                    import re
                    # 尝试匹配 filename="xxx" 或 filename*=utf-8''xxx
                    filename_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^";\r\n]+)["\']?', content_disposition)
                    if filename_match:
                        from urllib.parse import unquote
                        filename = unquote(filename_match.group(1))

                # 如果无法获取文件名，使用时间戳生成
                if not filename:
                    filename = f"export_{int(time.time())}.bin"

                file_path = os.path.join(download_dir, filename)

                # 写入文件
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"文件下载成功，保存路径: {file_path}")
                # 将文件路径附加到响应对象中，方便后续断言或提取
                response.download_file_path = file_path

            else:
                logger.warning(f"Export请求失败，状态码: {response.status_code}, 响应内容: {response.text[:200]}")

            return response

        except Exception as e:
            logger.error(f"Export请求发生异常: {e}")
            raise

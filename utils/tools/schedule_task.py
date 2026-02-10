# -*- coding: utf-8 -*-
# @Author  : 会飞的🐟
# @File    : schedule_task.py
# @Desc: 

import sys
import time
import schedule
import subprocess
from loguru import logger

def run_task(command_args):
    """
    执行测试任务
    """
    logger.info(f"开始执行定时任务，执行命令: {' '.join(command_args)}")
    try:
        # 使用当前 Python 解释器执行 run.py
        cmd = [sys.executable, "run.py"] + command_args
        subprocess.run(cmd, check=True)
        logger.info("定时任务执行完成")
    except subprocess.CalledProcessError as e:
        logger.error(f"定时任务执行失败: {e}")
    except Exception as e:
        logger.error(f"定时任务执行出现异常: {e}")

def start_schedule(command_args, run_time="22:00"):
    """
    开启定时任务
    :param command_args: 传递给 run.py 的参数列表
    :param run_time: 每天运行的时间，格式 "HH:MM"
    """
    logger.info(f"已开启定时任务模式，将于每天 {run_time} 自动运行测试...")
    
    # 安排任务
    schedule.every().day.at(run_time).do(run_task, command_args)
    
    # 保持运行
    while True:
        schedule.run_pending()
        time.sleep(60)

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.0",
#     "python-dotenv>=1.0",
#     "loguru>=0.7",
#     "httpx>=0.27",
#     "markdown>=3.7",
# ]
# ///
"""
创建 TAPD 任务（Task）

必填环境变量：
  TAPD_API_TOKEN      TAPD API 令牌
  TAPD_DEFAULT_OWNER  默认处理人/开发人员用户名（如 pinhenzhang）
  TAPD_ITERATION_ID   默认迭代 ID
  TAPD_CATEGORY_ID    默认任务分类 ID
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx
import markdown
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

# POST数据
# {"workspace_id":"69995517","is_editor_or_markdown":"1","Story":{"category_id":"1069995517002739700","priority":"Middle","iteration_id":"1069995517001563259","custom_field_24":"功能需求","custom_field_two":["智研","TAPD","CODING"],"custom_field_35":[],"version":"","cc":"","owner":"pinhenzhang;","developer":"pinhenzhang;","custom_field_29":"","custom_field_18":"2026-02-26","effort":"1","begin":"2026-02-25","due":"2026-02-26","custom_field_34":"","custom_field_32":"","custom_field_40":"","custom_field_43":"","label":[],"custom_field_45":"","custom_field_50":"","custom_field_51":"","attachment":"","name":"【产品模块】需求标题（请留意，需求为需要产品/技术验收的事项，请勿将任务拆解或临时任务登记为需求）","description":"<p>测试数据</p>","parent_id":"","workitem_type_id":"1069995517000288865","templated_id":"1069995517000798713","description_type":"1"},"is_template_relation":true,"workflow_auto_succeed_story_name":"1","auto_succeed_story_fields":false,"from":"","use_alias":0,"app_id":"0","draft_id":"","workitems_relation":"{\"pre_workitems\":{},\"post_workitems\":{},\"pre_workitems_count\":0,\"post_workitems_count\":0,\"pre_search\":{\"pre_search\":{\"id\":\"pre_search\",\"relation_type\":\"B_start_after_A_finish\"}},\"post_search\":{\"post_search\":{\"id\":\"post_search\",\"relation_type\":\"B_start_after_A_finish\"}}}","workitems_relation_to_save":"[]","secret_config":{"secret_root_id":"0","allow_list":"","add_participant_fields":"false","all_permission_roles":[],"add_bug_participant_fields":"false"},"PresetItems":"[]","program_id":"","edit_action":null,"use_scene":null,"add_story_token":"1001456007185427271","from_workspace_id":"","from_workitem_id":"","isEnd":false,"dsc_token":"AtrJHttBxViWM4Hm"}

class TaskArgs(BaseModel):
    """任务参数模型"""

    name: str
    description: str


class TapdConfig(BaseModel):
    """TAPD 配置模型"""

    api_token: str
    default_owner: str
    iteration_id: str
    category_id: str


TAPD_API_BASE_URL = "http://apiv2.tapd.woa.com"
TAPD_WORKSPACE_ID = "69995517"
# Task 类型的 workitem_type_id
TAPD_WORKITEM_TYPE_ID = "1069995517000288865"


class TaskCreateRequest(BaseModel):
    """TAPD 创建任务请求体"""

    workspace_id: str
    name: str
    priority: str = Field(default="High", pattern="^(High|Middle|Low|Nice To Have)$")
    effort: str = "1"
    begin: date
    due: date
    description: str | None = None
    description_type: str = "1"
    owner: str | None = None
    developer: str | None = None
    iteration_id: str | None = None
    category_id: str | None = None
    workitem_type_id: str | None = None


def load_dev_env() -> None:
    """从当前目录或上级目录查找 .dev.env 文件并加载。"""
    for directory in [Path.cwd(), *Path.cwd().parents]:
        env_file = directory / ".dev.env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.debug(f"已加载环境变量文件：{env_file}")
            break


def get_config() -> TapdConfig:
    """从环境变量获取 TAPD 配置。"""
    try:
        config = TapdConfig(
            api_token=os.environ.get("TAPD_API_TOKEN", "").strip(),
            default_owner=os.environ.get("TAPD_DEFAULT_OWNER", "").strip(),
            iteration_id=os.environ.get("TAPD_ITERATION_ID", "").strip(),
            category_id=os.environ.get("TAPD_CATEGORY_ID", "").strip(),
        )
        logger.debug(f"配置加载完成")
        return config
    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0]
            env_var = f"TAPD_{field.upper()}"
            logger.error(f"环境变量未设置：{env_var}")
        sys.exit(1)


def markdown_to_tapd_html(text: str) -> str:
    """将 Markdown 文本转换为 TAPD 可展示的 HTML。"""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return "<p></p>"

    return markdown.markdown(
        normalized,
        extensions=["extra", "sane_lists", "nl2br"],
    )


def build_request(args: TaskArgs, config: TapdConfig) -> TaskCreateRequest:
    """构建 TAPD 创建任务请求。"""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    return TaskCreateRequest(
        workspace_id=TAPD_WORKSPACE_ID,
        name=args.name,
        begin=today,
        due=tomorrow,
        description=markdown_to_tapd_html(args.description),
        owner=config.default_owner or None,
        developer=config.default_owner or None,
        iteration_id=config.iteration_id or None,
        category_id=config.category_id or None,
        workitem_type_id=TAPD_WORKITEM_TYPE_ID,
    )


def create_task(args: TaskArgs, config: TapdConfig) -> None:
    """创建 TAPD 任务。"""
    request = build_request(args, config)
    json_data = request.model_dump(exclude_none=True, mode="json")

    logger.debug(f"请求参数：{json_data}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_token}",
    }

    with httpx.Client(follow_redirects=True) as client:
        resp = client.post(
            f"{TAPD_API_BASE_URL}/stories",
            json=json_data,
            headers=headers,
        )

    body = resp.json()

    if not resp.is_success:
        logger.error(f"HTTP {resp.status_code}：{body.get('info', resp.reason_phrase)}")
        sys.exit(1)

    if body.get("status") != 1:
        logger.error(f"创建失败：{body.get('info', '未知错误')}")
        sys.exit(1)

    task = body["data"]["Story"]
    task_id = task["id"]

    # 只输出重要信息：单号
    logger.info(f"TAPD ID: #{task_id}")


def read_description_file(description_file: str) -> str:
    """从文件读取需求描述，避免 shell 传参导致换行丢失。"""
    path = Path(description_file).expanduser()

    if not path.exists() or not path.is_file():
        logger.error(f"描述文件不存在：{path}")
        sys.exit(1)

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.error(f"描述文件编码错误（需 UTF-8）：{path}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="创建 TAPD 任务")
    parser.add_argument("--name", required=True, help="任务标题（必填）")
    parser.add_argument("--description-file", required=True, help="详细描述文件路径（UTF-8，支持 Markdown）")

    args = parser.parse_args()

    load_dev_env()

    task_args = TaskArgs(
        name=args.name,
        description=read_description_file(args.description_file),
    )
    config = get_config()
    create_task(task_args, config)


if __name__ == "__main__":
    main()

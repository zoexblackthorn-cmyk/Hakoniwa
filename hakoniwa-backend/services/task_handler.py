"""
任务执行层 - 处理已调度的任务
"""


def send_email(to: str, content: str):
    """示例任务：发送邮件（仅打印，无真实 SMTP）"""
    print(f"[Task] send_email -> to={to}, content={content!r}")


def handle_task(task_type: str, content: str):
    """任务分发入口"""
    if task_type == "send_email":
        send_email("user@example.com", content)
    else:
        print(f"[Task] generic_reminder -> {content!r}")

# 统一导出Provider实现，启动装配代码无需了解各实现文件的位置。

from app.infrastructure.providers.qwen_text import QwenTextLLMProvider

__all__ = [

    "QwenTextLLMProvider",
]

from __future__ import annotations

import inspect
from dataclasses import dataclass

from pydantic import SecretStr

from app.bootstrap.config import Settings
from app.infrastructure.providers import (
    QwenTextLLMProvider,
)
from app.infrastructure.storage import (
    LocalFilesystemStorageProvider,
)
from app.ports.storage import StorageProvider
from app.ports.text import TextLLMProvider


def _secret(value: SecretStr | None) -> str:
    """
    安全地读取SecretStr中的真实字符串。如果配置值不存在则返回空字符串，避免调用方重复判断None。
    """
    return value.get_secret_value() if value is not None else ""


@dataclass(slots=True)
class ProviderBundle:
    """集中保存应用运行期间使用的四类Provider。"""
    text: TextLLMProvider
    asr : None
    vision : None
    storage: StorageProvider

    async def close(self) -> None:
        """关闭ProviderBundle中的全部Provider资源"""
        seen: set[int] = set()  # 保存已经关闭过的Provider对象ID。

        for provider in (self.text, self.asr, self.vision, self.storage):  # 依次处理四类Provider。
            if id(provider) in seen:  # 判断同一个Provider对象是否已经处理过。
                continue  # 已经处理过时跳过，避免重复关闭。

            seen.add(id(provider))  # 记录当前Provider对象ID。

            close = getattr(provider, "close", None)  # 获取Provider的close方法。

            if close is None:  # 判断当前Provider是否没有提供close方法。
                continue  # 没有需要释放的资源时直接跳过。

            result = close()  # 调用Provider的close方法。

            if inspect.isawaitable(result):  # 判断close方法返回的是否为可等待对象。
                await result  # 异步等待资源关闭完成。


def create_storage(settings: Settings) -> StorageProvider:
    return LocalFilesystemStorageProvider(
        root=settings.local_storage_root,  # 设置本地对象文件根目录。
        public_base_url=settings.local_storage_public_base_url,  # 设置签名地址的公开基础URL。
        # 读取签名密钥。
        signing_secret=settings.local_storage_signing_secret.get_secret_value(),
        upload_path=f"{settings.api_prefix}/storage/uploads",  # 设置签名上传接口路径。
        download_path=f"{settings.api_prefix}/storage/downloads",  # 设置签名下载接口路径。
    )


def create_provider_bundle(settings: Settings) -> ProviderBundle:
    """根据Settings创建完整的ProviderBundle。最后统一包装成ProviderBundle返回。"""
    storage = create_storage(settings)  # 根据配置创建文件存储Provider。

    text = QwenTextLLMProvider(
        api_key=_secret(settings.dashscope_api_key),  # 读取百炼API Key。
        base_url=settings.qwen_base_url,  # 设置千问接口基础地址。
        model=settings.qwen_text_model,  # 设置千问模型名称。
        timeout_seconds=settings.provider_timeout_seconds,  # 设置请求超时时间。
        max_retries=settings.provider_max_retries,  # 设置最大重试次数。
        trust_env=settings.provider_trust_env,  # 决定是否读取系统代理环境变量。
    )

    return ProviderBundle(  # 将四类Provider组合成统一资源包。
        text=text,
        asr=None,
        vision=None,
        storage=storage,
    )


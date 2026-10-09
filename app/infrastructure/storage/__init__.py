# 统一导出本地、内存和S3三种存储实现。
from app.infrastructure.storage.local_filesystem import LocalFilesystemStorageProvider


__all__ = [
    "LocalFilesystemStorageProvider",

]

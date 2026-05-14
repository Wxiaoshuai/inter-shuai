"""清空 Milvus 数据库中的所有集合."""

from pymilvus import MilvusClient

from src.config import settings


def clear_milvus():
    """删除 Milvus 中的所有集合."""
    client = MilvusClient(uri=settings.milvus_uri)

    # 获取所有集合
    collections = client.list_collections()
    print(f"找到 {len(collections)} 个集合: {collections}")

    for name in collections:
        try:
            client.drop_collection(name)
            print(f"✅ 已删除集合: {name}")
        except Exception as e:
            print(f"❌ 删除集合 {name} 失败: {e}")

    print("\n清空完成！")


if __name__ == "__main__":
    clear_milvus()
import os
import json
from typing import Dict, Set, Any

class CacheManager:
    def __init__(self, cache_dir: str = ".cache"):
        """初始化缓存管理器"""
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "bgm_cache.json")
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def save_cache(self, collections: Dict[str, Any]):
        """保存收藏数据到缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(collections, f, ensure_ascii=False, indent=2)
            print("缓存数据已保存")
        except Exception as e:
            print(f"保存缓存数据失败: {str(e)}")
    
    def load_cache(self) -> Dict[str, Any]:
        """从缓存文件加载收藏数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"data": [], "total": 0}
        except Exception as e:
            print(f"加载缓存数据失败: {str(e)}")
            return {"data": [], "total": 0}
    
    def compare_collections(self, new_collections: Dict[str, Any], old_collections: Dict[str, Any]) -> tuple[list, list, list]:
        """比较新旧收藏数据，返回需要更新的条目"""
        new_items = {}
        old_items = {}
        
        # 构建新旧数据的映射
        for item in new_collections.get("data", []):
            new_items[item["subject"]["id"]] = item
        
        for item in old_collections.get("data", []):
            old_items[item["subject"]["id"]] = item
        
        # 找出新增、更新和删除的条目
        added = []
        updated = []
        deleted = list(set(old_items.keys()) - set(new_items.keys()))
        
        for subject_id, new_item in new_items.items():
            if subject_id not in old_items:
                added.append(new_item)
            else:
                # 比较收藏状态是否变化
                old_item = old_items[subject_id]
                if new_item["type"] != old_item["type"]:
                    updated.append(new_item)
        
        return added, updated, [int(id) for id in deleted]
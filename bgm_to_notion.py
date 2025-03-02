import os
import requests
import json
from dotenv import load_dotenv
from notion_client import Client
from cache_manager import CacheManager
from env_manager import update_env_file

# 加载环境变量
load_dotenv()

# 获取环境变量
BGM_TOKEN = os.getenv('BGM_TOKEN')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')  # 新增：从环境变量获取数据库ID

# 初始化 Notion 客户端
notion = Client(auth=NOTION_TOKEN)

# 初始化缓存管理器
cache_manager = CacheManager()

# Bangumi API 基础 URL
BGM_API_BASE = "https://api.bgm.tv"

# 请求头
headers = {
    "User-Agent": "BGMToNotion/0.1",
    "Authorization": f"Bearer {BGM_TOKEN}"
}

def get_user_collections(username, subject_type=None, collection_type=None, limit=50):
    """获取用户收藏"""
    url = f"{BGM_API_BASE}/v0/users/{username}/collections"
    
    params = {
        "limit": limit,
        "offset": 0  # Add default offset parameter
    }
    
    if subject_type:
        params["subject_type"] = subject_type
    
    if collection_type:
        params["type"] = collection_type
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取收藏失败: {response.status_code}")
        print(response.text)
        return None

def get_subject_detail(subject_id):
    """获取条目详细信息"""
    url = f"{BGM_API_BASE}/v0/subjects/{subject_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取条目详情失败: {response.status_code}")
        print(response.text)
        return None

def create_notion_database():
    """创建新的 Notion 数据库"""
    try:
        # 检查是否有指定的父页面ID
        if NOTION_PAGE_ID:
            parent_page_id = NOTION_PAGE_ID
            print(f"使用指定的父页面: {parent_page_id}")
        else:
            # 如果没有指定父页面ID，则搜索现有页面
            search_results = notion.search(query="", filter={"property": "object", "value": "page"}, page_size=1)
            
            if not search_results["results"]:
                print("未找到可用的页面，无法创建数据库")
                return None
            
            # 使用找到的第一个页面作为父页面
            parent_page_id = search_results["results"][0]["id"]
            print(f"使用搜索到的父页面: {parent_page_id}")
        
        # 在该页面下创建数据库
        database = notion.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[
                {
                    "type": "text",
                    "text": {
                        "content": "Bangumi 收藏"
                    }
                }
            ],
            properties={
                "标题": {
                    "title": {}
                },
                "中文名": {
                    "rich_text": {}
                },
                "类型": {
                    "select": {}
                },
                "评分": {
                    "number": {}
                },
                "收藏状态": {
                    "select": {}
                },
                "ID": {
                    "number": {}
                },
                "链接": {
                    "url": {}
                },
                "发行日期": {
                    "date": {}
                },
                "评分人数": {
                    "number": {}
                },
                "排名": {
                    "number": {}
                },
                "封面": {
                    "files": {}
                },
                "标签": {
                    "multi_select": {}
                }
            }
        )
        
        database_id = database["id"]
        print(f"已创建新的 Notion 数据库: {database_id}")
        
        return database_id
    except Exception as e:
        print(f"创建数据库失败: {str(e)}")
        return None

def get_subject_image(subject_id):
    """获取条目封面图片"""
    url = f"{BGM_API_BASE}/v0/subjects/{subject_id}/image"
    
    params = {
        "type": "large"  # 获取大图
    }
    
    response = requests.get(url, headers=headers, params=params, allow_redirects=False)
    
    if response.status_code == 302:
        return response.headers.get('Location')
    else:
        print(f"获取条目封面失败: {response.status_code}")
        return None

def add_to_notion_database(database_id, collection):
    """将收藏添加或更新到 Notion 数据库"""
    subject = collection["subject"]
    
    # 查询是否已存在该条目
    query_params = {
        "filter": {
            "property": "ID",
            "number": {
                "equals": subject["id"]
            }
        }
    }
    
    existing_pages = notion.databases.query(database_id=database_id, **query_params).get("results", [])
    
    # 处理重复条目，只保留一个（如果有多个相同ID的条目）
    if len(existing_pages) > 1:
        print(f"发现ID为 {subject['id']} 的重复条目，共 {len(existing_pages)} 条，将只保留最新的一条")
        # 按更新时间排序，保留最新的一条
        existing_pages.sort(key=lambda x: x.get("last_edited_time", ""), reverse=True)
        # 删除多余的条目
        for page in existing_pages[1:]:
            try:
                notion.pages.update(page_id=page["id"], archived=True)
                print(f"已归档重复条目: ID {subject['id']}")
            except Exception as e:
                print(f"归档重复条目失败: ID {subject['id']} - {str(e)}")
        # 只保留最新的一条用于更新
        existing_pages = [existing_pages[0]]
    
    # 获取更详细的条目信息
    subject_detail = get_subject_detail(subject["id"])
    
    # 获取条目封面图片
    cover_image = get_subject_image(subject["id"])
    
    # 收藏状态映射
    collection_type_map = {
        1: "想看",
        2: "看过",
        3: "在看",
        4: "搁置",
        5: "抛弃"
    }
    
    # 条目类型映射
    subject_type_map = {
        1: "书籍",
        2: "动画",
        3: "音乐",
        4: "游戏",
        6: "三次元"
    }
    
    properties = {
        "标题": {
            "title": [
                {
                    "text": {
                        "content": subject["name"]
                    }
                }
            ]
        },
        "中文名": {
            "rich_text": [
                {
                    "text": {
                        "content": subject["name_cn"] if subject["name_cn"] else ""
                    }
                }
            ]
        },
        "类型": {
            "select": {
                "name": subject_type_map.get(subject["type"], "未知")
            }
        },
        "ID": {
            "number": subject["id"]
        },
        "链接": {
            "url": f"https://bgm.tv/subject/{subject['id']}"
        },
        "收藏状态": {
            "select": {
                "name": collection_type_map.get(collection["type"], "未知")
            }
        }
    }
    
    # 添加封面图片（如果有）
    if cover_image:
        properties["封面"] = {
            "files": [
                {
                    "name": f"封面-{subject['id']}",
                    "type": "external",
                    "external": {
                        "url": cover_image
                    }
                }
            ]
        }
    
    # 添加评分信息（如果有）
    if subject_detail and "rating" in subject_detail:
        properties["评分"] = {
            "number": subject_detail["rating"]["score"]
        }
        properties["评分人数"] = {
            "number": subject_detail["rating"]["total"]
        }
        if "rank" in subject_detail["rating"] and subject_detail["rating"]["rank"]:
            properties["排名"] = {
                "number": subject_detail["rating"]["rank"]
            }
    
    # 添加发行日期（如果有）
    if subject_detail and "date" in subject_detail and subject_detail["date"]:
        properties["发行日期"] = {
            "date": {
                "start": subject_detail["date"]
            }
        }
    
    # 添加标签信息（如果有）
    if subject_detail and "tags" in subject_detail:
        tags = []
        for tag in subject_detail["tags"]:
            tags.append({"name": tag["name"]})
        if tags:
            properties["标签"] = {
                "multi_select": tags
            }
    
    # 更新或创建条目
    try:
        page_properties = {
            "properties": properties
        }
        
        # 如果有封面图片，设置为页面封面
        if cover_image:
            page_properties["cover"] = {
                "type": "external",
                "external": {
                    "url": cover_image
                }
            }
        
        if existing_pages:
            # 更新现有条目
            page_id = existing_pages[0]["id"]
            notion.pages.update(page_id=page_id, **page_properties)
            print(f"已更新: {subject['name']}")
        else:
            # 创建新条目
            page_properties["parent"] = {"database_id": database_id}
            notion.pages.create(**page_properties)
            print(f"已添加: {subject['name']}")
    except Exception as e:
        print(f"添加失败: {subject['name']} - {str(e)}")

def mark_deleted_items(database_id, bgm_subject_ids):
    """将在 Notion 中存在但在 Bangumi 中不存在的条目标记为删除"""
    # 获取 Notion 数据库中的所有条目
    all_pages = []
    has_more = True
    start_cursor = None
    
    while has_more:
        query_params = {}
        if start_cursor:
            query_params["start_cursor"] = start_cursor
        
        response = notion.databases.query(database_id=database_id, **query_params)
        all_pages.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
    
    print(f"Notion 数据库中共有 {len(all_pages)} 条记录")
    
    # 找出在 Notion 中存在但在 Bangumi 中不存在的条目
    deleted_count = 0
    for page in all_pages:
        try:
            # 获取条目 ID
            subject_id = page["properties"]["ID"]["number"]
            # 获取当前收藏状态
            current_status = page["properties"]["收藏状态"]["select"]["name"] if page["properties"]["收藏状态"]["select"] else ""
            
            # 如果条目不在 Bangumi 收藏中且状态不是"删除"，则标记为删除
            if subject_id not in bgm_subject_ids and current_status != "删除":
                notion.pages.update(
                    page_id=page["id"],
                    properties={
                        "收藏状态": {
                            "select": {
                                "name": "删除"
                            }
                        }
                    }
                )
                deleted_count += 1
                print(f"已标记为删除: ID {subject_id}")
        except Exception as e:
            print(f"处理条目时出错: {str(e)}")
    
    print(f"共标记 {deleted_count} 条记录为删除状态")

def get_user_info():
    """从 Bangumi API 获取当前用户信息"""
    url = f"{BGM_API_BASE}/v0/me"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取用户信息失败: {response.status_code}")
        print(response.text)
        return None

def update_notion_database(database_id):
    """更新 Notion 数据库的属性"""
    try:
        # 先获取数据库现有属性
        database = notion.databases.retrieve(database_id=database_id)
        existing_properties = database.get('properties', {})
        
        # 保留现有的title属性
        title_property = existing_properties.get('标题', {'title': {}})
        
        # 定义要更新的属性
        properties = {
            "标题": title_property,  # 使用现有的title属性
            "中文名": {
                "rich_text": {}
            },
            "类型": {
                "select": {}
            },
            "评分": {
                "number": {}
            },
            "收藏状态": {
                "select": {}
            },
            "ID": {
                "number": {}
            },
            "链接": {
                "url": {}
            },
            "发行日期": {
                "date": {}
            },
            "评分人数": {
                "number": {}
            },
            "排名": {
                "number": {}
            },
            "封面": {
                "files": {}
            },
            "标签": {
                "multi_select": {}
            }
        }
        
        response = notion.databases.update(
            database_id=database_id,
            properties=properties
        )
        print(f"已更新数据库属性")
        return True
    except Exception as e:
        print(f"更新数据库属性失败: {str(e)}")
        return False

def main():
    print("开始同步 Bangumi 收藏到 Notion...")
    
    # 获取用户信息
    user_info = get_user_info()
    if not user_info:
        print("获取用户信息失败，请检查 BGM_TOKEN 是否正确")
        return
    
    username = user_info["username"]
    print(f"已获取用户信息: {username}")
    
    # 检查或创建数据库
    global NOTION_DATABASE_ID
    if not NOTION_DATABASE_ID:
        # 尝试从缓存加载数据库ID
        NOTION_DATABASE_ID = cache_manager.load_database_id()
        
    if not NOTION_DATABASE_ID:
        print("未找到 Notion 数据库 ID，将创建新的数据库...")
        NOTION_DATABASE_ID = create_notion_database()
        if not NOTION_DATABASE_ID:
            print("错误：创建数据库失败")
            return
        # 保存新创建的数据库ID到缓存
        cache_manager.save_database_id(NOTION_DATABASE_ID)
    
    # 更新数据库属性
    if not update_notion_database(NOTION_DATABASE_ID):
        print("错误：更新数据库属性失败，请检查数据库ID是否正确")
        print("数据库ID可能已失效，将清除所有缓存并重新创建数据库...")
        # 删除所有缓存文件
        if os.path.exists(cache_manager.db_cache_file):
            os.remove(cache_manager.db_cache_file)
            print("已清除数据库ID缓存")
        if os.path.exists(cache_manager.cache_file):
            os.remove(cache_manager.cache_file)
            print("已清除收藏数据缓存")
        
        # 重新创建数据库
        NOTION_DATABASE_ID = create_notion_database()
        if not NOTION_DATABASE_ID:
            print("错误：创建数据库失败")
            return
        # 保存新创建的数据库ID到缓存
        cache_manager.save_database_id(NOTION_DATABASE_ID)
        
        # 再次尝试更新数据库属性
        if not update_notion_database(NOTION_DATABASE_ID):
            print("错误：更新新创建的数据库属性失败")
            return
    
    print(f"使用 Notion 数据库: {NOTION_DATABASE_ID}")
    
    # 加载本地缓存数据
    print("加载本地缓存数据...")
    cached_collections = cache_manager.load_cache()
    
    # 获取用户收藏
    print("获取 Bangumi 收藏数据...")
    collections = get_user_collections(username)
    
    if not collections:
        print("未获取到收藏数据")
        return
    
    total = collections["total"]
    print(f"共有 {total} 条收藏")
    
    # 如果收藏数量超过一页，继续获取后续页面
    current_offset = 50
    while current_offset < total:
        # 获取下一页数据
        params = {"offset": current_offset, "limit": 50}
        url = f"{BGM_API_BASE}/v0/users/{username}/collections"
        response = requests.get(url, headers=headers, params=params)
        next_page = response.json() if response.status_code == 200 else None
        
        if not next_page:
            break
        
        # 合并数据
        collections["data"].extend(next_page["data"])
        current_offset += 50
    
    # 保存最新数据到缓存
    print("保存最新数据到本地缓存...")
    cache_manager.save_cache(collections)
    
    # 比较新旧数据，找出需要更新的条目
    print("比较本地缓存与最新数据...")
    added_items, updated_items, deleted_ids = cache_manager.compare_collections(collections, cached_collections)
    
    print(f"发现 {len(added_items)} 个新增条目, {len(updated_items)} 个更新条目, {len(deleted_ids)} 个删除条目")
    
    # 记录所有 Bangumi 收藏的条目 ID
    bgm_subject_ids = set()
    for collection in collections["data"]:
        bgm_subject_ids.add(collection["subject"]["id"])
    
    # 处理新增条目
    for collection in added_items:
        add_to_notion_database(NOTION_DATABASE_ID, collection)
    
    # 处理更新条目
    for collection in updated_items:
        add_to_notion_database(NOTION_DATABASE_ID, collection)
    
    # 处理删除条目
    if deleted_ids:
        print("\n开始处理已从 Bangumi 中删除的条目...")
        mark_deleted_items(NOTION_DATABASE_ID, bgm_subject_ids)
    
    print("同步完成!")

if __name__ == "__main__":
    main()
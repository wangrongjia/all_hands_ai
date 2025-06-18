#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime

def get_user_lists_with_repos(username):
    """使用 GraphQL API 获取用户的自定义 Lists 及其中的仓库"""
    token = os.environ.get('GITHUB_TOKEN')
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 首先获取用户的所有 Lists
    query = """
    query($username: String!) {
        user(login: $username) {
            lists(first: 50) {
                nodes {
                    name
                    description
                    items(first: 100) {
                        totalCount
                        nodes {
                            ... on Repository {
                                name
                                owner {
                                    login
                                }
                                full_name: nameWithOwner
                                stargazerCount
                                url
                                description
                                primaryLanguage {
                                    name
                                }
                            }
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {"username": username}
    
    response = requests.post(
        'https://api.github.com/graphql',
        headers=headers,
        json={'query': query, 'variables': variables}
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    if 'errors' in data:
        print(f"GraphQL errors: {data['errors']}")
        return None
    
    return data['data']['user']['lists']['nodes']

def get_more_repos_from_list(username, list_name, cursor):
    """获取 List 中更多的仓库（分页）"""
    token = os.environ.get('GITHUB_TOKEN')
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json'
    }
    
    query = """
    query($username: String!, $cursor: String!) {
        user(login: $username) {
            lists(first: 50) {
                nodes {
                    name
                    items(first: 100, after: $cursor) {
                        nodes {
                            ... on Repository {
                                name
                                owner {
                                    login
                                }
                                full_name: nameWithOwner
                                stargazerCount
                                url
                                description
                                primaryLanguage {
                                    name
                                }
                            }
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {"username": username, "cursor": cursor}
    
    response = requests.post(
        'https://api.github.com/graphql',
        headers=headers,
        json={'query': query, 'variables': variables}
    )
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    if 'errors' in data:
        return None
    
    # 找到对应的 list
    for lst in data['data']['user']['lists']['nodes']:
        if lst['name'] == list_name:
            return lst['items']
    
    return None

def generate_custom_lists_markdown(lists_data, username):
    """生成基于用户自定义分类的 Markdown 文档"""
    total_repos = sum(len(lst['items']['nodes']) for lst in lists_data)
    total_stars = sum(
        repo['stargazerCount'] for lst in lists_data 
        for repo in lst['items']['nodes']
    )
    
    md_content = f"# {username} 的 GitHub Starred 仓库 (按自定义分类)\n\n"
    md_content += f"📊 **统计信息**\n"
    md_content += f"- 自定义分类数: **{len(lists_data)}** 个\n"
    md_content += f"- 分类中的仓库数: **{total_repos:,}** 个\n"
    md_content += f"- 总 Star 数: **{total_stars:,}** 个\n"
    md_content += f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 生成目录
    md_content += "## 📚 目录\n\n"
    for i, lst in enumerate(lists_data, 1):
        list_name = lst['name']
        repo_count = len(lst['items']['nodes'])
        list_stars = sum(repo['stargazerCount'] for repo in lst['items']['nodes'])
        description = lst['description'] or '无描述'
        
        md_content += f"{i}. [{list_name}](#{list_name.lower().replace(' ', '-')}) ({repo_count} 个仓库, {list_stars:,} stars) - {description}\n"
    
    md_content += "\n---\n\n"
    
    # 按每个自定义分类生成内容
    for lst in lists_data:
        list_name = lst['name']
        description = lst['description'] or '无描述'
        repos = lst['items']['nodes']
        
        if not repos:
            continue
            
        list_stars = sum(repo['stargazerCount'] for repo in repos)
        avg_stars = list_stars // len(repos) if repos else 0
        
        md_content += f"## {list_name}\n\n"
        md_content += f"📝 **分类描述**: {description}\n\n"
        md_content += f"📈 **分类统计**: {len(repos)} 个仓库 | 总计 {list_stars:,} stars | 平均 {avg_stars:,} stars\n\n"
        
        # 按 star 数量倒序排列
        sorted_repos = sorted(repos, key=lambda x: x['stargazerCount'], reverse=True)
        
        md_content += "| 排名 | 仓库名称 | Star 数量 | 语言 | 描述 | 链接 |\n"
        md_content += "|------|----------|-----------|------|------|------|\n"
        
        for i, repo in enumerate(sorted_repos, 1):
            full_name = repo['full_name']
            stars = repo['stargazerCount']
            url = repo['url']
            language = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'N/A'
            desc = repo.get('description') or '暂无描述'
            # 截断描述
            if len(desc) > 50:
                desc = desc[:50] + '...'
            
            md_content += f"| {i} | **{full_name}** | {stars:,} ⭐ | {language} | {desc} | [🔗 查看]({url}) |\n"
        
        md_content += "\n"
    
    # 添加所有仓库的 Top 10 (去重)
    all_repos = [repo for lst in lists_data for repo in lst['items']['nodes']]
    if all_repos:
        # 去重：使用字典以 full_name 为键来去重
        unique_repos = {}
        for repo in all_repos:
            full_name = repo['full_name']
            if full_name not in unique_repos:
                unique_repos[full_name] = repo
        
        md_content += "## 🏆 所有分类中 Top 10 最受欢迎的仓库\n\n"
        top_repos = sorted(unique_repos.values(), key=lambda x: x['stargazerCount'], reverse=True)[:10]
        
        md_content += "| 排名 | 仓库名称 | Star 数量 | 语言 | 所属分类 | 链接 |\n"
        md_content += "|------|----------|-----------|------|----------|------|\n"
        
        for i, repo in enumerate(top_repos, 1):
            full_name = repo['full_name']
            stars = repo['stargazerCount']
            language = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'N/A'
            url = repo['url']
            
            # 找到这个仓库属于哪个分类
            repo_lists = []
            for lst in lists_data:
                for r in lst['items']['nodes']:
                    if r['full_name'] == full_name:
                        repo_lists.append(lst['name'])
            
            categories = ', '.join(set(repo_lists))  # 使用 set 去重分类名称
            
            md_content += f"| {i} | **{full_name}** | {stars:,} ⭐ | {language} | {categories} | [🔗 查看]({url}) |\n"
    
    md_content += "\n---\n\n"
    md_content += f"*本文档基于用户自定义分类生成，数据来源于 GitHub GraphQL API*\n"
    
    return md_content

def main():
    username = 'wangrongjia'
    
    print(f"正在获取用户 {username} 的自定义 Lists...")
    lists_data = get_user_lists_with_repos(username)
    
    if not lists_data:
        print("无法获取用户的 Lists 数据")
        return
    
    print(f"找到 {len(lists_data)} 个自定义分类:")
    for lst in lists_data:
        repo_count = len(lst['items']['nodes'])
        print(f"  - {lst['name']}: {repo_count} 个仓库 ({lst['description'] or '无描述'})")
    
    # 生成 Markdown
    markdown_content = generate_custom_lists_markdown(lists_data, username)
    
    # 保存到文件
    output_file = f'{username}_starred_repos_custom_lists.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n自定义分类 Markdown 文档已保存到: {output_file}")
    
    # 显示统计信息
    total_repos = sum(len(lst['items']['nodes']) for lst in lists_data)
    total_stars = sum(
        repo['stargazerCount'] for lst in lists_data 
        for repo in lst['items']['nodes']
    )
    
    print(f"\n📊 总体统计:")
    print(f"  自定义分类数: {len(lists_data)}")
    print(f"  分类中的仓库数: {total_repos:,}")
    print(f"  总 Star 数: {total_stars:,}")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
import requests
import json
import os
from collections import defaultdict

def get_all_starred_repos(username):
    """获取用户的所有 starred 仓库"""
    token = os.environ.get('GITHUB_TOKEN')
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    all_repos = []
    page = 1
    
    while True:
        url = f'https://api.github.com/users/{username}/starred?per_page=100&page={page}'
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
            
        repos = response.json()
        if not repos:  # 没有更多数据
            break
            
        all_repos.extend(repos)
        page += 1
        print(f"已获取第 {page-1} 页，共 {len(repos)} 个仓库")
    
    return all_repos

def categorize_repos(repos):
    """根据语言对仓库进行分类"""
    categories = defaultdict(list)
    
    for repo in repos:
        language = repo.get('language') or 'Other'
        categories[language].append(repo)
    
    return categories

def generate_markdown(categories):
    """生成 Markdown 文档"""
    md_content = "# wangrongjia 的 Starred 仓库\n\n"
    md_content += f"总计: {sum(len(repos) for repos in categories.values())} 个仓库\n\n"
    
    # 按分类排序（按该分类下仓库数量排序）
    sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
    
    for language, repos in sorted_categories:
        md_content += f"## {language} ({len(repos)} 个仓库)\n\n"
        
        # 按 star 数量倒序排列
        sorted_repos = sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)
        
        md_content += "| 仓库名称 | Star 数量 | 链接 |\n"
        md_content += "|----------|-----------|------|\n"
        
        for repo in sorted_repos:
            full_name = repo['full_name']
            stars = repo['stargazers_count']
            html_url = repo['html_url']
            
            md_content += f"| {full_name} | {stars:,} | [查看仓库]({html_url}) |\n"
        
        md_content += "\n"
    
    return md_content

def main():
    username = 'wangrongjia'
    print(f"正在获取用户 {username} 的 starred 仓库...")
    
    repos = get_all_starred_repos(username)
    print(f"总共获取到 {len(repos)} 个 starred 仓库")
    
    # 分类
    categories = categorize_repos(repos)
    print(f"分为 {len(categories)} 个分类")
    
    # 生成 Markdown
    markdown_content = generate_markdown(categories)
    
    # 保存到文件
    output_file = 'wangrongjia_starred_repos.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Markdown 文档已保存到: {output_file}")
    
    # 显示统计信息
    print("\n分类统计:")
    for language, repos in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {language}: {len(repos)} 个仓库")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
import requests
import json
import os
from collections import defaultdict
from datetime import datetime

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

def generate_enhanced_markdown(categories, username):
    """生成增强版 Markdown 文档"""
    total_repos = sum(len(repos) for repos in categories.values())
    total_stars = sum(repo['stargazers_count'] for repos in categories.values() for repo in repos)
    
    md_content = f"# {username} 的 GitHub Starred 仓库分析\n\n"
    md_content += f"📊 **统计概览**\n"
    md_content += f"- 总仓库数: **{total_repos:,}** 个\n"
    md_content += f"- 总 Star 数: **{total_stars:,}** 个\n"
    md_content += f"- 编程语言: **{len(categories)}** 种\n"
    md_content += f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 生成目录
    md_content += "## 📚 目录\n\n"
    sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
    
    for i, (language, repos) in enumerate(sorted_categories, 1):
        category_stars = sum(repo['stargazers_count'] for repo in repos)
        md_content += f"{i}. [{language}](#{language.lower().replace('+', 'plus').replace('#', 'sharp')}) ({len(repos)} 个仓库, {category_stars:,} stars)\n"
    
    md_content += "\n---\n\n"
    
    # 按分类排序（按该分类下仓库数量排序）
    for language, repos in sorted_categories:
        category_stars = sum(repo['stargazers_count'] for repo in repos)
        avg_stars = category_stars // len(repos) if repos else 0
        
        md_content += f"## {language}\n\n"
        md_content += f"📈 **分类统计**: {len(repos)} 个仓库 | 总计 {category_stars:,} stars | 平均 {avg_stars:,} stars\n\n"
        
        # 按 star 数量倒序排列
        sorted_repos = sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)
        
        md_content += "| 排名 | 仓库名称 | Star 数量 | 描述 | 链接 |\n"
        md_content += "|------|----------|-----------|------|------|\n"
        
        for i, repo in enumerate(sorted_repos, 1):
            full_name = repo['full_name']
            stars = repo['stargazers_count']
            html_url = repo['html_url']
            desc = repo.get('description') or '暂无描述'
            description = desc[:50] + ('...' if len(desc) > 50 else '')
            
            md_content += f"| {i} | **{full_name}** | {stars:,} ⭐ | {description} | [🔗 查看]({html_url}) |\n"
        
        md_content += "\n"
    
    # 添加 Top 10 最受欢迎的仓库
    md_content += "## 🏆 Top 10 最受欢迎的仓库\n\n"
    all_repos_flat = [repo for repos in categories.values() for repo in repos]
    top_repos = sorted(all_repos_flat, key=lambda x: x['stargazers_count'], reverse=True)[:10]
    
    md_content += "| 排名 | 仓库名称 | Star 数量 | 语言 | 链接 |\n"
    md_content += "|------|----------|-----------|------|------|\n"
    
    for i, repo in enumerate(top_repos, 1):
        full_name = repo['full_name']
        stars = repo['stargazers_count']
        language = repo.get('language', 'Other')
        html_url = repo['html_url']
        
        md_content += f"| {i} | **{full_name}** | {stars:,} ⭐ | {language} | [🔗 查看]({html_url}) |\n"
    
    md_content += "\n---\n\n"
    md_content += f"*本文档由脚本自动生成，数据来源于 GitHub API*\n"
    
    return md_content

def main():
    username = 'wangrongjia'
    print(f"正在获取用户 {username} 的 starred 仓库...")
    
    repos = get_all_starred_repos(username)
    print(f"总共获取到 {len(repos)} 个 starred 仓库")
    
    # 分类
    categories = categorize_repos(repos)
    print(f"分为 {len(categories)} 个分类")
    
    # 生成增强版 Markdown
    markdown_content = generate_enhanced_markdown(categories, username)
    
    # 保存到文件
    output_file = f'{username}_starred_repos_enhanced.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"增强版 Markdown 文档已保存到: {output_file}")
    
    # 显示统计信息
    total_stars = sum(repo['stargazers_count'] for repos in categories.values() for repo in repos)
    print(f"\n📊 总体统计:")
    print(f"  总仓库数: {len(repos):,}")
    print(f"  总 Star 数: {total_stars:,}")
    print(f"  编程语言数: {len(categories)}")
    
    print("\n🏷️ 分类统计:")
    for language, repos in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        category_stars = sum(repo['stargazers_count'] for repo in repos)
        print(f"  {language}: {len(repos)} 个仓库 ({category_stars:,} stars)")

if __name__ == '__main__':
    main()
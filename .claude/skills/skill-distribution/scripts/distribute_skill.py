#!/usr/bin/env python3
"""
Skill Distribution Script

Skillを複数のエージェントリポジトリに一括配布する。

使用例:
    # 単一Skill配布
    python distribute_skill.py chatgpt-parallel-research

    # 複数Skill配布
    python distribute_skill.py chatgpt-parallel-research x-automation

    # 全Skill配布
    python distribute_skill.py --all

    # ドライラン
    python distribute_skill.py chatgpt-parallel-research --dry-run

    # 新規のみ配布
    python distribute_skill.py chatgpt-parallel-research --mode new_only

    # 特定リポジトリのみ
    python distribute_skill.py chatgpt-parallel-research --repos fiction_craft_agent o2p-agent
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


DESKTOP_PATH = Path.home() / "Desktop"


def get_source_skills_path(source_repo: str) -> Path:
    return DESKTOP_PATH / source_repo / ".claude" / "skills"

EXCLUDE_SKILLS = set()


def get_available_skills(source_skills_path: Path) -> List[str]:
    """配布可能なSkill一覧を取得"""
    if not source_skills_path.exists():
        return []

    skills = []
    for item in source_skills_path.iterdir():
        if item.is_dir() and item.name not in EXCLUDE_SKILLS:
            # SKILL.mdが存在するフォルダのみ
            if (item / "SKILL.md").exists():
                skills.append(item.name)

    return sorted(skills)


def find_target_repos(
    skill_name: str,
    exclude_repos: set,
    include_repos: Optional[List[str]] = None,
) -> List[Path]:
    """
    配布先リポジトリを検索

    Args:
        skill_name: Skill名
        include_repos: 配布先を限定するリポジトリ名リスト（Noneで全リポジトリ）

    Returns:
        配布先のskillsディレクトリパスのリスト
    """
    targets = []

    for item in DESKTOP_PATH.iterdir():
        if not item.is_dir():
            continue

        repo_name = item.name

        # 除外リポジトリをスキップ
        if repo_name in exclude_repos:
            continue

        # 限定リポジトリが指定されている場合
        if include_repos and repo_name not in include_repos:
            continue

        # .claude/skills/ が存在するリポジトリのみ
        skills_dir = item / ".claude" / "skills"
        if skills_dir.exists():
            targets.append(skills_dir)

    return sorted(targets)


def distribute_skill(
    skill_name: str,
    source_skills_path: Path,
    exclude_repos: set,
    mode: str = "overwrite",
    dry_run: bool = False,
    include_repos: Optional[List[str]] = None
) -> Dict:
    """
    単一Skillを配布

    Args:
        skill_name: 配布するSkill名
        mode: "overwrite" | "new_only"
        dry_run: True=実行せず確認のみ
        include_repos: 配布先を限定するリポジトリ名リスト

    Returns:
        配布結果の辞書
    """
    source_path = source_skills_path / skill_name

    if not source_path.exists():
        return {
            "skill": skill_name,
            "success": False,
            "error": f"Source skill not found: {source_path}",
            "results": []
        }

    targets = find_target_repos(skill_name, exclude_repos, include_repos)
    results = []

    for target_skills_dir in targets:
        repo_name = target_skills_dir.parent.parent.name
        target_path = target_skills_dir / skill_name

        result = {
            "repo": repo_name,
            "target": str(target_path),
            "status": None,
            "note": ""
        }

        try:
            exists = target_path.exists()

            if exists and mode == "new_only":
                result["status"] = "Skipped"
                result["note"] = "Already exists (new_only mode)"
            elif exists:
                # 上書き
                if not dry_run:
                    shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
                result["status"] = "Updated"
                result["note"] = "Overwritten"
            else:
                # 新規作成
                if not dry_run:
                    shutil.copytree(source_path, target_path)
                result["status"] = "Created"
                result["note"] = "New"

            if dry_run:
                result["note"] += " (dry-run)"

        except Exception as e:
            result["status"] = "Error"
            result["note"] = str(e)

        results.append(result)

    return {
        "skill": skill_name,
        "success": True,
        "source": str(source_path),
        "results": results,
        "summary": {
            "total": len(results),
            "updated": sum(1 for r in results if r["status"] == "Updated"),
            "created": sum(1 for r in results if r["status"] == "Created"),
            "skipped": sum(1 for r in results if r["status"] == "Skipped"),
            "errors": sum(1 for r in results if r["status"] == "Error")
        }
    }


def print_result(result: Dict, verbose: bool = False):
    """配布結果を表示"""
    skill = result.get("skill", "unknown")

    if not result.get("success"):
        print(f"\n[ERROR] {skill}: {result.get('error')}")
        return

    summary = result.get("summary", {})
    results = result.get("results", [])

    print(f"\n## {skill}")
    print(f"Source: {result.get('source')}")
    print(f"Total: {summary.get('total', 0)} repos")
    print(f"  - Updated: {summary.get('updated', 0)}")
    print(f"  - Created: {summary.get('created', 0)}")
    print(f"  - Skipped: {summary.get('skipped', 0)}")
    print(f"  - Errors: {summary.get('errors', 0)}")

    if verbose or summary.get('errors', 0) > 0:
        print("\nDetails:")
        for r in results:
            status_icon = {
                "Updated": "U",
                "Created": "+",
                "Skipped": "-",
                "Error": "!"
            }.get(r["status"], "?")
            print(f"  [{status_icon}] {r['repo']}: {r['note']}")


def main():
    parser = argparse.ArgumentParser(
        description="Skillを複数のエージェントリポジトリに一括配布する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s chatgpt-parallel-research
  %(prog)s chatgpt-parallel-research x-automation
  %(prog)s --all
  %(prog)s chatgpt-parallel-research --dry-run
  %(prog)s chatgpt-parallel-research --mode new_only
  %(prog)s chatgpt-parallel-research --repos fiction_craft_agent o2p-agent
        """
    )

    parser.add_argument(
        "skills",
        nargs="*",
        help="配布するSkill名（複数指定可）"
    )
    parser.add_argument(
        "--source-repo",
        default="browser-controller-agent",
        help="配布元リポジトリ名（Desktop配下、default: browser-controller-agent）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="全Skillを配布"
    )
    parser.add_argument(
        "--mode",
        choices=["overwrite", "new_only"],
        default="overwrite",
        help="配布モード（default: overwrite）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実行せず確認のみ"
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        help="配布先リポジトリを限定"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="配布可能なSkill一覧を表示"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細表示"
    )

    args = parser.parse_args()

    source_repo = args.source_repo
    source_skills_path = get_source_skills_path(source_repo)
    exclude_repos = {source_repo}

    # Skill一覧表示
    if args.list:
        skills = get_available_skills(source_skills_path)
        print("Available skills:")
        for skill in skills:
            print(f"  - {skill}")
        return 0

    # 配布するSkillを決定
    if args.all:
        skills = get_available_skills(source_skills_path)
    elif args.skills:
        skills = args.skills
    else:
        parser.print_help()
        return 1

    if not skills:
        print("No skills to distribute")
        return 1

    # 配布実行
    print(f"=== Skill Distribution ===")
    print(f"DateTime: {datetime.now().isoformat()}")
    print(f"Source repo: {source_repo}")
    print(f"Source skills: {source_skills_path}")
    print(f"Mode: {args.mode}")
    print(f"Dry-run: {args.dry_run}")
    print(f"Skills: {', '.join(skills)}")
    if args.repos:
        print(f"Target repos: {', '.join(args.repos)}")

    all_results = []
    for skill in skills:
        result = distribute_skill(
            skill_name=skill,
            source_skills_path=source_skills_path,
            exclude_repos=exclude_repos,
            mode=args.mode,
            dry_run=args.dry_run,
            include_repos=args.repos
        )
        all_results.append(result)
        print_result(result, verbose=args.verbose)

    # 総合サマリー
    total_updated = sum(r.get("summary", {}).get("updated", 0) for r in all_results)
    total_created = sum(r.get("summary", {}).get("created", 0) for r in all_results)
    total_skipped = sum(r.get("summary", {}).get("skipped", 0) for r in all_results)
    total_errors = sum(r.get("summary", {}).get("errors", 0) for r in all_results)

    print(f"\n=== Summary ===")
    print(f"Skills: {len(skills)}")
    print(f"Updated: {total_updated}")
    print(f"Created: {total_created}")
    print(f"Skipped: {total_skipped}")
    print(f"Errors: {total_errors}")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

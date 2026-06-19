"""
A股AI投研系统 — 一键安装脚本
将 skills/commands/MCP配置 安装到用户的 Claude Code 环境中

用法: python install.py
"""

import sys
import os
import shutil
import platform
from pathlib import Path

# ── 版本 ──────────────────────────────────────────
VERSION = "0.0.0"

# ── 路径检测 ──────────────────────────────────────
REPO_DIR = Path(__file__).parent.resolve()
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"

SKILLS_SRC = REPO_DIR / "skills" / "analysts"
SKILLS_DST = CLAUDE_DIR / "skills" / "analysts"

COMMANDS_SRC = REPO_DIR / "commands"
COMMANDS_DST = CLAUDE_DIR / "commands"

MCP_TEMPLATE = REPO_DIR / ".mcp.json.template"
MCP_DST = HOME / ".mcp.json"

IS_WINDOWS = platform.system() == "Windows"


def confirm(msg: str) -> bool:
    """询问用户确认"""
    resp = input(f"{msg} [Y/n]: ").strip().lower()
    return resp in ("", "y", "yes")


def check_python():
    """检查 Python 版本"""
    ver = sys.version_info
    if ver < (3, 10):
        print(f"\n❌ Python {ver.major}.{ver.minor} 不满足最低要求 (3.10+)")
        sys.exit(1)
    print(f"  Python: {sys.executable} ({ver.major}.{ver.minor}.{ver.micro})")


def install_skills():
    """复制 skills 到 ~/.claude/skills/analysts/"""
    print("\n📦 安装 AI 角色 Skills...")
    SKILLS_DST.mkdir(parents=True, exist_ok=True)

    skill_dirs = [d for d in sorted(SKILLS_SRC.iterdir())
                  if d.is_dir() and (d / "SKILL.md").exists()]
    count = 0

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        dst_dir = SKILLS_DST / skill_dir.name
        dst_dir.mkdir(exist_ok=True)
        dst_file = dst_dir / "SKILL.md"

        shutil.copy2(skill_md, dst_file)
        print(f"  ✅ {skill_dir.name}/SKILL.md")
        count += 1

    print(f"  共安装 {count} 个 Skill")


def install_commands():
    """复制 commands 到 ~/.claude/commands/"""
    print("\n📋 安装斜杠命令...")
    COMMANDS_DST.mkdir(parents=True, exist_ok=True)

    count = 0
    for cmd_file in sorted(COMMANDS_SRC.glob("*.md")):
        dst_file = COMMANDS_DST / cmd_file.name
        shutil.copy2(cmd_file, dst_file)
        print(f"  ✅ {cmd_file.name}")
        count += 1

    if count == 0:
        print("  ⚠️  未找到命令文件")
    else:
        print(f"  共安装 {count} 个命令")


def check_dependencies():
    """检查核心 Python 依赖是否已安装"""
    print("\n🔍 检查 Python 依赖...")
    deps = {"akshare": "akshare>=1.18", "mcp": "mcp>=1.27", "fastmcp": "fastmcp>=3.4",
            "pandas": "pandas>=2.0", "numpy": "numpy>=1.24", "ta": "ta>=0.10,<0.12"}
    missing = []
    for mod, spec in deps.items():
        try:
            __import__(mod)
            if mod == "ta":
                from ta.trend import MACD
                from ta.momentum import RSIIndicator
            print(f"  ✅ {mod}")
        except ImportError:
            print(f"  ❌ {mod} — {spec}")
            missing.append(mod)
    if missing:
        print(f"\n❌ 缺少依赖：{', '.join(missing)}")
        print(f"   请先运行：pip install -r {REPO_DIR / 'requirements.txt'}")
        return False
    return True


def install_mcp_config():
    """生成项目级 .mcp.json（优先）和 ~/.mcp.json（兜底），替换占位符"""
    if not check_dependencies():
        sys.exit(1)

    print("\n⚙️  生成 MCP 配置...")

    python_path = sys.executable
    repo_path = REPO_DIR.as_posix()

    print(f"  Python: {python_path}")
    print(f"  Repo:   {repo_path}")

    template_content = MCP_TEMPLATE.read_text(encoding='utf-8')
    config = template_content.replace("{{PYTHON_PATH}}", python_path)
    config = config.replace("{{REPO_PATH}}", repo_path)

    # 🔴 关键修复：写入两个位置
    # 1. 项目根目录（Claude Code 优先读取）
    # 2. ~/.mcp.json（全局兜底）
    targets = {
        "项目根目录（Claude Code 优先）": REPO_DIR / ".mcp.json",
        "用户主目录（全局兜底）": MCP_DST,
    }

    for label, target in targets.items():
        if target.exists() and target == MCP_DST:
            backup_path = target.with_suffix(".json.install-backup")
            print(f"  ⚠️  {target} 已存在")
            if confirm("  是否覆盖？(旧配置将备份)"):
                shutil.copy2(target, backup_path)
                print(f"  📁 旧配置已备份到 {backup_path}")
            else:
                print(f"  ⏭️  跳过 {label}")
                continue
        target.write_text(config, encoding='utf-8')
        print(f"  ✅ 已生成 {target} ({label})")


def print_next_steps():
    """打印后续步骤（根据操作系统适配命令）"""
    workspace_dir = HOME / "ai-investment"
    ws = str(workspace_dir)

    print("\n" + "=" * 60)
    print(f"🎉 A股AI投研系统 v{VERSION} 安装完成！")
    print("=" * 60)
    print()
    print("接下来请手动完成以下步骤：")
    print()
    print("1️⃣  安装 Python 依赖：")
    print(f"    pip install -r \"{REPO_DIR / 'requirements.txt'}\"")
    print()
    print("2️⃣  配置 API Key：")
    settings_dst = CLAUDE_DIR / "settings.json"
    settings_tmpl = REPO_DIR / "workspace-template" / ".claude" / "settings.json.template"
    if IS_WINDOWS:
        print(f"    复制 {settings_tmpl} 到 {settings_dst}")
        print(f"    编辑 {settings_dst}，填入你的 API Key")
    else:
        print(f"    cp {settings_tmpl} {settings_dst}")
        print(f"    编辑 {settings_dst}，填入你的 API Key")
    print()
    print("3️⃣  创建工作区目录：")
    if IS_WINDOWS:
        print(f'    Copy-Item -Recurse "{REPO_DIR / "workspace-template"}\\*" "{ws}\\"')
    else:
        print(f"    mkdir -p {ws}")
        print(f"    cp -r {REPO_DIR / 'workspace-template'}/* {ws}/")
    print()
    print("4️⃣  运行自检程序（验证环境是否完整）：")
    print(f"    python {REPO_DIR / 'tools' / 'self-test.py'}")
    print("    预期输出：5/5 全部通过。如有未通过项，根据提示修复。")
    print()
    print("5️⃣  在 Claude Code 中测试：")
    print("    /analyze-initial 002414 高德红外")
    print()
    print("📖 详细文档：")
    print(f"    {REPO_DIR / 'docs' / '使用手册.md'}")
    print()
    print("⚠️  免责声明：本系统仅供学习研究，不构成投资建议。")


def main():
    print("=" * 60)
    print(f"  A股AI投研系统 v{VERSION} — 安装脚本")
    print("=" * 60)
    print(f"  Repo: {REPO_DIR}")
    print(f"  Home: {HOME}")
    print(f"  OS:   {platform.system()} {platform.release()}")

    check_python()

    # 检查模板文件
    if not MCP_TEMPLATE.exists():
        print(f"\n❌ 错误：找不到 {MCP_TEMPLATE}")
        sys.exit(1)

    try:
        install_skills()
        install_commands()
        install_mcp_config()
        print_next_steps()
    except Exception as e:
        print(f"\n❌ 安装出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

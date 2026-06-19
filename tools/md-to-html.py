"""
A股AI投研报告 HTML 生成器
用法: python tools/md-to-html.py [标的目录名]
     在项目根目录下运行，或任意位置运行均可（自动定位项目根目录）
示例: python tools/md-to-html.py 002202-金风科技
"""

import sys, os, re
from pathlib import Path
import markdown

# ── 配置 ─────────────────────────────────────────
# 自动定位项目根目录（脚本在 tools/ 下，项目根目录在上一级）
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BASE = PROJECT_ROOT / "reports" / "stocks"

# ── HTML 模板 ────────────────────────────────────
TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
:root{{--bg:#0f1117;--card:#1a1d28;--bor:#2a2d3a;--tx:#c9d1d9;--mu:#8b949e;--hl:#f0f6fc;
  --gn:#3fb950;--rd:#f85149;--yl:#d2991d;--bl:#58a6ff;--pu:#bc8cff;--or:#f0883e}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif;
  background:var(--bg);color:var(--tx);line-height:1.75;padding:0 20px 60px}}
.wrap{{max-width:1000px;margin:0 auto}}
.hero{{text-align:center;padding:60px 0 40px;border-bottom:1px solid var(--bor)}}
.hero h1{{font-size:2.2rem;font-weight:800;color:var(--hl);margin-bottom:6px}}
.hero .sub{{font-size:1rem;color:var(--mu)}}
.badge-row{{display:flex;gap:10px;justify-content:center;margin-top:18px;flex-wrap:wrap}}
.badge{{padding:6px 18px;border-radius:20px;font-size:0.82rem;font-weight:600;border:1px solid var(--bor);background:var(--card)}}
.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:30px 0}}
.sum-card{{background:var(--card);border:1px solid var(--bor);border-radius:10px;padding:16px;text-align:center}}
.sum-card .val{{font-size:1.55rem;font-weight:800;color:var(--hl)}}
.sum-card .lbl{{font-size:0.76rem;color:var(--mu);margin-top:4px}}
section{{padding:40px 0}}section+section{{border-top:1px solid var(--bor)}}
h2{{font-size:1.35rem;font-weight:700;color:var(--hl);margin:28px 0 16px;padding-bottom:8px;border-bottom:2px solid var(--bor)}}
h3{{font-size:1.05rem;font-weight:600;color:var(--hl);margin:24px 0 12px}}
h4{{font-size:0.95rem;font-weight:600;color:var(--hl);margin:16px 0 8px}}
h5{{font-size:0.88rem;font-weight:600;color:var(--mu);margin:12px 0 6px}}
p{{margin:8px 0;color:var(--mu)}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:0.88rem;overflow-x:auto;display:block}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid var(--bor);white-space:nowrap}}
th{{background:var(--card);color:var(--hl);font-weight:600;font-size:0.8rem;letter-spacing:0.5px}}
tr:hover td{{background:rgba(255,255,255,0.02)}}
blockquote{{background:rgba(88,166,255,0.04);border-left:3px solid var(--bl);padding:10px 16px;margin:14px 0;border-radius:0 8px 8px 0;color:var(--mu)}}
pre{{background:#0d1117;border:1px solid var(--bor);border-radius:8px;padding:18px;overflow-x:auto;font-size:0.82rem;line-height:1.7;color:var(--mu)}}
pre code{{background:none;padding:0;font-size:inherit}}
code{{background:rgba(255,255,255,0.06);padding:2px 6px;border-radius:4px;font-size:0.85rem}}
ul,ol{{padding-left:22px;color:var(--mu)}}li{{padding:2px 0}}
strong{{color:var(--hl)}}
em{{color:var(--mu)}}
hr{{border:none;border-top:1px solid var(--bor);margin:30px 0}}
footer{{text-align:center;padding:44px 0 20px;color:var(--mu);font-size:0.82rem;border-top:1px solid var(--bor)}}
a{{color:var(--bl);text-decoration:none}}
.card{{background:var(--card);border:1px solid var(--bor);border-radius:12px;padding:22px;margin:14px 0}}
.analyst-tag{{display:inline-block;padding:2px 10px;border-radius:4px;font-size:0.75rem;font-weight:600;margin-right:8px}}
.analyst-tag.fund{{background:rgba(88,166,255,0.15);color:var(--bl)}}
.analyst-tag.chip{{background:rgba(240,136,62,0.15);color:var(--or)}}
.analyst-tag.tech{{background:rgba(63,185,80,0.15);color:var(--gn)}}
.analyst-tag.sent{{background:rgba(188,140,255,0.15);color:var(--pu)}}
.signal-box{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}}
.sig{{background:var(--card);border:1px solid var(--bor);border-radius:10px;padding:18px;text-align:center}}
.sig .v{{font-size:1.5rem;font-weight:800}}.sig .l{{font-size:0.8rem;color:var(--mu);margin-top:4px}}
.sig.gn{{border-color:var(--gn)}}.sig.gn .v{{color:var(--gn)}}
.sig.rd{{border-color:var(--rd)}}.sig.rd .v{{color:var(--rd)}}
.sig.yl{{border-color:var(--yl)}}.sig.yl .v{{color:var(--yl)}}
.sig.pu{{border-color:var(--pu)}}.sig.pu .v{{color:var(--pu)}}
nav{{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0;padding:14px 18px;background:var(--card);border:1px solid var(--bor);border-radius:10px;font-size:0.84rem}}
.score-badge{{display:inline-block;padding:4px 12px;border-radius:14px;font-weight:700;font-size:0.85rem}}
.score-badge.high{{background:rgba(63,185,80,0.15);color:var(--gn)}}
.score-badge.mid{{background:rgba(210,153,29,0.15);color:var(--yl)}}
.score-badge.low{{background:rgba(248,81,73,0.15);color:var(--rd)}}
.highlight-box{{padding:14px 18px;border-radius:10px;margin:14px 0;font-size:0.88rem}}
.highlight-box.bull{{background:rgba(63,185,80,0.06);border:1px solid rgba(63,185,80,0.2)}}
.highlight-box.bear{{background:rgba(248,81,73,0.06);border:1px solid rgba(248,81,73,0.2)}}
.highlight-box.warn{{background:rgba(210,153,29,0.06);border:1px solid rgba(210,153,29,0.2)}}
.flow-steps{{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}}
.flow-step{{background:var(--card);border:1px solid var(--bor);border-radius:8px;padding:10px 14px;text-align:center;flex:1;min-width:100px;position:relative}}
.flow-step::after{{content:"→";position:absolute;right:-12px;top:50%;transform:translateY(-50%);color:var(--bl);font-size:1rem;font-weight:700}}
.flow-step:last-child::after{{display:none}}
.flow-step .sn{{font-size:0.65rem;color:var(--bl);font-weight:700}}
.flow-step .sl{{font-size:0.78rem;color:var(--hl);margin-top:2px;font-weight:600}}
.arch-layer{{border-left:3px solid;padding:12px 16px;margin:6px 0;border-radius:0 10px 10px 0;background:var(--card)}}
.arch-layer.top{{border-color:var(--rd)}}.arch-layer.mid{{border-color:var(--bl)}}.arch-layer.base{{border-color:var(--gn)}}
.chain-tree{{background:var(--card);border:1px solid var(--bor);border-radius:10px;padding:20px 24px;margin:16px 0;font-family:"SF Mono","Cascadia Code",monospace;font-size:0.82rem;line-height:1.9;color:var(--tx);overflow-x:auto}}
.chain-tree .l1{{color:var(--or);font-weight:700;font-size:0.9rem}}
.chain-tree .l2{{color:var(--bl);margin-left:12px}}
.chain-tree .l3{{color:var(--mu);margin-left:24px;font-size:0.78rem}}
.visual-tree{{background:var(--card);border:1px solid var(--bor);border-radius:12px;padding:20px;margin:16px 0;font-size:0.85rem}}
.visual-tree .vt-section{{color:var(--or);font-weight:700;font-size:0.95rem;padding:10px 0 6px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:8px}}
.visual-tree .vt-section:first-child{{padding-top:0}}
.visual-tree .vt-group{{margin-left:8px;padding:6px 0}}
.visual-tree .vt-branch{{color:var(--bl);font-weight:600;padding:5px 0;font-size:0.85rem}}
.visual-tree .vt-arrow{{display:inline-block;color:var(--bl);font-size:0.7rem;margin-right:4px;transition:transform 0.2s}}
.visual-tree .vt-leaf{{color:var(--mu);padding:2px 0 2px 24px;font-size:0.78rem;line-height:1.6}}
.visual-tree .vt-leaf::before{{content:"· ";color:var(--pu);font-weight:700}}
.visual-flow{{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0;justify-content:center}}
.visual-flow .vf-step{{background:var(--card);border:1px solid var(--bor);border-radius:10px;padding:12px 18px;text-align:center;flex:1;min-width:120px;position:relative}}
.visual-flow .vf-step::after{{content:"→";position:absolute;right:-12px;top:50%;transform:translateY(-50%);color:var(--bl);font-size:1.1rem;font-weight:700}}
.visual-flow .vf-step:last-child::after{{display:none}}
.visual-flow .vf-num{{display:block;font-size:0.65rem;color:var(--bl);font-weight:700;margin-bottom:2px}}
.visual-flow .vf-label{{display:block;font-size:0.82rem;color:var(--hl);font-weight:600}}
@media(max-width:640px){{.visual-flow{{flex-direction:column}}.visual-flow .vf-step::after{{content:"↓";right:50%;top:auto;bottom:-10px;transform:translateX(50%)}}.visual-flow .vf-step:last-child::after{{display:none}}}}
@media(max-width:640px){{.flow-steps{{flex-direction:column}}.flow-step::after{{content:"↓";right:50%;top:auto;bottom:-12px;transform:translateX(50%)}}.flow-step:last-child::after{{display:none}}}}
</style>
</head>
<body><div class="wrap">
{hero}
{nav}
{body}
<footer><p>{title} · 四维 Subagent 并行编排 · AI 美化师拼接输出</p><p style="margin-top:4px;color:var(--rd)">仅供学习研究参考，不构成投资建议</p></footer>
</div></body></html>'''


# ── 预处理：ASCII 图表 → 可视化 HTML ──────────
def _preprocess_diagrams(md_text: str) -> str:
    """扫描 markdown 中的围栏代码块（```），将包含树形/流程图的块转换为可视化 HTML"""
    tree_chars = set('├└│')
    flow_chars = set('┌┐┘')

    def _replace_fenced_block(m):
        content = m.group(1)
        # 判断块类型
        has_tree = any(c in content for c in tree_chars)
        has_flow = any(c in content for c in flow_chars)
        if not (has_tree or has_flow):
            return m.group(0)  # 不是图表块，保留原样
        # 按行拆分，保留所有行（包括章节标题和空行）
        block_lines = content.split('\n')
        if not block_lines:
            return m.group(0)
        # 只保留有意义的行：树形/流程字符、章节标题、非空行
        filtered = []
        for line in block_lines:
            stripped = line.strip()
            if not stripped:
                filtered.append(line)
                continue
            if any(c in stripped for c in tree_chars | flow_chars):
                filtered.append(line)
            elif any(kw in stripped for kw in ['上游', '中游', '下游', '全景', '流程', '架构', '图示']):
                filtered.append(line)
            elif filtered:  # 已经在块内，保留可能的相关行
                filtered.append(line)
        if not filtered:
            return m.group(0)
        # 选择渲染器
        if has_tree and not has_flow:
            rendered = _render_tree_block(block_lines)
        else:
            rendered = _render_flow_block(block_lines)
        return rendered if rendered else m.group(0)

    return re.sub(
        r'```\n(.*?)```',
        _replace_fenced_block,
        md_text,
        flags=re.DOTALL
    )

def _render_tree_block(block):
    """将树形图块渲染为可视化 HTML。用空行包裹避免被 markdown 解析器转义。"""
    if not block:
        return ''
    nodes = []
    for line in block:
        stripped = line.strip()
        if not stripped:
            nodes.append({'type': 'spacer'})
            continue
        # 解析行内容
        is_section = (stripped.startswith('上游') or stripped.startswith('中游') or
                      stripped.startswith('下游'))
        is_branch = stripped.startswith('├──') or stripped.startswith('└──')
        is_leaf = stripped.startswith('│')
        if is_section:
            nodes.append({'type': 'section', 'text': stripped})
        elif is_branch:
            name = stripped[4:].strip() if len(stripped) > 4 else stripped
            nodes.append({'type': 'branch', 'text': name})
        elif is_leaf:
            detail = re.sub(r'^│\s*', '', stripped).strip()
            detail = re.sub(r'^└──\s*', '', detail)
            nodes.append({'type': 'leaf', 'text': detail})
        elif stripped == '│':
            pass
        else:
            nodes.append({'type': 'text', 'text': stripped})
    if not nodes:
        return ''
    # 构建 HTML（无缩进，前后空行确保 markdown 识别为原始 HTML）
    lines = ['', '<div class="visual-tree">']
    in_subgroup = False
    for node in nodes:
        t = node['type']
        if t == 'section':
            if in_subgroup:
                lines.append('</div>')
                in_subgroup = False
            lines.append(f'<div class="vt-section">{node["text"]}</div>')
        elif t == 'branch':
            if not in_subgroup:
                lines.append('<div class="vt-group">')
                in_subgroup = True
            lines.append(f'<div class="vt-branch"><span class="vt-arrow">▶</span> {node["text"]}</div>')
        elif t == 'leaf':
            lines.append(f'<div class="vt-leaf">{node["text"]}</div>')
    if in_subgroup:
        lines.append('</div>')
    lines.append('</div>')
    lines.append('')
    return '\n'.join(lines)

def _render_flow_block(block):
    """将流程图块渲染为可视化 HTML"""
    nodes = []
    for line in block:
        stripped = line.strip()
        if not stripped:
            continue
        clean = re.sub(r'[┌┐└┘├┤│─]', '', stripped).strip()
        if clean:
            nodes.append(clean)
    if not nodes:
        return ''
    steps = []
    for n in nodes:
        n = re.sub(r'^\d+\.?\s*', '', n)
        steps.append(n)
    lines = ['', '<div class="visual-flow">']
    for i, s in enumerate(steps):
        lines.append(f'<div class="vf-step"><span class="vf-num">{i+1}</span><span class="vf-label">{s}</span></div>')
    lines.append('</div>')
    lines.append('')
    return '\n'.join(lines)


# ── Markdown → HTML ─────────────────────────────
def md_to_html(text: str) -> str:
    """Convert markdown to HTML with extensions"""
    # 先预处理可视化图表
    text = _preprocess_diagrams(text)
    return markdown.markdown(text, extensions=['tables', 'fenced_code', 'codehilite', 'nl2br'])


# ── 后处理：自动增强可视化 ─────────────────────
def _enhance_visuals(html: str) -> str:
    """检测报告中的关键结构元素并用CSS类包装，提升可读性"""
    # 1. 为综合分析评分表添加颜色标记: 检测 ≥80 / 60-79 / <60 模式的分数
    html = re.sub(
        r'(<td[^>]*>)\s*(\d{2,3})\s*(分\s*)?(</td>)',
        lambda m: f'{m.group(1)}<span class="score-badge ' +
                  ('high' if int(m.group(2)) >= 80 else 'mid' if int(m.group(2)) >= 60 else 'low') +
                  f'">{m.group(2)}{m.group(3) or ""}</span>{m.group(4)}',
        html
    )
    # 2. 为信号汇总表（多列对比）添加视觉样式
    html = re.sub(
        r'(<table>\s*<thead>\s*<tr>\s*(<th>[^<]*</th>\s*){4,}</tr>)',
        r'<table class="matrix-table">\1',
        html,
        count=1
    )
    # 3. 为引用块中的关键结论添加视觉样式
    html = re.sub(
        r'<blockquote>\s*<p>(<strong>)?(🔴|⚠️|✅|❌)(.*?)</p>\s*</blockquote>',
        r'<div class="highlight-box warn">\1\2\3</div>',
        html
    )
    # 4. 残留 ASCII 图清理: 对未匹配的树形字符代码块做兜底着色
    def _wrap_codehilite(m):
        inner = m.group(1)
        if not any(c in inner for c in '├└│'):
            return m.group(0)
        inner = re.sub(r'^(上游[^\n]*)', r'<span class="l1">\1</span>', inner, flags=re.MULTILINE)
        inner = re.sub(r'^(中游[^\n]*)', r'<span class="l1">\1</span>', inner, flags=re.MULTILINE)
        inner = re.sub(r'^(下游[^\n]*)', r'<span class="l1">\1</span>', inner, flags=re.MULTILINE)
        inner = re.sub(r'^(├──[^\n]*)', r'<span class="l2">\1</span>', inner, flags=re.MULTILINE)
        inner = re.sub(r'^(└──[^\n]*)', r'<span class="l2">\1</span>', inner, flags=re.MULTILINE)
        inner = re.sub(r'^(│[^\n]*)', r'<span class="l3">\1</span>', inner, flags=re.MULTILINE)
        return f'<div class="chain-tree"><pre>\n{inner.strip()}\n</pre></div>'
    html = re.sub(r'<div class="codehilite"><pre><span></span><code>(.*?)</code></pre></div>', _wrap_codehilite, html, flags=re.DOTALL)
    return html

# ── 主逻辑 ───────────────────────────────────────
def build_report(stock_dir: str):
    report_dir = BASE / stock_dir / "01-初次覆盖"
    if not report_dir.exists():
        print(f"ERROR: 目录不存在: {report_dir}")
        sys.exit(1)

    # 查找文件
    chief_files = sorted(report_dir.glob("初次覆盖报告-[0-9]*.md"))
    # 查找子报告文件（取每个分析师的最新版本）
    all_sub_files = sorted(report_dir.glob("子报告-*.md"))
    # 按分析师类型分组，每组取最新版本（版本号最大的文件）
    sub_by_type = {}
    for sf in all_sub_files:
        # 文件名格式：子报告-基本面分析师-v1.md 或 子报告-基本面分析师-v1.1.md
        name = sf.stem.replace('子报告-', '')
        # 提取类型和版本：'基本面分析师-v1' → type='基本面分析师', ver='v1'
        parts = name.rsplit('-v', 1)
        atype = parts[0] if len(parts) > 1 else name
        ver = parts[1] if len(parts) > 1 else 'v1'
        if atype not in sub_by_type or ver > sub_by_type[atype][1]:
            sub_by_type[atype] = (sf, ver)
    sub_files = [v[0] for v in sub_by_type.values()]
    sub_files.sort()

    if not chief_files:
        print(f"ERROR: 未找到总分析师报告（初次覆盖报告-*.md）")
        sys.exit(1)

    chief_path = chief_files[-1]  # 取最新版本
    print(f"[CHIEF] {chief_path.name}")
    for sf in sub_files:
        print(f"[SUB]   {sf.name}")

    # 读取所有文件
    chief_md = chief_path.read_text(encoding='utf-8')
    sub_mds = {}
    for sf in sub_files:
        name = sf.stem.replace('子报告-', '').replace('-完整版', '')
        sub_mds[name] = sf.read_text(encoding='utf-8')

    # 提取股票名
    stock_name = stock_dir.split('-', 1)[-1]
    stock_code = stock_dir.split('-')[0]

    # ── 构建 HTML ──
    title = f"{stock_name}({stock_code}) 初次覆盖报告"

    # Hero
    hero = f'''<div class="hero">
<h1>{stock_name}</h1>
<div class="sub">{stock_code} · 初次覆盖报告 · 四维 Subagent 并行</div>
</div>'''

    # Nav
    nav_sections = []
    chief_html = md_to_html(chief_md)

    # Split chief report into sections for nav
    sections_in_chief = re.findall(r'<h2>(.*?)</h2>', chief_html)
    for s in sections_in_chief:
        clean = re.sub(r'<[^>]+>', '', s).strip()
        if clean:
            slug = re.sub(r'[^\w]', '', clean)[:20]
            nav_sections.append(f'<a href="#{slug}">{clean[:15]}</a>')

    nav = '<nav><strong>目录</strong> ' + ' '.join(nav_sections) + '</nav>'

    # Body: chief report + sub-reports
    # Add IDs to chief H2s for nav
    for h2_text in re.findall(r'<h2>(.*?)</h2>', chief_html):
        clean = re.sub(r'<[^>]+>', '', h2_text).strip()
        slug = re.sub(r'[^\w]', '', clean)[:20]
        chief_html = chief_html.replace(f'<h2>{h2_text}</h2>', f'<h2 id="{slug}">{h2_text}</h2>', 1)

    body_parts = [chief_html]

    # Append sub-reports with analyst tags
    sub_tags = {
        '基本面分析师': '<h2>附：基本面分析完整报告 <span class="analyst-tag fund">@analyst-fundamental</span></h2>',
        '筹码面分析师': '<h2>附：筹码面分析完整报告 <span class="analyst-tag chip">@analyst-chip-flow</span></h2>',
        '技术面分析师': '<h2>附：技术面分析完整报告 <span class="analyst-tag tech">@analyst-technical</span></h2>',
        '情绪面分析师': '<h2>附：情绪面分析完整报告 <span class="analyst-tag sent">@analyst-sentiment</span></h2>',
    }

    for name, md_text in sub_mds.items():
        tag = sub_tags.get(name, f'<h2>附：{name}完整报告</h2>')
        body_parts.append(f'<section>{tag}{md_to_html(md_text)}</section>')

    body = '\n'.join(body_parts)

    # ── 后处理：自动增强可视化 ──
    body = _enhance_visuals(body)

    html = TEMPLATE.format(title=title, hero=hero, nav=nav, body=body)

    # 写入
    out_path = report_dir / f"初次覆盖报告-{stock_code}-完整版.html"
    out_path.write_text(html, encoding='utf-8')
    print(f"\n[DONE] {out_path}")
    print(f"   文件大小: {out_path.stat().st_size / 1024:.0f} KB")


# ── 入口 ─────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python tools/md-to-html.py [标的目录名]")
        print("示例: python tools/md-to-html.py 002202-金风科技")
        print("注意: 请在项目工作区根目录下运行此脚本")
        sys.exit(1)

    build_report(sys.argv[1])

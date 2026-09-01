"""Terminal and HTML report renderers."""

from __future__ import annotations

from html import escape
from typing import Any


def render_terminal(profile: dict[str, Any]) -> str:
    title = f"DataLens · {profile['file']}"
    lines = [title, "=" * len(title), f"{profile['rows']} rows · {profile['columns_count']} columns · {profile['duplicate_rows']} duplicate rows", ""]
    for column in profile["columns"]:
        quality = 100 - column["missing_percent"]
        lines.append(f"{column['name']}  [{column['type']}]")
        lines.append(f"  completeness {quality:.1f}% · unique {column['unique']} · missing {column['missing']}")
        if "numeric" in column:
            numeric = column["numeric"]
            lines.append(f"  min {numeric['min']:g} · max {numeric['max']:g} · mean {numeric['mean']:g} · median {numeric['median']:g}")
        elif column["top_values"]:
            popular = ", ".join(f"{item['value']} ({item['count']})" for item in column["top_values"][:3])
            lines.append(f"  top {popular}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_html(profile: dict[str, Any]) -> str:
    cards = []
    for column in profile["columns"]:
        top_values = "".join(f"<li><span>{escape(str(item['value']))}</span><b>{item['count']}</b></li>" for item in column["top_values"][:5]) or "<li>No values</li>"
        numeric = ""
        if "numeric" in column:
            numeric = "<div class='stats'>" + "".join(f"<div><small>{escape(key.replace('_', ' '))}</small><strong>{value:g}</strong></div>" for key, value in column["numeric"].items()) + "</div>"
        cards.append(f"""
        <article>
          <div class="card-head"><div><p>{escape(column['type'].upper())}</p><h2>{escape(column['name'])}</h2></div><span>{100-column['missing_percent']:.1f}% complete</span></div>
          <div class="bar"><i style="width:{100-column['missing_percent']}%"></i></div>
          <p class="meta">{column['unique']} unique · {column['missing']} missing</p>
          {numeric or f'<h3>Most common</h3><ul>{top_values}</ul>'}
        </article>""")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>DataLens · {escape(profile['file'])}</title>
<style>
:root{{--ink:#17201d;--muted:#69756f;--paper:#f1f5f2;--green:#177155;--lime:#b9e672}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}header{{padding:52px max(24px,6vw);background:#173b31;color:white}}header p{{color:var(--lime);font-weight:800;letter-spacing:.12em}}h1{{margin:8px 0;font-size:clamp(36px,6vw,72px);letter-spacing:-.05em}}header span{{color:#c6d3ce}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;padding:32px max(24px,6vw)}}article{{padding:22px;border:1px solid #d9e2dc;border-radius:16px;background:white;box-shadow:0 9px 30px #17402b10}}.card-head{{display:flex;justify-content:space-between;gap:16px}}.card-head p,h2{{margin:0}}.card-head p{{font-size:11px;color:var(--green);font-weight:900;letter-spacing:.12em}}.card-head span{{font-size:12px;color:var(--muted)}}h2{{font-size:22px}}h3{{font-size:12px;text-transform:uppercase;letter-spacing:.1em}}.bar{{height:7px;margin:20px 0 8px;border-radius:10px;background:#e7ede8;overflow:hidden}}.bar i{{display:block;height:100%;background:var(--lime)}}.meta{{color:var(--muted);font-size:13px}}ul{{padding:0;list-style:none}}li{{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #edf0ed}}.stats{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:18px}}.stats div{{padding:10px;border-radius:9px;background:var(--paper)}}small,strong{{display:block}}small{{color:var(--muted);text-transform:capitalize}}strong{{font-size:18px}}
</style></head><body><header><p>MERHATTA SOFTWARES · DATA QUALITY REPORT</p><h1>{escape(profile['file'])}</h1><span>{profile['rows']} rows · {profile['columns_count']} columns · {profile['duplicate_rows']} duplicate rows</span></header><main>{''.join(cards)}</main></body></html>"""

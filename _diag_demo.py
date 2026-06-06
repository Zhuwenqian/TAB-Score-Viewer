# -*- coding: utf-8 -*-
"""诊断 Demo v5.gp5 的布局问题"""
import sys, os
sys.path.insert(os.path.dirname(os.path.abspath(__file__)))
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gtp_engine.parser import parse_gtp
from gtp_engine.renderer.layout_engine import TabLayoutEngine

gp = r'e:\Projects\TAB Score Viewer\gtp格式-吉他谱全集\gtp格式电吉他谱\Demo v5.gp5'
song = parse_gtp(gp)

print(f'=== 文件信息 ===')
print(f'标题: {song.title}')
print(f'音轨数: {len(song.tracks)}')

# 只看第一个音轨 (Rhythm Guitar)
t = song.tracks[0]
print(f'\n目标音轨: {t.name} ({len(t.measures)}小节)')

engine = TabLayoutEngine()
pages = engine.layout(t, 900, 1200)
print(f'总页数: {len(pages)}')
total_systems = 0
total_measures_rendered = 0

for pi, p in enumerate(pages):
    print(f'\n--- 第{pi+1}页: {len(p.systems)}系统, height={p.height}px ---')
    total_systems += len(p.systems)
    for si, s in enumerate(p.systems):
        ms = len(s.measures)
        total_measures_rendered += ms
        print(f'  系统{si+1}: y=[{s.y_top}-{s.y_bottom}], {ms}小节')
        for mi, m in enumerate(s.measures):
            mw = m.x_end - m.x_start
            nb = len(m.measure.beats)
            mk = m.measure.marker or ''
            if mi < 8 or pi == 0:  # 只打印前几个避免刷屏
                print(f'    小节{m.measure.number}: 宽={mw}px, {nb}拍, marker="{mk}"')

print(f'\n=== 统计 ===')
print(f'原始小节数: {len(t.measures)}')
print(f'渲染系统数: {total_systems}')
print(f'渲染小节总数: {total_measures_rendered}')
print(f'缺失小节: {len(t.measures) - total_measures_rendered}')

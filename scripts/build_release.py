"""Rebuild the single-file guide and hash manifest; optionally create a ZIP outside the bundle."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {'__pycache__', '.git', '.venv', 'node_modules', 'dist'}


def files(root):
    return sorted(p for p in root.rglob('*') if p.is_file() and not any(s in EXCLUDE for s in p.relative_to(root).parts) and p.suffix not in {'.pyc', '.zip'})


def build(root=ROOT, zip_path=None):
    docs = [root/p for p in ['START-HERE.md','SKILL.md','PORTABILITY.md']]
    docs += sorted((root/'references').glob('*.md'))
    docs += sorted((root/'examples').glob('*.md'))
    docs += sorted((root/'templates').glob('*.md'))
    docs += [root/'PROVENANCE.md',root/'LICENSE-NOTICE.md']
    docs = [p for p in docs if p.exists()]
    ids = {p.resolve():f'chapter-{i+1:02d}' for i,p in enumerate(docs)}
    chunks = ['# 动态叙事制作完整手册\n\n版本2.0.0。方法正文与模板合并版；可执行工具、图片与测试使用完整包。先读入口，按任务跳读。\n']
    chunks += ['- ['+p.stem+'](#'+ids[p.resolve()]+')' for p in docs]
    for p in docs:
        text = p.read_text(encoding='utf-8')
        text = re.sub(r'\A---\n.*?\n---\n', '', text, flags=re.S)
        def rewrite(match):
            label, target = match.group(1), match.group(2)
            if re.match(r'https?://|#',target):
                return match.group(0)
            resolved = (p.parent/target.split('#')[0]).resolve()
            if resolved in ids:
                return f'[{label}](#{ids[resolved]})'
            return label + '（完整包文件：' + target + '）'
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',rewrite,text)
        chunks.append(f'\n\n---\n\n<a id="{ids[p.resolve()]}"></a>\n\n'+text)
    chunks.append('\n\n## 机读项目空模板\n\n```json\n'+(root/'templates/project.json').read_text(encoding='utf-8')+'\n```\n')
    (root/'FULL-GUIDE.md').write_text('\n'.join(chunks),encoding='utf-8')
    entries = {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files(root) if p.name != 'MANIFEST.json'}
    (root/'MANIFEST.json').write_text(json.dumps({'version':'2.0.0','algorithm':'sha256','files':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if zip_path:
        zip_path = Path(zip_path).resolve()
        if zip_path.is_relative_to(root.resolve()):
            raise ValueError('ZIP must be outside bundle to avoid including itself')
        zip_path.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as archive:
            for p in files(root):
                archive.write(p,Path('visual-story-production')/p.relative_to(root))
        with zipfile.ZipFile(zip_path) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP CRC failed')
    return len(entries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip',type=Path)
    args = parser.parse_args()
    print(json.dumps({'manifestFiles':build(zip_path=args.zip),'zip':str(args.zip) if args.zip else None}))

"""Check local references, manifest hashes and accidental project dependencies. No network calls."""
from pathlib import Path
import hashlib
import json
import re
from build_release import files

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    errors = []
    all_files = files(root)
    for p in all_files:
        if p.suffix.lower() in {'.mp4','.mov','.mp3','.wav','.exe','.dll'}:
            errors.append('Unexpected project media/binary: '+p.name)
        if p.suffix in {'.md','.json','.py','.yml','.yaml','.svg'}:
            text = p.read_text(encoding='utf-8-sig')
            if re.search(r'[A-Za-z]:[\\/](?:Users|CodexSpace|media|WorkSpace)',text):
                errors.append('Machine-specific path: '+p.relative_to(root).as_posix())
            if re.search(r'https?://(?:localhost|127\.0\.0\.1):\d+',text):
                errors.append('Local server dependency: '+p.relative_to(root).as_posix())
        if p.suffix == '.json':
            try:
                json.loads(p.read_text(encoding='utf-8-sig'))
            except ValueError:
                errors.append('Invalid JSON: '+p.name)
        if p.suffix != '.md':
            continue
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if re.match(r'https?://|mailto:|#',target):
                continue
            path = (p.parent / target.split('#')[0]).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                errors.append('Missing/outside link in '+p.name+': '+target)
    skill = (root/'SKILL.md').read_text(encoding='utf-8')
    if not re.search(r'\A---\nname: visual-story-production\ndescription: .+\n',skill):
        errors.append('Invalid skill metadata')
    try:
        manifest = json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))['files']
        actual = {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in all_files if p.name != 'MANIFEST.json'}
        if actual != manifest:
            errors.append('Manifest mismatch: rebuild after intentional changes')
    except (OSError,ValueError,KeyError):
        errors.append('Missing/invalid MANIFEST.json')
    return {'passed':not errors,'files':len(all_files),'errors':errors,'scope':'Local integrity and portability, not artistic or cross-harness certification'}


if __name__ == '__main__':
    report = validate()
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report['passed'] else 1)

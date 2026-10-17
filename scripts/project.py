"""Portable record initializer and structural checker, Python 3.10+, standard library.
Does not render, transcribe, certify aesthetics, or modify source material.
"""
import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1]
MODES = {'static', 'sampled-playback', 'continuous-motion', 'audio', 'technical', 'user-feedback'}
STATES = {'planned', 'storyboard', 'implemented', 'observed', 'accepted'}


def init(destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Refusing to overwrite an existing path')
    destination.mkdir(parents=True)
    for folder in ('source', 'assets', 'storyboards', 'evidence'):
        (destination / folder).mkdir()
    for item in (BUNDLE / 'templates').iterdir():
        if item.is_file():
            shutil.copy2(item, destination / item.name)
    (destination / 'source/narration.txt').write_text('', encoding='utf-8')
    return destination


def check(root):
    root = Path(root).resolve()
    errors, warnings = [], []

    def file_for(value, label):
        if not isinstance(value, str) or not value or Path(value).is_absolute() or ':' in value or '\\' in value:
            errors.append(label + ': expected portable relative path')
            return None
        p = (root / value).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            errors.append(label + ': missing file or path escapes project')
            return None
        return p

    def num(value):
        return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)

    def array(row, key, label):
        value = row.get(key, [])
        if not isinstance(value, list):
            errors.append(label + ': ' + key + ' must be a list')
            return []
        return value

    def span(value, maximum, label, integer=False):
        valid = isinstance(value, list) and len(value) == 2 and all(num(x) for x in value)
        if integer and valid:
            valid = all(isinstance(x, int) for x in value)
        if not valid or not 0 <= value[0] < value[1] <= maximum:
            errors.append(label + ': invalid range')
            return False
        return True

    try:
        data = json.loads((root / 'project.json').read_text(encoding='utf-8-sig'))
        if not isinstance(data, dict):
            raise ValueError('project.json must be an object')
    except (OSError, ValueError) as exc:
        return {'structuralPass': False, 'errors': [str(exc)], 'warnings': [], 'qualityCertified': False}
    if data.get('schemaVersion') != 1:
        errors.append('Unsupported schemaVersion')
    if not data.get('title') or not data.get('revision'):
        errors.append('Title and revision are required')
    stage = data.get('stage')
    if stage not in {'research', 'storyboard', 'web', 'export'}:
        errors.append('Invalid stage')
    if not isinstance(data.get('exportAuthorized'), bool):
        errors.append('exportAuthorized must be boolean')
    if stage == 'export' and data.get('exportAuthorized') is not True:
        errors.append('Export stage is not authorized')
    source = data.get('source', {})
    if not isinstance(source, dict):
        source = {}
    source_file = file_for(source.get('path'), 'source')
    text = ''
    if source_file:
        raw = source_file.read_bytes()
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeError:
            errors.append('Source must be UTF-8; preserve original separately when transcoding')
        if not text.strip():
            errors.append('Source is empty')
        if hashlib.sha256(raw).hexdigest() != source.get('sha256'):
            errors.append('Source hash mismatch or unset; verify intended source before recording hash')
    tables = {}
    for name in ('assets', 'speakers', 'scenes', 'evidence'):
        rows = data.get(name)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            errors.append(name + ': expected list of objects')
            rows = []
        table = {}
        for row in rows:
            ident = row.get('id')
            if not isinstance(ident, str) or not ident or ident in table:
                errors.append(name + ': missing or duplicate id')
            else:
                table[ident] = row
        tables[name] = table
    for ident, row in tables['assets'].items():
        file_for(row.get('path'), 'asset ' + ident)
        if not row.get('purpose') or not row.get('provenance'):
            errors.append('Asset ' + ident + ': purpose and provenance required')
    for ident, row in tables['speakers'].items():
        if not row.get('name'):
            errors.append('Speaker ' + ident + ': name required')
        if row.get('identityAssetId') is not None and row['identityAssetId'] not in tables['assets']:
            errors.append('Speaker ' + ident + ': unknown identity asset')
    for ident, row in tables['evidence'].items():
        file_for(row.get('path'), 'evidence ' + ident)
        scene = tables['scenes'].get(row.get('scene'))
        if not scene:
            errors.append('Evidence ' + ident + ': unknown scene')
        elif num(scene.get('duration')):
            span(row.get('range'), scene['duration'], 'evidence ' + ident)
        if row.get('mode') not in MODES or not row.get('findings'):
            errors.append('Evidence ' + ident + ': mode and findings required')
        if row.get('revision') != data.get('revision'):
            errors.append('Evidence ' + ident + ': stale revision')
    previous_end = 0.0
    for ident, row in tables['scenes'].items():
        start, duration = row.get('start'), row.get('duration')
        if not num(start) or not num(duration) or start < 0 or duration <= 0:
            errors.append('Scene ' + ident + ': invalid start/duration')
            continue
        if abs(start - previous_end) > 0.001:
            errors.append('Scene ' + ident + ': gap, overlap or unordered timeline')
        previous_end = start + duration
        span(row.get('sourceRange'), len(text), 'scene ' + ident, integer=True)
        if not row.get('informationTask') or row.get('status') not in STATES:
            errors.append('Scene ' + ident + ': task/status required')
        frames = row.get('keyframes', [])
        if not isinstance(frames, list):
            frames = []
            errors.append('Scene ' + ident + ': keyframes must be a list')
        if row.get('status') != 'planned' and row.get('smallFix') is not True and len(frames) < 3:
            errors.append('Scene ' + ident + ': at least three storyboard frames required')
        for frame in frames:
            if not isinstance(frame, dict):
                errors.append('Invalid keyframe object')
                continue
            file_for(frame.get('path'), 'keyframe ' + ident)
            if not num(frame.get('localTime')) or not 0 <= frame['localTime'] <= duration:
                errors.append('Scene ' + ident + ': keyframe time outside scene')
        for cue in array(row, 'cues', 'Scene ' + ident):
            if not isinstance(cue, dict) or not num(cue.get('at')) or not 0 <= cue['at'] <= duration or not cue.get('meaning'):
                errors.append('Scene ' + ident + ': invalid cue')
        for asset_id in array(row, 'assetIds', 'Scene ' + ident):
            if not isinstance(asset_id, str) or asset_id not in tables['assets']:
                errors.append('Scene ' + ident + ': unknown asset')
        for quote in array(row, 'quotes', 'Scene ' + ident):
            if not isinstance(quote, dict):
                errors.append('Invalid quote object')
                continue
            qr = quote.get('sourceRange')
            if span(qr, len(text), 'quote ' + ident, integer=True):
                if text[qr[0]:qr[1]] != quote.get('text'):
                    errors.append('Scene ' + ident + ': quote differs from source')
                sr = row.get('sourceRange')
                if isinstance(sr, list) and len(sr) == 2 and all(num(x) for x in sr) and not sr[0] <= qr[0] < qr[1] <= sr[1]:
                    errors.append('Scene ' + ident + ': quote outside scene source range')
            if not isinstance(quote.get('speakerId'), str) or quote.get('speakerId') not in tables['speakers']:
                errors.append('Scene ' + ident + ': unknown quote speaker')
        evidence = [e for e in tables['evidence'].values() if e.get('scene') == ident]
        if row.get('status') in {'observed', 'accepted'} and not evidence:
            errors.append('Scene ' + ident + ': observation claimed without evidence')
        if row.get('status') == 'accepted' and not any(e.get('mode') == 'user-feedback' for e in evidence):
            errors.append('Scene ' + ident + ': acceptance claimed without user feedback')
        if not any(e.get('mode') == 'continuous-motion' for e in evidence):
            warnings.append('Scene ' + ident + ': continuous motion not recorded; static/technical checks cannot replace it')
    if not tables['scenes']:
        errors.append('No scenes planned')
    total = data.get('durationSeconds')
    if total is not None and (not num(total) or abs(total - previous_end) > 0.001):
        errors.append('Total duration mismatch')
    return {'structuralPass': not errors, 'errors': errors, 'warnings': warnings,
            'qualityCertified': False, 'scope': 'Record consistency only; inspect actual artifacts and observations',
            'scenes': len(tables['scenes']), 'revision': data.get('revision')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'check'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if args.command == 'init':
        try:
            print('Created records at ' + str(init(args.directory)))
        except (OSError, ValueError) as exc:
            parser.exit(2, str(exc) + '\n')
    else:
        report = check(args.directory)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(0 if report['structuralPass'] else 1)


if __name__ == '__main__':
    main()

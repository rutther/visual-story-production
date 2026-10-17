import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project = load('project')
motion = load('motion_math')


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)/'nested 目录'/'example'
        shutil.copytree(ROOT/'examples/process-project',self.root)
        self.data = json.loads((self.root/'project.json').read_text(encoding='utf-8'))

    def tearDown(self):
        self.temp.cleanup()

    def check(self):
        (self.root/'project.json').write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')
        return project.check(self.root)

    def test_relocated_example_and_limits(self):
        result = self.check()
        self.assertTrue(result['structuralPass'],result)
        self.assertFalse(result['qualityCertified'])
        self.assertTrue(result['warnings'])

    def test_initializer_refuses_overwrite(self):
        with self.assertRaises(ValueError):
            project.init(self.root)
        dest = Path(self.temp.name)/'fresh'
        project.init(dest)
        self.assertFalse(project.check(dest)['structuralPass'])

    def test_source_mutation_detected(self):
        (self.root/'source/narration.txt').write_text('偷偷改稿',encoding='utf-8')
        self.assertFalse(self.check()['structuralPass'])

    def test_export_boundary(self):
        self.data['stage'] = 'export'
        self.assertIn('Export stage is not authorized',self.check()['errors'])

    def test_missing_storyboard(self):
        self.data['scenes'][0]['keyframes'][1]['path']='storyboards/missing.svg'
        self.assertFalse(self.check()['structuralPass'])

    def test_path_escape(self):
        self.data['source']['path']='../outside.txt'
        self.assertFalse(self.check()['structuralPass'])

    def test_nonfinite_time(self):
        self.data['scenes'][0]['duration']=float('nan')
        self.assertFalse(self.check()['structuralPass'])

    def test_timeline_overlap(self):
        new = copy.deepcopy(self.data['scenes'][0])
        new['id']='second'
        new['start']=11
        self.data['scenes'].append(new)
        self.assertTrue(any('overlap' in x for x in self.check()['errors']))

    def test_cue_outside(self):
        self.data['scenes'][0]['cues'][0]['at']=13
        self.assertFalse(self.check()['structuralPass'])

    def test_malformed_optional_lists(self):
        scene = self.data['scenes'][0]
        scene.update(cues=None, quotes={}, assetIds='not-a-list')
        result = self.check()
        self.assertFalse(result['structuralPass'])
        self.assertEqual(sum('must be a list' in e for e in result['errors']), 3)

    def test_unhashable_asset_and_speaker_ids(self):
        scene = self.data['scenes'][0]
        scene['assetIds'] = [{}]
        scene['quotes'] = [{'sourceRange':[0,2], 'text':'原水', 'speakerId':[]}]
        self.assertFalse(self.check()['structuralPass'])

    def test_quote_and_unknown_identity(self):
        self.data['scenes'][0]['quotes']=[{'text':'编造的话','sourceRange':[0,4],'speakerId':'unknown'}]
        errors=self.check()['errors']
        self.assertTrue(any('quote differs' in x for x in errors))
        self.assertTrue(any('unknown quote speaker' in x for x in errors))

    def test_evidence_is_not_acceptance(self):
        self.data['scenes'][0]['status']='accepted'
        self.assertTrue(any('acceptance claimed' in x for x in self.check()['errors']))

    def test_stale_evidence(self):
        (self.root/'evidence.md').write_text('Static layout inspected, not motion.',encoding='utf-8')
        self.data['evidence']=[{'id':'e1','scene':'process-001','revision':'old','mode':'static','range':[0,1],'path':'evidence.md','findings':'one state'}]
        self.assertTrue(any('stale revision' in x for x in self.check()['errors']))

    def test_unicode_codepoint_quote(self):
        text='说明😀“进入滤芯”结束'
        raw=text.encode('utf-8')
        (self.root/'source/narration.txt').write_bytes(raw)
        self.data['source']['sha256']=hashlib.sha256(raw).hexdigest()
        self.data['speakers']=[{'id':'teacher','name':'示例讲师','identityAssetId':None}]
        scene=self.data['scenes'][0]
        scene['sourceRange']=[0,len(text)]
        start=text.index('进入')
        scene['quotes']=[{'text':'进入滤芯','sourceRange':[start,start+4],'speakerId':'teacher'}]
        self.assertTrue(self.check()['structuralPass'])


class MotionTests(unittest.TestCase):
    def test_seek_has_no_history(self):
        times=[0,6,12,3,6]
        values=[motion.progress(t,4,4) for t in times]
        self.assertEqual(values,[0,0.5,1,0,0.5])

    def test_zero_duration_and_bad_input(self):
        self.assertEqual(motion.progress(1,2,0),0)
        self.assertEqual(motion.progress(2,2,0),1)
        with self.assertRaises(ValueError):
            motion.progress(1,0,-1)

    def test_crop_annotation_alignment(self):
        transform=motion.cover_transform((100,200,400,200),(800,400))
        self.assertEqual(motion.project_point((100,200),transform),(0,0))
        self.assertEqual(motion.project_point((500,400),transform),(800,400))

    def test_cover_center(self):
        transform=motion.cover_transform((0,0,1000,500),(300,300))
        self.assertEqual(motion.project_point((500,250),transform),(150,150))

    def test_cumulative_frames(self):
        boundaries=motion.frame_boundaries([0.1]*10,24)
        self.assertEqual(boundaries[-1],24)
        self.assertEqual(sum(b-a for a,b in zip(boundaries,boundaries[1:])),24)


if __name__ == '__main__':
    unittest.main()

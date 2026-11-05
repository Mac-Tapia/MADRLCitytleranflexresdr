"""Prepare/compile a dependency patch without changing that dependency."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
relative = 'external/HARL/harl/common/valuenorm.py'
source = (ROOT/relative).read_text(encoding='utf-8')
old = '''        self.running_mean = nn.Parameter(
            torch.zeros(input_shape), requires_grad=False
        ).to(**self.tpdv)
        self.running_mean_sq = nn.Parameter(
            torch.zeros(input_shape), requires_grad=False
        ).to(**self.tpdv)
        self.debiasing_term = nn.Parameter(torch.tensor(0.0), requires_grad=False).to(
            **self.tpdv
        )'''
new = '''        self.running_mean = nn.Parameter(
            torch.zeros(input_shape, **self.tpdv), requires_grad=False
        )
        self.running_mean_sq = nn.Parameter(
            torch.zeros(input_shape, **self.tpdv), requires_grad=False
        )
        self.debiasing_term = nn.Parameter(
            torch.tensor(0.0, **self.tpdv), requires_grad=False
        )'''
assert source.count(old) == 1
candidate = source.replace(old, new)
compile(candidate, relative, 'exec')
candidate_path = ROOT/'.superpowers/sdd/remediacion_integrada/harl_valuenorm_candidate.py.txt'
candidate_path.write_text(candidate, encoding='utf-8')
diff = ''.join(difflib.unified_diff(source.splitlines(True), candidate.splitlines(True),
                                 fromfile='a/'+relative, tofile='b/'+relative))
(OUT/'proposed_harl_valuenorm.patch').write_text(diff, encoding='utf-8')
report = {'target': relative, 'applied': False, 'candidate_compiles': True,
          'candidate_path': candidate_path.relative_to(ROOT).as_posix(),
          'before_sha256_lf': hashlib.sha256(source.encode('utf-8')).hexdigest(),
          'after_sha256_lf': hashlib.sha256(candidate.encode('utf-8')).hexdigest()}
(OUT/'harl_patch_preflight.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))

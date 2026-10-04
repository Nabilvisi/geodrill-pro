"""Record the exact verified local development environment and synthetic fixtures."""
from importlib.metadata import distributions
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.api import demo

lines = sorted('{}=={}'.format(d.metadata['Name'], d.version) for d in distributions() if d.metadata['Name'].lower() != 'pip')
(ROOT / 'requirements-lock.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
fixtures = ROOT / 'simulation' / 'fixtures'
fixtures.mkdir(parents=True, exist_ok=True)
for name, data in [('synthetic-drilling.csv', demo.telemetry()), ('synthetic-survey.csv', demo.SURVEY), ('synthetic-logs.las', demo.LAS)]:
    (fixtures / name).write_bytes(data)
print('Dependency lock and synthetic fixtures written.')

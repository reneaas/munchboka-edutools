"""Build an account-home extraction archive, excluding credentials and tests."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root = Path(__file__).resolve().parent
out = root / 'quiz-subdomain.zip'
with ZipFile(out, 'w', ZIP_DEFLATED) as archive:
    for folder, destination in [('public', 'public_html/quiz'), ('private/livequiz', 'jeopardy-private/livequiz')]:
        source = root / folder
        for path in sorted(source.rglob('*')):
            if path.is_file():
                archive.write(path, str(Path(destination) / path.relative_to(source)))
print(out)

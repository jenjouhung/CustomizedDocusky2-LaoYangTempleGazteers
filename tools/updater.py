"""Replace only the web core from a checked release; retain data and rollback on failure."""
import json, zipfile, hashlib, tempfile, shutil
from pathlib import Path
from packages import ROOT, backup
def update(path):
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp,zipfile.ZipFile(path) as z:
        stage=Path(tmp); info=json.loads(z.read('release.json'))
        if info.get('schema')!=1:raise ValueError('更新格式不相容')
        checks=info['files'];names=z.namelist()
        if len(set(names))!=len(names) or set(names)!=set(checks)|{'release.json'}:raise ValueError('更新清單不一致')
        if sum(x.file_size for x in z.infolist())>100*1024**2:raise ValueError('更新檔過大')
        for name,sha in checks.items():
            target=(stage/name).resolve()
            if not name.startswith('web/') or not target.is_relative_to((stage/'web').resolve()):raise ValueError('更新只能包含前端程式')
            data=z.read(name)
            if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('更新校驗失敗')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        for name in ['index.html','app.js','style.css','core/data.js','core/query.js','core/state.js','core/facets.js']:
            if not (stage/'web'/name).is_file():raise ValueError('更新缺少必要檔案：'+name)
        backup(automatic=True)
        old=stage/'previous-web';(ROOT/'web').rename(old)
        try:(stage/'web').rename(ROOT/'web')
        except Exception:
            old.rename(ROOT/'web');raise
        retained=ROOT/'previous-release'
        if retained.exists():shutil.rmtree(retained)
        old.rename(retained)

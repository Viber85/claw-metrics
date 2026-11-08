"""Cache the exact licensed Meson wrap patches, verifying upstream SHA256 pins."""
import base64,configparser,hashlib,pathlib,sys


def cache(subprojects,bundled):
    target=subprojects/'packagecache';target.mkdir(exist_ok=True)
    count=0
    for path in sorted(subprojects.glob('*.wrap')):
        config=configparser.ConfigParser(interpolation=None);config.read(path)
        if not config.has_section('wrap-file') or not config.has_option('wrap-file','patch_hash'):continue
        wrap=config['wrap-file'];name=wrap['patch_filename']
        if pathlib.Path(name).name!=name:raise ValueError('Invalid upstream patch filename')
        raw=base64.b64decode(''.join((bundled/(path.stem+'.zip.b64')).read_text().split()),validate=True)
        if hashlib.sha256(raw).hexdigest()!=wrap['patch_hash']:raise ValueError('Pinned patch hash mismatch: '+path.name)
        (target/name).write_bytes(raw);count+=1
        print('Verified cached upstream patch:',name)
    if count!=4:raise ValueError('Expected exactly four pinned upstream patches')


if __name__=='__main__':cache(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))

"""Cache the exact licensed Meson wrap patches, verifying upstream SHA256 pins."""
import base64,configparser,hashlib,pathlib,re,subprocess,sys


def cache(subprojects,bundled):
    target=subprojects/'packagecache';target.mkdir(exist_ok=True)
    count=0
    for path in sorted(subprojects.glob('*.wrap')):
        config=configparser.ConfigParser(interpolation=None);config.read(path)
        if not config.has_section('wrap-file'):continue
        wrap=config['wrap-file']
        # GitHub archive redirects can fail independently of codeload. The
        # canonical codeload bytes have the same upstream-pinned source hash.
        source=target/wrap['source_filename']
        if source.name!=wrap['source_filename']:raise ValueError('Invalid upstream source filename')
        if not source.exists() or hashlib.sha256(source.read_bytes()).hexdigest()!=wrap['source_hash']:
            url=wrap['source_url']
            archive=re.fullmatch(r'https://github.com/([^/]+/[^/]+)/archive/(.+)\.(tar\.gz|zip)',url)
            if archive:url=f'https://codeload.github.com/{archive[1]}/{archive[3]}/{archive[2]}'
            temporary=source.with_name(source.name+'.download')
            subprocess.run(['curl','--fail','--silent','--show-error','--location','--retry','4','--connect-timeout','15','--max-time','60',url,'-o',str(temporary)],check=True)
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=wrap['source_hash']:raise ValueError('Pinned source hash mismatch: '+path.name)
            temporary.replace(source)
        print('Verified cached upstream source:',source.name,flush=True)
        if 'patch_hash' not in wrap:continue
        name=wrap['patch_filename']
        if pathlib.Path(name).name!=name:raise ValueError('Invalid upstream patch filename')
        raw=base64.b64decode(''.join((bundled/(path.stem+'.zip.b64')).read_text().split()),validate=True)
        if hashlib.sha256(raw).hexdigest()!=wrap['patch_hash']:raise ValueError('Pinned patch hash mismatch: '+path.name)
        (target/name).write_bytes(raw);count+=1
        print('Verified cached upstream patch:',name)
    if count!=4:raise ValueError('Expected exactly four pinned upstream patches')


if __name__=='__main__':cache(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))

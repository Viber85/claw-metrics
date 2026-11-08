"""Compare actual browser preview rectangles with real ImGui and production slots."""
import argparse,copy,hashlib,json,pathlib,re,shutil,subprocess,tempfile,urllib.request
from check_modular_imgui import HASHES,ROOT,TEXT,raster,schema


def node(name,children=(),token=None,axis='row',**extra):
    return dict(id=name,name=name,kind='metric' if token else 'group',token=token or 'fps.value',children=list(children),axis=axis,align='start',selfAlign='auto',visible=True,gap=6,padding=0,scale=100,width=180,height=44,color='',background='',opacity=100,outline=False,**extra)


def fixture():
    groups=[]
    for key in ('cpu','gpu'):
        readings=node(key+'-readings',[node(key+'-'+part,token=key+'.'+part) for part in ('load','temp','clock')])
        group=node(key,[node(key+'-label',token=key+'.label'),readings],axis='column',paddingX=12,paddingY=8)
        group.update(background='#152C55',gap=2);groups.append(group)
    memory=[]
    for key in ('ram','vram'):
        group=node(key,[node(key+'-label',token=key+'.label'),node(key+'-value',token=key+'.value',paddingX=0,paddingY=3)],paddingX=12,paddingY=4)
        group.update(background='#152C55',gap=8);memory.append(group)
    return schema.validate_layout(dict(schema='claw-modular-layout',version=1,anchor='top-left',x=16,y=16,paddingX=13,paddingY=7,root=node('overlay',[node('processors',groups),node('memory',memory)],axis='column')))


def run(args):
    output=pathlib.Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    # Use the actual production reservation strings, not shorter sample readings.
    adapter=(ROOT/'experiments/modular/mangohud_adapter.inc').read_text()
    def strings(pattern):return re.findall(r'"([^"]*)"',re.search(pattern,adapter).group(1))
    keys=strings(r'keys\[\]=\{([^}]+)\}')
    slots=strings(r'slots\[\]=\{([^}]+)\}')
    assert len(keys)==len(slots)==32
    with tempfile.TemporaryDirectory() as directory:
        tmp=pathlib.Path(directory);imgui=tmp/'imgui';imgui.mkdir()
        for name,digest in HASHES.items():
            raw=(pathlib.Path(args.imgui_dir)/name).read_bytes() if args.imgui_dir else urllib.request.urlopen('https://raw.githubusercontent.com/ocornut/imgui/v1.89.9/'+name,timeout=30).read()
            raw=(raw.decode().rstrip()+'\n').encode();assert hashlib.sha256(raw).hexdigest()==digest
            (imgui/name).write_bytes(raw)
        probe=tmp/'probe'
        subprocess.run(['g++','-std=c++14','-O1','-I',str(imgui),'-I',str(ROOT/'experiments/native'),str(ROOT/'tools/preview_parity_probe.cpp'),*[str(imgui/name) for name in HASHES if name.endswith('.cpp')],'-o',str(probe)],check=True)
        snapshot=tmp/'snapshot.tsv';snapshot.write_text(''.join(f'{key}\t{TEXT[key]}\t{slot}\n' for key,slot in zip(keys,slots) if key in TEXT))
        cases=[]
        for size in (18,12,28):
            for units in (True,False):
                for weight in ('Regular','Light','SemiBold','Bold'):
                    doc=fixture();doc['root']['scale']={12:85,18:100,28:125}[size]
                    name=f'{size}-{int(units)}-{weight.lower()}'
                    transport=tmp/'layout';target=output/name
                    def native():
                        transport.write_text(schema.encode_native(doc))
                        font=pathlib.Path(args.font_dir)/f'BarlowSemiCondensed-{weight}.ttf'
                        subprocess.run([str(probe),str(font),str(transport),str(snapshot),str(target),str(size),str(int(units))],check=True)
                        return json.loads(target.with_suffix('.json').read_text())['boxes']
                    boxes=native()
                    # Reproduce the user's padded RAM/VRAM values: align each
                    # lower card with its processor card to the nearest pixel.
                    for index,key in enumerate(('ram','vram')):
                        target_width=boxes[('cpu','gpu')[index]][2]
                        delta=target_width-boxes[key][2]
                        assert delta>=0
                        doc['root']['children'][1]['children'][index]['children'][1]['paddingX']=round(delta/2)
                    boxes=native()
                    for upper,lower in (('cpu','ram'),('gpu','vram')):assert abs(boxes[upper][2]-boxes[lower][2])<=1.001
                    cases.append(dict(layout=doc,size=size,units=units,weight=weight.lower(),boxes=boxes))
                    if size==18 and units and weight=='Regular':raster(target.with_suffix('.json'))
        manifest=output/'cases.json';manifest.write_text(json.dumps(cases))
        print(f'PASS real ImGui: {len(cases)} padded CPU/GPU/RAM/VRAM cases, matching card widths, nested scale, 4 font weights and both unit modes.',flush=True)
        if not args.native_only:
            browser=args.browser or shutil.which('google-chrome') or shutil.which('chromium')
            if not browser:raise RuntimeError('A real Chrome/Chromium is required; no mock geometry fallback')
            subprocess.run(['node','tools/check_preview_parity.mjs',str(manifest),str(output/'preview.html'),browser],cwd=ROOT,check=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--imgui-dir');parser.add_argument('--font-dir',required=True);parser.add_argument('--output',required=True);parser.add_argument('--browser');parser.add_argument('--native-only',action='store_true');run(parser.parse_args())

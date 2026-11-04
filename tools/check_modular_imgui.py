"""Real ImGui text measurement and draw-list fixtures for modular layout v1."""
import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_native_layout import HASHES
spec = importlib.util.spec_from_file_location('schema', ROOT / 'experiments/modular/schema.py')
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)

TEXT = {'fps.label':'FPS', 'fps.value':'84', 'fps.ms':'11.9 ms', 'cpu.label':'CPU',
        'cpu.load':'36%', 'cpu.temp':'54°C', 'cpu.clock':'3500 MHz', 'cpu.power':'8.6 W',
        'gpu.label':'GPU', 'gpu.load':'72%', 'gpu.temp':'52°C', 'gpu.clock':'1750 MHz',
        'gpu.power':'12.4 W', 'ram.label':'RAM', 'ram.value':'12.6 GiB',
        'vram.label':'VRAM', 'vram.value':'7.4 GiB', 'tdp.value':'TDP 28 W',
        'battery.power':'DRAW 27 W'}


def fixture(document):
    nodes = []
    def flatten(n):
        index = len(nodes)
        nodes.append((n, []))
        for child in n['children']:
            nodes[index][1].append(flatten(child))
        return index
    flatten(document['root'])
    lines = ['inline std::vector<claw_modular::Node> fixture(){', f'std::vector<claw_modular::Node> out({len(nodes)});']
    for i, (n, children) in enumerate(nodes):
        for key, value in [('id',json.dumps(n['id'])), ('token',json.dumps(n['token'])),
                           ('group',str(n['kind']=='group').lower()), ('visible',str(n['visible']).lower()),
                           ('axis','claw_modular::Axis::'+n['axis'].title()),
                           ('align','claw_modular::Align::'+n['align'].title()),
                           ('gap',str(n['gap'])), ('padding',str(n['padding'])),
                           ('scale',str(n['scale']/100)), ('width',str(n['width'])),
                           ('height',str(n['height'])), ('children','{'+','.join(map(str,children))+'}')]:
            lines.append(f'out[{i}].{key}={value};')
    lines += ['return out;}', 'inline std::string reading(const std::string& key){']
    for key, text in TEXT.items():
        lines.append('if(key=='+json.dumps(key)+')return '+json.dumps(text, ensure_ascii=False)+';')
    lines += ['return "--";}', 'inline ImU32 color(const std::string& key){',
              'if(key.find("fps")==0||key=="gpu.label")return IM_COL32(48,229,80,255);',
              'if(key=="cpu.label")return IM_COL32(55,201,239,255);',
              'if(key=="tdp.value")return IM_COL32(255,189,69,255);',
              'if(key=="battery.power"||key=="ram.label"||key=="vram.label")return IM_COL32(190,110,220,255);',
              'return IM_COL32(240,242,245,255); }']
    return '\n'.join(lines)


def raster(path):
    import numpy as np
    from PIL import Image
    data = json.loads(path.read_text())
    atlas = np.asarray(Image.open(path.with_name(path.stem+'-atlas.pgm')), dtype=float)/255
    h,w=data['height'],data['width']; canvas=np.empty((h,w,3),dtype=float);canvas[:]=[25,38,54]
    for draw in data['lists']:
        vertices=np.asarray(draw['v'],dtype=float);indices=draw['idx']
        for command in draw['cmd']:
            start,count,cx,cy,cx2,cy2=command[:6];base=command[6] if len(command)>6 else 0
            for offset in range(int(start),int(start+count),3):
                v=vertices[[indices[offset]+base,indices[offset+1]+base,indices[offset+2]+base]];xy=v[:,:2]
                lo=np.maximum(np.floor(xy.min(0)).astype(int),[max(0,int(cx)),max(0,int(cy))]);hi=np.minimum(np.ceil(xy.max(0)).astype(int),[min(w,int(cx2)),min(h,int(cy2))])
                if np.any(hi<=lo):continue
                a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-8:continue
                yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]];xx=xx+.5;yy=yy+.5
                u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
                vv=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;ww=1-u-vv
                mask=(u>=0)&(vv>=0)&(ww>=0);weight=np.stack([u,vv,ww],axis=-1)
                uv=weight@v[:,2:4];tx=np.clip(uv[:,:,0]*atlas.shape[1]-.5,0,atlas.shape[1]-1);ty=np.clip(uv[:,:,1]*atlas.shape[0]-.5,0,atlas.shape[0]-1)
                ix=tx.astype(int);iy=ty.astype(int);jx=np.minimum(ix+1,atlas.shape[1]-1);jy=np.minimum(iy+1,atlas.shape[0]-1);fx=tx-ix;fy=ty-iy
                alpha_tex=(atlas[iy,ix]*(1-fx)+atlas[iy,jx]*fx)*(1-fy)+(atlas[jy,ix]*(1-fx)+atlas[jy,jx]*fx)*fy
                packed=v[:,4].astype(np.uint32);colors=np.stack([(packed>>shift)&255 for shift in (0,8,16,24)],axis=-1).astype(float)
                col=weight@colors;alpha=(col[:,:,3]/255*alpha_tex*mask)[:,:,None];region=canvas[lo[1]:hi[1],lo[0]:hi[0]];region[:]=col[:,:,:3]*alpha+region*(1-alpha)
    Image.fromarray(np.clip(canvas,0,255).astype('uint8')).save(path.with_suffix('.png'))


def run(args):
    output=pathlib.Path(args.render_dir);output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        tmp=pathlib.Path(directory);imgui=tmp/'imgui';imgui.mkdir()
        for name,expected in HASHES.items():
            if args.imgui_dir:data=(pathlib.Path(args.imgui_dir)/name).read_bytes()
            else:
                with urllib.request.urlopen('https://raw.githubusercontent.com/ocornut/imgui/v1.89.9/'+name,timeout=30) as response:data=response.read()
            data=(data.decode().rstrip()+'\n').encode();assert hashlib.sha256(data).hexdigest()==expected,name
            (imgui/name).write_bytes(data)
        if args.font:
            font=pathlib.Path(args.font)
            import main
            assert main.valid_git_font(font.read_bytes(),main.BARLOW_BLOBS['regular'][1]),'Unexpected Barlow font'
        else:
            font=tmp/'ClawSans.ttf';font.write_bytes(gzip.decompress(base64.b64decode((ROOT/'assets/ClawSans.ttf.gz.b64').read_bytes())))
            import main
            assert hashlib.sha256(font.read_bytes()).hexdigest()==main.FONT_SHA256
        for name in ('two-rows','graph-focus','horizontal','vertical','graph-below','separator'):
            source='graph-below' if name=='separator' else name
            preset=ROOT/('tests/fixtures' if source=='graph-below' else 'assets/modular' if source in ('horizontal','vertical') else 'experiments/modular')/(source+'.json')
            document=schema.load_layout(preset.read_text())
            if name=='separator':
                from copy import deepcopy
                line=deepcopy(document['root']['children'][-1])
                line.update(id='fixture-separator',token='separator',name='Separator line',width=160,height=2,color='#ABCDEF')
                document['root']['children'].insert(1,line)
                document=schema.validate_layout(document)
            if name=='horizontal':
                document['root']['children'][0]['selfAlign']='end'
            (tmp/'modular_fixture.h').write_text(fixture(document))
            transport=tmp/'input.layout';transport.write_text(schema.encode_native(document))
            binary=tmp/'probe'
            subprocess.run(['g++','-std=c++14','-O1','-I',str(imgui),'-I',str(tmp),'-I',str(ROOT/'experiments/native'),
                            str(ROOT/'tools/modular_imgui_probe.cpp'),*[str(imgui/n) for n in HASHES if n.endswith('.cpp')],'-o',str(binary)],check=True)
            for width,height in ((1280,800),(1920,1080)):
                for style in range(6):
                    target=output/f'{name}-{width}x{height}-style{style}'
                    subprocess.run([str(binary),str(font),str(width),str(height),str(target),str(transport),str(style)],check=True)
                    raster(target.with_suffix('.json'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--imgui-dir');parser.add_argument('--font');parser.add_argument('--render-dir',required=True);run(parser.parse_args())

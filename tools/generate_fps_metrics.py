"""Generate SVG ink metrics from the pinned fonts; requires fontTools."""
from pathlib import Path
from io import BytesIO
import argparse,base64,gzip,json
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--font-dir',type=Path,default=ROOT/'assets/fonts');args=p.parse_args()
fonts={key:args.font_dir/('BarlowSemiCondensed-'+weight+'.ttf') for key,weight in [('light','Light'),('regular','Regular'),('semibold','SemiBold'),('bold','Bold')]}
fonts['sans']=BytesIO(gzip.decompress(base64.b64decode((ROOT/'assets/ClawSans.ttf.gz.b64').read_bytes())))
result={}
for key,path in fonts.items():
    font=TTFont(path);cmap=font.getBestCmap();glyphs=font.getGlyphSet()
    advance=max(font['hmtx'].metrics[cmap[ord(c)]][0] for c in '0123456789')
    bounds=[];advances={}
    for c in '0123456789-':
        name=cmap[ord(c)];a=font['hmtx'].metrics[name][0];advances[c]=a
        if c=='-':continue
        pen=BoundsPen(glyphs);glyphs[name].draw(pen);x0,y0,x1,y1=pen.bounds
        offset=(advance-a)/2;bounds.append((x0+offset,y0,x1+offset,y1))
    result[key]={'units':font['head'].unitsPerEm,'lineUnits':font['hhea'].ascent-font['hhea'].descent,'advance':advance,'left':min(b[0] for b in bounds),'bottom':min(b[1] for b in bounds),'right':max(b[2] for b in bounds),'top':max(b[3] for b in bounds),'advances':advances}
(ROOT/'src/modular/fps-font-metrics.ts').write_text('// Generated from the same pinned fonts as preview-fonts.ts; tools/generate_fps_metrics.py.\nexport const fpsFontMetrics='+json.dumps(result,separators=(',',':'))+';\n')

import json
L=json.load(open('logo_parts.json')); SH=json.load(open('shadows.json'))
h=open('ident_template.html').read()
for k in ['baaBowl','wawLoop','wawTail','seenR','seenL','mid','dot','alef','hamza','stroke','tri']:
    h=h.replace('%'+k+'%',L[k])
for n,p in [('shadowW','sW'),('shadowS','sS')]:
    for v,s in zip(SH[n],'xywh'): h=h.replace(f'%{p}{s}%',f'{v:.4f}')
h=h.replace('%GLYPHS%',''.join(f'<path transform="translate({x} {y})" d="{d}"/>' for d,x,y in L['glyphs'] if d))
assert '%' not in h.split('<script>')[0].replace('100%','').replace('0%','').replace('62%','').replace('65%','').replace('-8%','').replace('108%','').replace('92%','').replace('85%','').replace('75%','').replace('90%','').replace('80%',''), 'unfilled placeholder'
open('ident.html','w').write(h)

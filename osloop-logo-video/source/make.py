import json
L=json.load(open('logo.json'))
h=open('template.html').read()
gl=''.join(f'<g><path transform="translate({x} {y})" d="{d}"/></g>' for d,x,y in L['glyphs'])
for k,v in [('%MID%',L['mid']),('%DOT%',L['dot']),('%STROKE%',L['stroke']),('%ALEF%',L['alef']),('%HAMZA%',L['hamza']),('%TRI%',L['tri']),('%GLYPHS%',gl),('%GLYPHDATA%',json.dumps([[0,x,y] for d,x,y in L['glyphs']]))]:
    h=h.replace(k,v)
open('anim.html','w').write(h)

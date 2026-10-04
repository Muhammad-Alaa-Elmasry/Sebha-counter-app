// node snap.js <format> <px> <t1> <t2> ...  → snap_<f>_<t>.png
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const [f,px,...ts]=process.argv.slice(2);
const FMT={h:[1920,1080],v:[1080,1920],art:[535.658,284.936]}[f];
(async()=>{const b=await chromium.launch();
const p=await b.newPage({viewport:{width:Math.ceil(FMT[0]*px),height:Math.ceil(FMT[1]*px)},deviceScaleFactor:f==='art'?1:1});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+process.cwd()+`/ident.html?f=${f}&px=${px}`);await p.waitForTimeout(300);
for(const t of ts){await p.evaluate(t=>render(+t),t);await p.screenshot({path:`snap_${f}_${t}.png`,clip:{x:0,y:0,width:FMT[0]*px,height:FMT[1]*px}});}
await b.close();})();

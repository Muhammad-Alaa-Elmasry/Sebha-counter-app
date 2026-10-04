// node render.js <format h|v> <px scale> <fps> <out.mp4> [crf]
// Renders the ident frame-by-frame (deterministic, no real-time playback) and muxes sound.wav.
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const {spawn}=require('child_process');
const [f='h',px='1',fps='60',outFile='ident.mp4',crf='14']=process.argv.slice(2);
const DUR=7.6, FPS=+fps, N=Math.round(DUR*FPS);
const FMT={h:[1920,1080],v:[1080,1920]}[f]; const W=Math.round(FMT[0]*px), H=Math.round(FMT[1]*px);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:W,height:H}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+process.cwd()+`/ident.html?f=${f}&px=${px}&t=0`);await p.waitForTimeout(500);
const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-c:v','png','-i','-','-i','sound.wav',
  '-c:v','libx264','-preset','slow','-crf',crf,'-tune','grain','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
  '-c:a','aac','-b:a','256k','-t',String(DUR),'-movflags','+faststart',outFile],{stdio:['pipe','inherit','inherit']});
for(let i=0;i<N;i++){await p.evaluate(t=>render(t),i/FPS);
  const buf=await p.screenshot({type:'png',clip:{x:0,y:0,width:W,height:H}});
  if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));}
ff.stdin.end();ff.on('close',c=>{console.log('done',outFile,c);b.close();});})();

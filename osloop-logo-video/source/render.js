const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const {spawn}=require('child_process');
const FPS=60,DUR=15,N=FPS*DUR;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+process.cwd()+'/anim.html');await p.waitForTimeout(500);
const ff=spawn('ffmpeg',['-y','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','video_silent.mp4'],{stdio:['pipe','ignore','inherit']});
for(let i=0;i<N;i++){await p.evaluate(t=>render(t),i/FPS);const buf=await p.screenshot({type:'jpeg',quality:95});
 if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r)); if(i%60==0)console.log('frame',i);}
ff.stdin.end();ff.on('close',c=>{console.log('ffmpeg done',c);b.close();});})();

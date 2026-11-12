(() => {
  'use strict';
  const $=id=>document.getElementById(id), video=$('source'), voice=$('voice'), canvas=$('picture');
  const ctx=canvas.getContext('2d'), musicAudio=new Audio(); musicAudio.loop=true;
  let config, recorder, chunks=[], takeBlob, takeUrl, mic, audio, destination, analyser, musicGain;
  let active=false, paused=false, scrolling=false, lastFrame=0, elapsed=0, began=0;
  let audioNodes=[], urls=[], pendingExport=false, musicLoaded=false, totalBytes=0;
  let cueWords=[], cuePosition=0, cueIndex=-1;
  video.muted=true;
  const clock=t=>`${String(Math.floor(t/60)).padStart(2,'0')}:${String(Math.floor(t%60)).padStart(2,'0')}`;
  const say=(text,error=false)=>{$('message').textContent=text;$('message').classList.toggle('error',error);};
  function buildCues(){
    const script=$('script'),text=script.innerText;
    script.replaceChildren();cueWords=[];cueIndex=-1;
    for(const part of text.split(/(\s+)/)){
      if(!part)continue;
      if(/^\s+$/.test(part)){script.append(document.createTextNode(part));continue;}
      const word=document.createElement('span');word.className='cue-word';word.textContent=part;
      script.append(word);cueWords.push(word);
    }
    cuePosition=Math.min(cuePosition,Math.max(0,cueWords.length-1));
  }
  function showCue(){
    const index=Math.min(Math.floor(cuePosition),cueWords.length-1);
    if(index<0||index===cueIndex)return;
    if(cueIndex>=0)cueWords[cueIndex]?.classList.remove('current-word');
    cueIndex=index;const word=cueWords[index];word.classList.add('current-word');
    const box=$('prompter'),bounds=box.getBoundingClientRect(),line=word.getBoundingClientRect();
    box.scrollTop+=line.top-bounds.top-box.clientHeight*.34;
    $('cue-progress').textContent=`Word ${index+1} of ${cueWords.length}`;
  }
  function setScrolling(value){
    if(value&&(!cueWords.length||$('script').isContentEditable))buildCues();
    scrolling=value;$('script').contentEditable=String(!value&&!active);
    $('scroll').textContent=value?'Pause teleprompter':'Start teleprompter';
    $('scroll').setAttribute('aria-pressed',String(value));
    if(value)showCue();
  }
  function resetCues(){
    cueWords[cueIndex]?.classList.remove('current-word');cuePosition=0;cueIndex=-1;
    $('prompter').scrollTop=0;$('cue-progress').textContent='Ready to read';
    if(scrolling)showCue();
  }
  function controls(){
    $('record').disabled=!config||!video.duration||active;
    $('pause').disabled=!active;$('stop').disabled=!active;
    $('pause').textContent=paused?'Resume take':'Pause take';
    $('preview').disabled=active;$('rewind').disabled=active;$('position').disabled=active;
    ['mode','voice-file','video-file','device','music-file','logo-file'].forEach(id=>$(id).disabled=active);
    $('export').disabled=active||pendingExport||!takeBlob;
    $('state').textContent=active?(paused?'Take paused':'Recording'):takeBlob?'Take ready':'Ready';
    $('state').classList.toggle('recording',active&&!paused);
  }
  function draw(now){
    const dt=lastFrame?Math.min((now-lastFrame)/1000,.1):0;lastFrame=now;
    ctx.fillStyle='#101b19';ctx.fillRect(0,0,1920,1080);
    if(video.readyState>=2){const scale=Math.min(1920/video.videoWidth,1080/video.videoHeight),w=video.videoWidth*scale,h=video.videoHeight*scale;ctx.drawImage(video,(1920-w)/2,(1080-h)/2,w,h);}
    if($('show-title').checked){ctx.fillStyle='rgba(15,29,25,.92)';ctx.fillRect(0,0,1920,56);ctx.fillStyle='#fff';ctx.font='24px Segoe UI';ctx.fillText($('title').value.slice(0,100),28,37);}
    if($('show-logo').checked&&$('logo').complete&&$('logo').naturalWidth){const logo=$('logo'),w=145,h=logo.naturalHeight/logo.naturalWidth*w;ctx.fillStyle='rgba(255,255,255,.96)';ctx.fillRect(1742,18,w+22,h+14);ctx.drawImage(logo,1753,25,w,h);}
    let rms=0;if(analyser){const values=new Float32Array(analyser.fftSize);analyser.getFloatTimeDomainData(values);rms=Math.sqrt(values.reduce((s,v)=>s+v*v,0)/values.length);}
    $('meter').value=Math.min(1,rms*5);$('level').textContent=rms>.19?'Loud — lower mic gain':active?'Voice level':'Voice level';
    if(musicGain&&audio){const level=$('music').checked?Number($('music-level').value):0;musicGain.gain.setTargetAtTime(rms>.025?level*.22:level,audio.currentTime,.12);}
    if(active&&!paused){elapsed+=(now-began)/1000;began=now;$('record-clock').textContent=clock(elapsed);}
    if(scrolling&&(!active||!paused)){
      cuePosition=Math.min(Math.max(0,cueWords.length-1),cuePosition+dt*Number($('speed').value)/60);showCue();
      if(cueWords.length&&cuePosition>=cueWords.length-1)setScrolling(false);
    }
    $('position').value=String(video.currentTime||0);$('time').textContent=`${clock(video.currentTime||0)} / ${clock(Number.isFinite(video.duration)?video.duration:0)}`;
    requestAnimationFrame(draw);
  }
  async function cleanup(){
    mic?.getTracks().forEach(t=>t.stop());mic=null;
    canvasStream?.getTracks().forEach(t=>t.stop());canvasStream=null;
    musicAudio.pause();voice.pause();musicAudio._take?.pause();voice._take?.pause();musicAudio._take=null;voice._take=null;
    audioNodes.forEach(n=>{try{n.stop?.();}catch(_){};try{n.disconnect();}catch(_){}});audioNodes=[];
    if(audio){await audio.close();audio=null;}analyser=null;musicGain=null;
  }
  let canvasStream;
  async function record(){
    if(active)return;
    const mode=$('mode').value;
    if(mode==='file'&&!voice.src){say('Import your narration audio file first.',true);return;}
    if(takeBlob&&!confirm('A take is already available. Download it first if needed. Start a new take?'))return;
    $('record').disabled=true;say('Preparing your take…');
    try{
      audio=new AudioContext({sampleRate:48000});await audio.resume();destination=audio.createMediaStreamDestination();
      let input;
      if(mode==='microphone'){
        mic=await navigator.mediaDevices.getUserMedia({audio:{deviceId:$('device').value?{exact:$('device').value}:undefined,echoCancellation:true,noiseSuppression:true,autoGainControl:false},video:false});
        input=audio.createMediaStreamSource(mic);
      }else if(mode==='file'){
        // A fresh element avoids reconnecting a MediaElementSource across takes.
        const element=new Audio(voice.src);voice.pause();voice._take=element;input=audio.createMediaElementSource(element);audioNodes.push(input);
      }
      if(input){
        const high=audio.createBiquadFilter();high.type='highpass';high.frequency.value=75;
        const compressor=audio.createDynamicsCompressor();compressor.threshold.value=-20;compressor.ratio.value=2.5;compressor.knee.value=12;
        analyser=audio.createAnalyser();analyser.fftSize=1024;
        input.connect(high).connect(compressor).connect(analyser).connect(destination);audioNodes.push(input,high,compressor,analyser);
      }
      musicGain=audio.createGain();musicGain.gain.value=0;musicGain.connect(destination);audioNodes.push(musicGain);
      if(musicLoaded){const element=new Audio(musicAudio.src);element.loop=true;musicAudio._take=element;const node=audio.createMediaElementSource(element);node.connect(musicGain);audioNodes.push(node);}
      else{[130.81,164.81,196].forEach((frequency,i)=>{const oscillator=audio.createOscillator(),gain=audio.createGain();oscillator.frequency.value=frequency;oscillator.type='sine';gain.gain.value=.24;oscillator.connect(gain).connect(musicGain);oscillator.start();audioNodes.push(oscillator,gain);});}
      canvasStream=canvas.captureStream(30);
      const tracks=[...canvasStream.getVideoTracks(),...destination.stream.getAudioTracks()];
      const type=['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/mp4'].find(t=>MediaRecorder.isTypeSupported(t));
      if(!type)throw Error('This browser cannot record the supported video formats. Use current Chrome or Edge.');
      const stream=new MediaStream(tracks);recorder=new MediaRecorder(stream,{mimeType:type,videoBitsPerSecond:10000000,audioBitsPerSecond:192000});
      chunks=[];totalBytes=0;
      recorder.ondataavailable=event=>{if(event.data.size){chunks.push(event.data);totalBytes+=event.data.size;if(totalBytes>config.max_upload_bytes*.9&&recorder.state!=='inactive'){say('Take reached the size limit. It has been stopped and preserved.',true);stop();}}};
      recorder.onerror=event=>{say(`Recording failed: ${event.error?.message||'unknown error'}. Keep any available original take.`,true);stop();};
      recorder.onstop=async()=>{
        takeBlob=new Blob(chunks,{type:recorder.mimeType});if(takeUrl)URL.revokeObjectURL(takeUrl);takeUrl=URL.createObjectURL(takeBlob);
        $('take').src=takeUrl;$('raw').href=takeUrl;$('raw').download=recorder.mimeType.includes('mp4')?'rel301m-original-take.mp4':'rel301m-original-take.webm';$('take-panel').hidden=false;$('download').hidden=true;
        active=false;paused=false;setScrolling(false);video.pause();voice._take?.pause();musicAudio._take?.pause();await cleanup();controls();
        say('Take preserved. Play it back, check your voice and picture, then export MP4. You can download the original take now.');
      };
      video.pause();if(video.currentTime>.01){await new Promise(resolve=>{video.addEventListener('seeked',resolve,{once:true});video.currentTime=0;});}
      $('picture').scrollIntoView({block:'nearest'});await video.play();await new Promise(requestAnimationFrame);
      elapsed=0;voice._take&&(voice._take.currentTime=0);resetCues();began=performance.now();active=true;paused=false;
      recorder.start(1000);if(voice._take)await voice._take.play();if(musicAudio._take)await musicAudio._take.play();setScrolling(true);controls();
      say(mode==='microphone'?'Recording your microphone and the video. Read the script; pause the take whenever needed.':mode==='file'?'Recording the video with your imported narration.':'Recording video without narration.');
    }catch(error){if(recorder?.state==='recording')recorder.stop();active=false;setScrolling(false);await cleanup();controls();say(`${error.name}: ${error.message}. Your existing take has not been deleted.`,true);}
  }
  function stop(){if(recorder&&recorder.state!=='inactive')recorder.stop();}
  async function pause(){
    if(!active)return;
    if(!paused){recorder.pause();video.pause();voice._take?.pause();musicAudio._take?.pause();paused=true;}
    else{recorder.resume();began=performance.now();paused=false;await video.play();if(voice._take)await voice._take.play();if(musicAudio._take)await musicAudio._take.play();}controls();
  }
  async function exportTake(){
    if(!takeBlob||pendingExport)return;pendingExport=true;controls();$('export-status').textContent='Uploading this take to the localhost exporter…';
    try{
      const response=await fetch('/api/export',{method:'POST',headers:{'X-Studio-Token':config.token,'Content-Type':takeBlob.type},body:takeBlob});
      const body=await response.json();if(!response.ok)throw Error(body.error||response.status);
      let result;
      do{await new Promise(resolve=>setTimeout(resolve,1200));const r=await fetch(`/api/jobs/${body.id}`);result=await r.json();$('export-status').textContent=result.status==='running'?'Encoding H.264 video and leveling the audio locally…':result.status;}while(['queued','running'].includes(result.status));
      if(result.status!=='complete')throw Error(result.error||'Export failed');
      $('download').href=result.url;$('download').hidden=false;$('export-status').textContent='MP4 ready. Download and watch it before submitting. Your original take remains available.';
    }catch(error){$('export-status').textContent=`Export failed: ${error.message}. Download the original take and retry; it has been kept.`;}
    finally{pendingExport=false;controls();}
  }
  function localFile(input,target){const file=input.files[0];if(!file)return;const url=URL.createObjectURL(file);urls.push(url);target.src=url;target.load?.();}
  $('record').onclick=record;$('stop').onclick=stop;$('pause').onclick=pause;$('export').onclick=exportTake;
  $('preview').onclick=()=>video.paused?video.play().catch(e=>say(e.message,true)):video.pause();
  $('rewind').onclick=()=>{video.pause();video.currentTime=0;resetCues();};
  $('position').oninput=()=>{video.currentTime=Number($('position').value);};
  video.onloadedmetadata=()=>{$('position').max=String(video.duration);controls();};
  video.onended=()=>{if(active)say('The demo has ended. Finish your sentence, then select Stop and keep take. The final frame is held.');};
  $('voice-file').onchange=()=>{localFile($('voice-file'),voice);$('mode').value='file';say('Narration loaded. Record a take to combine this audio with the video.');};
  $('video-file').onchange=()=>localFile($('video-file'),video);
  $('music-file').onchange=()=>{localFile($('music-file'),musicAudio);musicLoaded=true;$('music').checked=true;};
  $('logo-file').onchange=()=>{localFile($('logo-file'),$('logo'));$('show-logo').checked=true;};
  $('scroll').onclick=()=>setScrolling(!scrolling);
  $('script-top').onclick=resetCues;$('font').oninput=()=>{$('script').style.fontSize=`${$('font').value}px`;};
  $('speed').oninput=()=>{$('pace').textContent=`${$('speed').value} words / min`;};
  const wordCount=()=>{$('words').textContent=`${$('script').innerText.trim().split(/\s+/).filter(Boolean).length} words`;};
  $('script').oninput=()=>{cueWords=[];cuePosition=0;cueIndex=-1;wordCount();$('cue-progress').textContent='Ready to read';};
  $('save-script').onclick=()=>{const url=URL.createObjectURL(new Blob([$('script').innerText],{type:'text/plain'}));const a=document.createElement('a');a.href=url;a.download='REL301m-narration.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  window.addEventListener('beforeunload',e=>{if(active||takeBlob){e.preventDefault();e.returnValue='';}});
  async function boot(){
    if(location.protocol==='file:'){
      $('state').textContent='Open the website';$('local-help').hidden=false;
      say('Open START_RECORDING_STUDIO.bat, then use the localhost website. Opening this HTML file directly cannot load the demo or export video.',true);return;
    }
    try{config=await fetch('/api/config').then(r=>r.json());$('script').textContent=config.script;wordCount();video.src=config.media_url;controls();}catch(e){say(`Cannot load studio: ${e.message}`,true);}
  }
  requestAnimationFrame(draw);boot();
})();

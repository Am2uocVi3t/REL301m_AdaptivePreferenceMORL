/* Cosmetic renderer only. Every moving object follows engine coordinates. */
(() => {
  'use strict';
  const colors = {mint:'#70e4c4', violet:'#bca9ff', amber:'#ffd08b'};
  const polygon = (ctx, points, fill, stroke) => {
    if (!points.length) return;
    ctx.beginPath(); points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();
    if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.stroke();}
  };
  function circle(ctx,x,y,r,fill){ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle=fill;ctx.fill();}
  function background(ctx,w,h) {
    const sky=ctx.createLinearGradient(0,0,0,h);sky.addColorStop(0,'#101831');sky.addColorStop(0.7,'#172b43');sky.addColorStop(1,'#2b3450');ctx.fillStyle=sky;ctx.fillRect(0,0,w,h);
    for(let i=0;i<95;i++){const x=((i*173+41)%797)/800*w,y=((i*i*23+31)%307)/500*h;circle(ctx,x,y,i%7===0?1.5:.65,i%3===0?'#82a3c1':'#d6e5f6');}
    const glow=ctx.createRadialGradient(w*.82,h*.2,1,w*.82,h*.2,w*.13);glow.addColorStop(0,'#75b4bc55');glow.addColorStop(1,'#75b4bc00');ctx.fillStyle=glow;ctx.fillRect(0,0,w,h);
    circle(ctx,w*.82,h*.2,w*.043,'#8daab1');circle(ctx,w*.831,h*.19,w*.039,'#152039');
  }
  function lunar(ctx,s,p,w,h,accent,trail){
    background(ctx,w,h);const sx=w/20,sy=h/15,point=([x,y])=>[x*sx,h-y*sy];
    polygon(ctx,[[0,h*.78],[w*.13,h*.61],[w*.26,h*.78],[w*.43,h*.60],[w*.65,h*.75],[w*.85,h*.62],[w,h*.75],[w,h],[0,h]],'#23314d');
    const ground=s.terrain.map(point);const terrain=ctx.createLinearGradient(0,h*.6,0,h);terrain.addColorStop(0,'#6b7385');terrain.addColorStop(.1,'#3b475f');terrain.addColorStop(1,'#1c2a40');
    polygon(ctx,[[0,h],...ground,[w,h]],terrain,'#c9c6cd');ctx.lineWidth=1;
    for(let i=0;i<ground.length-1;i++){const [x,y]=ground[i];ctx.strokeStyle='#c8d0e522';ctx.beginPath();ctx.moveTo(x,y+13);ctx.lineTo(x+7,y+18);ctx.lineTo(x+22,y+14);ctx.stroke();}
    const [x1,y]=point([s.pad[0],s.pad[2]]),[x2]=point([s.pad[1],s.pad[2]]);
    ctx.fillStyle='#a4f5d4';ctx.fillRect(x1,y-3,x2-x1,4);ctx.strokeStyle='#70e4c435';ctx.setLineDash([4,6]);ctx.strokeRect(x1,y-18,x2-x1,18);ctx.setLineDash([]);
    for(const x of [x1,x2]){ctx.strokeStyle='#c4e0e4';ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x,y-26);ctx.stroke();polygon(ctx,[[x,y-26],[x+13,y-22],[x,y-17]],colors.mint);}
    if(trail.length>1){ctx.beginPath();trail.forEach((v,i)=>{const q=point(v);i?ctx.lineTo(...q):ctx.moveTo(...q);});ctx.strokeStyle=accent+'42';ctx.lineWidth=1.5;ctx.stroke();}
    for(const leg of s.legs){ctx.save();const [x,y]=point(leg.position);ctx.translate(x,y);ctx.rotate(-leg.angle);for(const fixture of leg.fixtures){ctx.lineWidth=2;polygon(ctx,fixture.map(([a,b])=>[a*sx,-b*sy]),'#8c9cad','#d9e7ea');}ctx.restore();}
    ctx.save();const [x,shipY]=point(s.lander.position);ctx.translate(x,shipY);ctx.rotate(-s.lander.angle);
    if(p.action===2&&p.steps>0){const flame=ctx.createLinearGradient(0,8,0,45);flame.addColorStop(0,'#fff3b6');flame.addColorStop(.4,'#62e1ee');flame.addColorStop(1,'#5c7fff00');polygon(ctx,[[-8,8],[-11,21],[0,40+(p.steps%5)*3],[11,21],[8,8]],flame);}
    if((p.action===1||p.action===3)&&p.steps>0){const sign=p.action===1?1:-1;polygon(ctx,[[sign*20,-8],[sign*37,-3],[sign*20,0]],'#80e8f4');}
    const hull=ctx.createLinearGradient(-20,-18,22,16);hull.addColorStop(0,'#e4edf4');hull.addColorStop(.45,'#a4b5ca');hull.addColorStop(1,'#506780');
    for(const fixture of s.lander.fixtures){ctx.lineWidth=1.8;polygon(ctx,fixture.map(([a,b])=>[a*sx,-b*sy]),hull,'#edf7ff');}
    polygon(ctx,[[-12,-15],[12,-15],[9,-5],[-9,-5]],'#143e58','#6ddcf2');ctx.strokeStyle='#c4d2de';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(-17,5);ctx.lineTo(17,5);ctx.stroke();
    circle(ctx,0,1,2.8,accent);ctx.fillStyle='#46627d';ctx.fillRect(-12,11,24,4);ctx.restore();
    ctx.fillStyle='#b9cce2';ctx.font='11px ui-monospace, monospace';ctx.fillText(`ALT ${Math.max(0,s.lander.position[1]-s.pad[2]).toFixed(1)} m`,18,26);
    ctx.fillStyle=s.contact.some(Boolean)?colors.mint:'#b9cce2';ctx.fillText(s.contact.some(Boolean)?'GROUND CONTACT':'FLIGHT',18,44);
  }
  function rock(ctx,x,y,size,color){
    ctx.save();ctx.translate(x,y);ctx.scale(size,size);const shade=ctx.createLinearGradient(-1,-1,1,1);shade.addColorStop(0,'#778390');shade.addColorStop(1,'#29394b');
    polygon(ctx,[[-.85,.3],[-.7,-.6],[-.15,-1],[.6,-.8],[1,-.1],[.65,.8],[-.4,.85]],shade,'#94a0a755');
    polygon(ctx,[[-.7,-.6],[-.15,-1],[.1,-.2],[-.2,.25]],'#9ba3aa55');polygon(ctx,[[0,-.2],[.45,-.5],[.7,0],[.28,.48]],color+'99',color);ctx.restore();
  }
  function minecart(ctx,s,p,w,h,accent,trail){
    const floor=ctx.createLinearGradient(0,0,w,h);floor.addColorStop(0,'#1b3036');floor.addColorStop(1,'#142131');ctx.fillStyle=floor;ctx.fillRect(0,0,w,h);
    const marginX=w*.10,marginY=h*.12,point=([x,y])=>[marginX+x*(w-2*marginX),marginY+y*(h-2*marginY)];
    ctx.strokeStyle='#66877c14';ctx.lineWidth=1;for(let x=marginX;x<w;x+=w*.08){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}for(let y=marginY;y<h;y+=h*.08){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
    for(let i=0;i<50;i++){const x=(i*113+43)%800/800*w,y=(i*i*43+11)%500/500*h;circle(ctx,x,y,i%3===0?2:1,'#71968622');}
    const [bx,by]=point([0,0]);ctx.save();ctx.translate(bx,by);ctx.strokeStyle='#70e4c439';ctx.lineWidth=2;ctx.beginPath();ctx.arc(0,0,w*.055,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#1e4b4d';ctx.fillRect(-24,-23,48,46);ctx.strokeStyle='#77c5be';ctx.strokeRect(-24,-23,48,46);ctx.fillStyle='#9be7d3';ctx.fillRect(-18,-29,36,5);ctx.fillStyle='#0f2c35';ctx.fillRect(-13,-12,26,24);ctx.restore();
    ctx.fillStyle='#b5ccce';ctx.font='10px ui-monospace, monospace';ctx.fillText('BASE / DELIVERY',bx-25,by+49);
    s.mines.forEach((v,i)=>{const [x,y]=point(v);ctx.strokeStyle='#7f9ab020';ctx.setLineDash([3,5]);ctx.beginPath();ctx.arc(x,y,38,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);rock(ctx,x,y,26,i%2?colors.violet:colors.mint);rock(ctx,x+24,y+15,11,colors.violet);ctx.fillStyle='#a4bacd';ctx.fillText(`M${i+1}`,x-7,y+47);});
    if(trail.length>1){ctx.strokeStyle=accent+'55';ctx.lineWidth=2;ctx.beginPath();trail.forEach((v,i)=>{const q=point(v);i?ctx.lineTo(...q):ctx.moveTo(...q);});ctx.stroke();}
    const [x,y]=point(s.position);ctx.save();ctx.translate(x,y);ctx.rotate(s.angle*Math.PI/180);ctx.fillStyle='#00000055';ctx.fillRect(-18,-9,40,29);
    for(const yy of [-19,13]){ctx.fillStyle='#0a111c';ctx.fillRect(-17,yy,33,7);ctx.fillStyle='#5c7180';for(let j=-12;j<15;j+=8)ctx.fillRect(j,yy+1,3,5);}
    const body=ctx.createLinearGradient(0,-16,0,18);body.addColorStop(0,'#aebec9');body.addColorStop(1,'#455969');polygon(ctx,[[-22,-14],[12,-14],[24,-8],[24,8],[12,15],[-22,15]],body,'#d0e0e7');ctx.fillStyle='#1a2c3a';ctx.fillRect(-17,-9,24,19);
    s.cargo.forEach((amount,i)=>{ctx.fillStyle=i?colors.violet:colors.mint;ctx.fillRect(-15+i*11,8-Math.min(15,amount/s.capacity*30),9,Math.min(15,amount/s.capacity*30));});ctx.fillStyle=accent;ctx.fillRect(10,-7,8,13);circle(ctx,24,-6,2,'#eaffca');circle(ctx,24,6,2,'#eaffca');
    if(p.action===0&&p.steps>0){ctx.strokeStyle=colors.amber;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(27,0);ctx.lineTo(34+(p.steps%3)*3,0);ctx.stroke();}ctx.restore();
    ctx.fillStyle='#bfd3db';ctx.font='11px ui-monospace, monospace';ctx.fillText(`CARGO ${s.cargo.map(v=>v.toFixed(2)).join(' / ')} • CAP ${s.capacity.toFixed(1)}`,18,h-21);
  }
  class SceneRenderer{
    constructor(canvas,accent){this.canvas=canvas;this.ctx=canvas.getContext('2d');this.accent=accent;this.trail=[];this.lastStep=-1;}
    reset(){this.trail=[];this.lastStep=-1;}
    draw(panel){if(!panel)return;const s=panel.scene;if(panel.steps!==this.lastStep){this.trail.push(s.kind==='lunar'?s.lander.position:s.position);this.trail=this.trail.slice(-150);this.lastStep=panel.steps;}const {width:w,height:h}=this.canvas;this.ctx.clearRect(0,0,w,h);(s.kind==='lunar'?lunar:minecart)(this.ctx,s,panel,w,h,this.accent,this.trail);}
  }
  window.SceneRenderer=SceneRenderer;
})();

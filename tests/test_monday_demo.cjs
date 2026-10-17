// DOM logic unit tests only. No browser, network, API or model process is used.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
class Element {
  constructor() { this.children=[];this.events={};this._text="";this.value="";this.classes=new Set();
    this.classList={toggle:(name,on)=>on?this.classes.add(name):this.classes.delete(name)}; }
  set textContent(value) {this._text=String(value);}
  get textContent() {return this._text+this.children.map(child=>child.textContent).join(" ");}
  appendChild(child) {this.children.push(child);}
  replaceChildren() {this.children=[];this._text="";}
  addEventListener(name, callback) {this.events[name]=callback;}
}
const directory=process.argv[2] || "outputs/monday-team/REL301m_Team_Review_2026-10-19";
const ids=["actual-seeds","weight","weight-label","formula","utility-rows","choice","scenario","scenario-result","scenario-details","scenario-seeds"];
const elements=Object.fromEntries(ids.map(id=>[`#${id}`,new Element()]));
elements["#weight"].value="50";elements["#scenario"].value="zero";
const context={window:{},document:{querySelector:id=>{assert.ok(elements[id],id);return elements[id];},createElement:()=>new Element()}};
vm.runInNewContext(fs.readFileSync(path.join(directory,"data.js"),"utf8"),context);
vm.runInNewContext(fs.readFileSync(path.join(directory,"app.js"),"utf8"),context);
let checks=0;function check(condition,message){assert.ok(condition,message);checks++;}
check(elements["#actual-seeds"].children.length===3,"Three real seeds");
check(elements["#actual-seeds"].children.every(row=>row.children[1].textContent==="0/160"&&row.children[2].textContent==="0/160"),"Real ore counts");
const actual=elements["#actual-seeds"].textContent;
for(const [weight,choice] of [["0","C"],["50","B"],["100","A"]]){
  elements["#weight"].value=weight;elements["#weight"].events.input();
  check(elements["#choice"].textContent.endsWith(`${choice}.`),`Synthetic preference chooses ${choice}`);
  check(elements["#choice"].textContent.includes("giả định"),"Synthetic disclosure retained");
}
for(const [scenario,pass] of [["all-pass",true],["one-fails",false],["zero",false]]){
  elements["#scenario"].value=scenario;elements["#scenario"].events.change();
  check(elements["#scenario-result"].classes.has("pass")===pass,`Gate ${scenario}`);
  check(elements["#actual-seeds"].textContent===actual,"Synthetic interactions cannot change actual evidence");
}
console.log(JSON.stringify({status:"PASS",assertions:checks,browser_rendering_verified:false,scope:"Offline DOM logic only"}));

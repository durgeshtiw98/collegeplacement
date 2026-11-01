// Dependency-free interaction tests in a local headless Chrome installation.
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawn } from 'node:child_process';

const chrome = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const temporary = mkdtempSync(join(tmpdir(), 'placement-browser-'));
const input = resolve(process.argv[2] || 'reports/supplied/dashboard.html');
const screenshots = resolve('docs/screenshots');
mkdirSync(screenshots, { recursive: true });
const smoke = `
<script>
(async()=>{
 const checks=[];
 function check(name,condition){checks.push({name,passed:Boolean(condition)});}
 function change(id,value){document.getElementById(id).value=value;document.getElementById(id).dispatchEvent(new Event('change'));}
 check('No dashboard script errors',window.qaErrors.length===0);
 check('Four KPI cards render',document.querySelectorAll('#kpis .card').length===4);
 check('Baseline follow-up reconciles with Python',current.followUp.length===(A.follow_up||A.kpis.follow_up).length);
 check('Document fits viewport',document.documentElement.scrollWidth<=window.innerWidth);
 const dept=document.getElementById('department').options[1].value;
 change('department',dept);
 check('Department filter updates performance rows',current.departments.length===1&&current.departments[0].department===dept);
 check('Department filter updates follow-up',current.followUp.every(s=>s.department===dept));
 document.getElementById('reset').click();
 check('Reset restores student cohort',current.departments.length===(A.departments||A.kpis.departments).length);
 document.querySelector('nav [data-view="recruitment"]').click();
 check('Recruitment navigation works',!document.querySelector('[data-section="recruitment"]').hidden&&document.querySelector('[data-section="overview"]').hidden);
 change('company',document.getElementById('company').options[1].value);
 const driveCompanyKey=A.metadata.mode==='supplied-workbook'?'Company_ID':'company_id';
 check('Company filters drive aggregates',current.drives.every(d=>d[driveCompanyKey]===document.getElementById('company').value));
 if(document.getElementById('drive').options.length>1){change('drive',document.getElementById('drive').options[1].value);check('Drive filter updates table',current.drives.length===1);}
 document.getElementById('reset').click();
 document.querySelector('nav [data-view="students"]').click();
 const sid=current.followUp[0]?.student_id||'missing';
 document.getElementById('student-search').value=sid;
 document.getElementById('student-search').dispatchEvent(new Event('input'));
 check('Student search narrows queue',document.querySelectorAll('#student-table tbody tr').length===1);
 let exported=null;URL.createObjectURL=blob=>{exported=blob;return 'blob:qa';};URL.revokeObjectURL=()=>{};HTMLAnchorElement.prototype.click=function(){};
 document.getElementById('export-students').click();
 const csv=await exported.text();
 check('Filtered CSV contains searched student',csv.includes(sid)&&csv.trim().split('\\r\\n').length===2);
 document.querySelector('nav [data-view="quality"]').click();
 check('Data quality navigation works',!document.querySelector('[data-section="quality"]').hidden&&document.querySelectorAll('#quality-table tbody tr').length>0);
 check('No errors after interactions',window.qaErrors.length===0);
 document.getElementById('reset').click();document.querySelector('nav [data-view="overview"]').click();
 const result=document.createElement('pre');result.id='browser-qa-result';result.hidden=true;result.textContent=JSON.stringify({checks,errors:window.qaErrors});document.body.append(result);
})();
</script>`;
async function connectBrowser(label,width,height,file) {
 const child=spawn(chrome,['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--remote-debugging-pipe','--user-data-dir='+join(temporary,label)],{stdio:['ignore','ignore','pipe','pipe','pipe']});
 const pending=new Map();let id=0,buffer='';
 child.stdio[4].on('data',chunk=>{buffer+=chunk.toString();let boundary;while((boundary=buffer.indexOf('\0'))>=0){const message=JSON.parse(buffer.slice(0,boundary));buffer=buffer.slice(boundary+1);if(message.id&&pending.has(message.id)){const {resolve,reject}=pending.get(message.id);pending.delete(message.id);message.error?reject(new Error(JSON.stringify(message.error))):resolve(message.result);}}});
 function send(method,params={},sessionId){return new Promise((resolve,reject)=>{const next=++id;pending.set(next,{resolve,reject});child.stdio[3].write(JSON.stringify({id:next,method,params,...(sessionId?{sessionId}:{})})+'\0');});}
 const timeout=setTimeout(()=>child.kill(),30000);
 try {
  const {targetId}=await send('Target.createTarget',{url:'about:blank'});
  const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});
  await send('Page.enable',{},sessionId);
  await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:label==='mobile'},sessionId);
  await send('Page.navigate',{url:'file://'+file},sessionId);
  let result;
  for(let attempt=0;attempt<100;attempt++){
   const evaluated=await send('Runtime.evaluate',{expression:"document.getElementById('browser-qa-result')?.textContent",returnByValue:true},sessionId);
   if(evaluated.result.value){result=JSON.parse(evaluated.result.value);break;}
   await new Promise(resolve=>setTimeout(resolve,50));
  }
  if(!result)throw new Error(label+': dashboard smoke script did not finish');
  const actual=await send('Runtime.evaluate',{expression:'window.innerWidth',returnByValue:true},sessionId);
  result.checks.push({name:'Requested viewport is enforced',passed:actual.result.value===width});
  console.log(label+': '+result.checks.filter(c=>c.passed).length+'/'+result.checks.length+' checks passed at '+actual.result.value+' px');
  if(result.errors.length||result.checks.some(c=>!c.passed))throw new Error(JSON.stringify(result));
  await send('Page.navigate',{url:'file://'+input},sessionId);
  await new Promise(resolve=>setTimeout(resolve,200));
  const screenshot=await send('Page.captureScreenshot',{format:'png'},sessionId);
  writeFileSync(join(screenshots,'dashboard-'+label+'.png'),Buffer.from(screenshot.data,'base64'));
 } finally {clearTimeout(timeout);child.kill();await new Promise(resolve=>child.once('exit',resolve));}
}
try {
 const html=readFileSync(input,'utf8').replace('<head>','<head><script>window.qaErrors=[];window.addEventListener("error",e=>window.qaErrors.push(e.message));</script>');
 const file=join(temporary,'dashboard.html');writeFileSync(file,html+smoke);
 await connectBrowser('desktop',1440,1100,file);
 await connectBrowser('mobile',390,844,file);
} finally {rmSync(temporary,{recursive:true,force:true});}

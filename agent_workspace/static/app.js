'use strict';
const $ = id => document.getElementById(id);
let session, project = '', state, currentRun, busy = false;
function node(tag, text, className) { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (className) el.className = className; return el; }
function button(label, action, className='subtle') { const el=node('button',label,className); el.type='button'; el.addEventListener('click',action); return el; }
function notice(message='', error=false) { $('notice').textContent=message; $('notice').classList.toggle('error',error); }
async function api(path, data) {
  const options=data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-Agent-Token':session.token},body:JSON.stringify(data)};
  const response=await fetch(path,options);
  const result=await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
  return result;
}
async function work(action, label='Working…') {
  if (busy) return;
  busy=true; notice(label);
  const controls=[...document.querySelectorAll('button,input,select,textarea')].map(el=>[el,el.disabled]);
  controls.forEach(([el])=>el.disabled=true);
  try { await action(); }
  catch (error) { notice(error.message,true); }
  finally { controls.forEach(([el,disabled])=>el.disabled=disabled); busy=false; }
}
function showTab(name, focus=false) {
  for (const tab of ['ask','tasks','history']) { const active=tab===name; $(tab+'-tab').setAttribute('aria-selected',String(active)); $(tab+'-tab').tabIndex=active?0:-1; $(tab+'-panel').hidden=!active; }
  if (focus) $(name+'-tab').focus();
}
function query(path,id) { const params=new URLSearchParams({project}); if(id) params.set('id',id); return `${path}?${params}`; }
async function refresh(nextProject=project) {
  state=await api('/api/state'+(nextProject?'?'+new URLSearchParams({project:nextProject}):''));
  if (!nextProject && state.projects.length) return refresh(state.projects[0].id);
  project=nextProject;
  $('project').replaceChildren(...state.projects.map(p=>{const option=node('option',p.name);option.value=p.id;return option;}));
  $('project').value=project;
  renderSources(); renderTasks(); renderHistory();
}
function resetReport() { currentRun=null; $('report').hidden=true; $('empty').hidden=false; }
function renderSources() {
  $('source-count').textContent=state.documents.length;
  $('sources').replaceChildren();
  if(!state.documents.length) $('sources').append(node('li','No sources imported yet.','muted-empty'));
  for(const doc of state.documents) {
    const li=node('li'); const open=button(doc.name,()=>work(async()=>{
      const source=await api(query('/api/document',doc.id));
      $('document-name').textContent=source.name; $('document-meta').textContent=`Current source · SHA-256 ${source.digest}`;
      $('document-content').textContent=source.content.split('\n').map((line,index)=>`${index+1}  ${line}`).join('\n');
      $('document-dialog').showModal(); notice();
    }),'source-name');
    open.append(node('span',`${doc.characters.toLocaleString()} characters`,'source-meta'));
    const remove=button('×',()=>{if(confirm(`Delete source “${doc.name}”? Existing report snapshots will remain until you delete report history.`)) work(async()=>{await api('/api/delete-document',{project,id:doc.id});await refresh();notice('Source deleted. Existing reports retain their evidence snapshots.');});},'remove');
    remove.setAttribute('aria-label',`Delete source ${doc.name}`); li.append(open,remove); $('sources').append(li);
  }
}
function renderTasks() {
  for(const status of ['todo','doing','done']) {
    const tasks=state.tasks.filter(task=>task.status===status); const list=$(status); list.replaceChildren(); $(status+'-count').textContent=tasks.length;
    if(!tasks.length) list.append(node('li','No tasks here.','muted-empty'));
    for(const task of tasks) {
      const li=node('li'); li.append(node('p',task.title)); const controls=node('div',undefined,'task-controls'); const select=node('select');
      select.setAttribute('aria-label',`Status for ${task.title}`);
      for(const [value,label] of [['todo','To do'],['doing','In progress'],['done','Done']]) {const option=node('option',label);option.value=value;select.append(option);}
      select.value=task.status; select.addEventListener('change',()=>work(async()=>{await api('/api/task-status',{project,id:task.id,status:select.value});await refresh();notice('Task status saved.');}));
      const remove=button('×',()=>{if(confirm(`Delete task “${task.title}”?`))work(async()=>{await api('/api/delete-task',{project,id:task.id});await refresh();notice('Task deleted.');});});
      remove.setAttribute('aria-label',`Delete task ${task.title}`); controls.append(select,remove);li.append(controls);list.append(li);
    }
  }
}
function renderHistory() {
  $('history').replaceChildren();
  if(!state.runs.length) $('history').append(node('li','Ask a question to save your first report.','muted-empty'));
  for(const run of state.runs) {const li=node('li');li.append(button(run.question,()=>work(async()=>{const report=await api(query('/api/run',run.id));renderReport(report);showTab('ask');notice('Opened saved report with its original source snapshots.');})));const date=node('time',new Date(run.created).toLocaleString());date.dateTime=run.created;li.append(date);$('history').append(li);}
}
function renderReport(run) {
  currentRun=run; const result=run.result; $('empty').hidden=true;$('report').hidden=false;
  $('report-title').textContent=result.question;
  $('report-mode').textContent=result.mode==='evidence'?'Evidence · no AI call':`${result.mode} · AI synthesis`;
  $('report-note').textContent=result.mode==='evidence'?'These are matching source excerpts, not an AI-generated answer. Search matches keywords and may miss paraphrases.':'Every claim references a retrieved source. References are structurally checked; review the excerpts to judge whether each claim is actually supported.';
  $('warnings').replaceChildren(...result.warnings.map(message=>node('p',message+' Returned source excerpts instead.')));
  $('claims').replaceChildren();
  if(!result.claims.length)$('claims').append(node('p','The imported evidence does not answer this question. Try more specific project terms or import another source.'));
  for(const claim of result.claims) {const p=node('p',claim.text);for(const ref of claim.sources){p.append(button(`[${ref}]`,()=>{const target=$('evidence-'+ref);if(target){target.open=true;target.scrollIntoView({block:'nearest'});target.querySelector('summary').focus();}},'citation'));}$('claims').append(p);}
  $('steps-wrap').hidden=!result.next_steps.length; $('steps').replaceChildren();
  for(const title of result.next_steps){const li=node('li');const add=button('Add task',()=>work(async()=>{await api('/api/tasks',{project,title});await refresh();add.replaceWith(node('span','Added','fine-print'));notice('Suggestion added to To do.');}));li.append(node('span',title),add);$('steps').append(li);}
  $('evidence-count').textContent=result.sources.length;$('evidence').replaceChildren();
  for(const source of result.sources){const details=node('details',undefined,'evidence-card');details.id='evidence-'+source.source_id;const summary=node('summary',`[${source.source_id}] ${source.name} · lines ${source.start_line}–${source.end_line}`);const pre=node('pre',source.body.split('\n').map((line,index)=>`${source.start_line+index}  ${line}`).join('\n'));details.append(summary,pre,node('p','Snapshot SHA-256: '+source.digest,'fine-print'));$('evidence').append(details);}
  $('trace').replaceChildren(...result.trace.map(event=>node('li',`${event.elapsed_ms} ms · ${event.stage}: ${event.detail}`)));
  $('export-md').href=query('/api/export',run.id);$('export-json').href=query('/api/export',run.id)+'&format=json';
}
function updateMode() {
  const mode=$('provider').value;$('cloud-consent').hidden=mode!=='openrouter';$('allow-cloud').checked=false;$('allow-cloud').required=mode==='openrouter';
  $('mode-help').textContent=mode==='evidence'?'Evidence mode returns matching excerpts. It works without an API key or a model.':mode==='ollama'?'Uses your configured Ollama model on 127.0.0.1:11434. Model errors fall back visibly to evidence.':'Sends this question and selected excerpts to your configured OpenRouter model. Provider charges and data policies apply.';
}
for(const [index,name] of ['ask','tasks','history'].entries()){
  $(name+'-tab').addEventListener('click',()=>showTab(name));
  $(name+'-tab').addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?2:(index+(event.key==='ArrowRight'?1:2))%3;showTab(['ask','tasks','history'][next],true);}});
}
$('project').addEventListener('change',()=>work(async()=>{resetReport();await refresh($('project').value);notice();}));
$('project-form').addEventListener('submit',event=>{event.preventDefault();work(async()=>{const created=await api('/api/projects',{name:$('project-name').value});$('project-name').value='';resetReport();await refresh(created.id);notice('Project created. Import its notes to begin.');});});
$('sample').addEventListener('click',()=>work(async()=>{const sample=await api('/api/sample',{});resetReport();await refresh(sample.id);$('question').value='How often does the firmware sample soil moisture?';$('provider').value='evidence';updateMode();showTab('ask');notice('Fictional sample loaded. Click “Find an answer” to inspect its source evidence.');}));
$('files').addEventListener('change',()=>work(async()=>{
  if(!project)throw new Error('Create a project first.');
  const files=[...$('files').files];if(files.length>50)throw new Error('Import at most 50 files at once.');
  let changed=0,unchanged=0;const failures=[];
  for(const file of files){try{if(file.size>1000000)throw new Error('exceeds 1 MB');const content=new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer());const result=await api('/api/documents',{project,name:file.name,content});result.changed?changed++:unchanged++;}catch(error){failures.push(`${file.name}: ${error.message}`);}}
  $('files').value='';await refresh();notice(`${changed} imported or updated, ${unchanged} unchanged.${failures.length?' Skipped: '+failures.join('; '):''}`,failures.length>0);
},'Importing and indexing selected files…'));
$('ask-form').addEventListener('submit',event=>{event.preventDefault();work(async()=>{if(!project)throw new Error('Create a project first.');const run=await api('/api/ask',{project,question:$('question').value,provider:$('provider').value,allow_cloud:$('allow-cloud').checked});renderReport(run);$('allow-cloud').checked=false;await refresh();notice('Report saved with its source evidence.');},'Searching project evidence and waiting for the selected model, if enabled…');});
$('task-form').addEventListener('submit',event=>{event.preventDefault();work(async()=>{await api('/api/tasks',{project,title:$('task-title').value});$('task-title').value='';await refresh();notice('Task saved in To do.');});});
$('clear-history').addEventListener('click',()=>{if(confirm('Permanently delete every saved report and evidence snapshot in this project? Sources and tasks will remain.'))work(async()=>{await api('/api/clear-runs',{project});resetReport();await refresh();notice('Report history deleted.');});});
$('provider').addEventListener('change',updateMode);$('close-dialog').addEventListener('click',()=>$('document-dialog').close());
async function boot(){session=await api('/api/session');for(const [name,config] of Object.entries(session.providers)){const option=node('option',config.label+(config.available?'':' · not configured'));option.value=name;option.disabled=!config.available;$('provider').append(option);}updateMode();await refresh();notice();}
boot().catch(error=>notice('Could not connect to the local workspace: '+error.message,true));

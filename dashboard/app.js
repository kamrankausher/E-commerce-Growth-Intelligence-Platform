const API='';const charts={};let apiOnline=false;
const C={bg:'#1a1a26',border:'rgba(255,255,255,0.06)',text:'#e2e8f0',text2:'#94a3b8',
primary:'#6366f1',secondary:'#06b6d4',success:'#10b981',warning:'#f59e0b',danger:'#ef4444',
grad1:'rgba(99,102,241,0.5)',grad2:'rgba(6,182,212,0.5)'};

Chart.defaults.color=C.text2;Chart.defaults.borderColor=C.border;
Chart.defaults.font.family="'Inter',sans-serif";Chart.defaults.font.size=11;
Chart.defaults.plugins.legend.labels.usePointStyle=true;
Chart.defaults.plugins.legend.labels.pointStyleWidth=8;

// Nav
document.querySelectorAll('.nav-item').forEach(el=>{
el.addEventListener('click',()=>{
document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
el.classList.add('active');
document.getElementById('page-'+el.dataset.page).classList.add('active');
loadPage(el.dataset.page);
});});

const loaded={};
function loadPage(p){if(loaded[p])return;loaded[p]=true;
if(p==='overview')loadOverview();
else if(p==='analytics')loadAnalytics();
else if(p==='ab')loadAB();
else if(p==='churn')loadChurn();
else if(p==='ml')loadML();}

async function api(path){
const r=await fetch(API+path);
if(!r.ok)throw new Error(r.status);
return r.json();}

function animateNum(el,target,prefix='',suffix='',dec=0){
let start=0;const dur=1500;const t0=performance.now();
function step(t){const p=Math.min((t-t0)/dur,1);
const v=start+(target-start)*p;
el.textContent=prefix+(dec?v.toFixed(dec):Math.round(v).toLocaleString())+suffix;
if(p<1)requestAnimationFrame(step);}
requestAnimationFrame(step);}

function makeGrad(ctx,c1,c2){const g=ctx.createLinearGradient(0,0,0,300);g.addColorStop(0,c1);g.addColorStop(1,'transparent');return g;}

// Health check
async function checkAPI(){try{await api('/health');apiOnline=true;
document.getElementById('statusDot').classList.add('online');
document.getElementById('statusText').textContent='API Connected';
}catch(e){apiOnline=false;
document.getElementById('statusText').textContent='API Offline';}}

function showError(id,msg){
document.getElementById(id).innerHTML='<div class="error-state"><h3>⚠️ Connection Error</h3><p>'+msg+'</p><code>python -m uvicorn src.api.app:app --port 8000</code></div>';}

function exportChart(id){if(!charts[id])return;
const a=document.createElement('a');a.href=charts[id].toBase64Image();
a.download=id+'.png';a.click();}

// PAGE 1
async function loadOverview(){
try{const d=await api('/api/kpis');
animateNum(document.getElementById('v-rev'),d.total_revenue,'R$ ');
animateNum(document.getElementById('v-ord'),d.total_orders);
animateNum(document.getElementById('v-cust'),d.unique_customers);
animateNum(document.getElementById('v-aov'),d.avg_order_value,'R$ ','',2);
animateNum(document.getElementById('v-review'),d.avg_review_score,'','/ 5',1);
animateNum(document.getElementById('v-late'),d.late_delivery_pct,'','%',1);
}catch(e){document.getElementById('v-rev').textContent='ERR';}

try{const d=await api('/api/revenue_trend');
const ctx=document.getElementById('chartRevTrend').getContext('2d');
charts['chartRevTrend']=new Chart(ctx,{type:'line',data:{
labels:d.map(r=>r.month),datasets:[{label:'Revenue (R$)',data:d.map(r=>r.revenue),
borderColor:C.primary,backgroundColor:makeGrad(ctx,C.grad1,'transparent'),
fill:true,tension:.4,pointRadius:2,pointHoverRadius:5,borderWidth:2}]},
options:{responsive:true,plugins:{legend:{display:false}},
scales:{y:{grid:{color:C.border},ticks:{callback:v=>'R$'+v.toLocaleString()}},
x:{grid:{display:false},ticks:{maxTicksLimit:8}}}}});}catch(e){}

try{const d=await api('/api/top_states');
const ctx=document.getElementById('chartStates').getContext('2d');
const colors=d.map((_,i)=>`hsl(${230+i*12},70%,${60+i*2}%)`);
charts['chartStates']=new Chart(ctx,{type:'bar',data:{
labels:d.map(r=>r.state),datasets:[{label:'Revenue',data:d.map(r=>r.revenue),
backgroundColor:colors,borderRadius:6,borderSkipped:false}]},
options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},
scales:{x:{grid:{color:C.border},ticks:{callback:v=>'R$'+v.toLocaleString()}},
y:{grid:{display:false}}}}});}catch(e){}

try{const d=await api('/api/categories');
const ctx=document.getElementById('chartCats').getContext('2d');
const colors=d.map((_,i)=>`hsl(${170+i*18},60%,${55+i*2}%)`);
charts['chartCats']=new Chart(ctx,{type:'bar',data:{
labels:d.map(r=>r.category),datasets:[{label:'Revenue',data:d.map(r=>r.revenue),
backgroundColor:colors,borderRadius:6,borderSkipped:false}]},
options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},
scales:{x:{grid:{color:C.border}},y:{grid:{display:false}}}}});}catch(e){}

try{const d=await api('/api/payments');
const ctx=document.getElementById('chartPay').getContext('2d');
const colors=[C.primary,C.secondary,C.success,C.warning,C.danger];
charts['chartPay']=new Chart(ctx,{type:'doughnut',data:{
labels:d.map(r=>r.type),datasets:[{data:d.map(r=>r.value),backgroundColor:colors,
borderWidth:0,hoverOffset:8}]},
options:{responsive:true,cutout:'65%',plugins:{legend:{position:'right'}}}});}catch(e){}

try{const d=await api('/api/orders_table');
const tb=document.getElementById('ordersBody');tb.innerHTML='';
d.forEach(r=>{const sc=r.status.toLowerCase();
const bc='badge badge-'+(sc==='delivered'?'delivered':sc==='shipped'?'shipped':
sc==='canceled'?'canceled':sc==='processing'?'processing':'unavailable');
tb.innerHTML+='<tr><td>'+r.order_id+'</td><td>'+r.date+'</td><td>'+r.state+
'</td><td><span class="'+bc+'">'+r.status+'</span></td><td>R$ '+r.value.toLocaleString()+'</td></tr>';});}catch(e){}}

// PAGE 2
async function loadAnalytics(){
try{const d=await api('/api/cohort');
const cont=document.getElementById('cohortContainer');
const cohorts=[...new Set(d.map(r=>r.cohort_month))].sort();
const maxOff=Math.max(...d.map(r=>r.month_offset));
const base={};d.forEach(r=>{if(r.month_offset===0)base[r.cohort_month]=r.customers;});
let html='<div class="heatmap-grid" style="grid-template-columns:100px repeat('+(maxOff+1)+',1fr)">';
html+='<div class="heatmap-label">Cohort</div>';
for(let i=0;i<=maxOff;i++)html+='<div class="heatmap-label">M'+i+'</div>';
cohorts.forEach(c=>{html+='<div class="heatmap-label" style="text-align:left;font-weight:500;color:'+C.text+'">'+c.substring(0,7)+'</div>';
for(let m=0;m<=maxOff;m++){const rec=d.find(r=>r.cohort_month===c&&r.month_offset===m);
if(rec&&base[c]){const pct=Math.round(rec.customers/base[c]*100);
const op=Math.max(0.1,pct/100);
html+='<div class="heatmap-cell" style="background:rgba(99,102,241,'+op+');color:'+(pct>50?'#fff':C.text2)+'">'+pct+'%</div>';
}else html+='<div class="heatmap-cell" style="color:'+C.text3+'">—</div>';}});
html+='</div>';cont.innerHTML=html;}catch(e){document.getElementById('cohortContainer').innerHTML='<div class="error-state"><p>Could not load cohort data</p></div>';}

try{const d=await api('/api/rfm');
const ctx=document.getElementById('chartRFM').getContext('2d');
const colors={Champions:C.success,Loyal:'#22d3ee','New Customers':C.primary,'At Risk':C.warning,Lost:C.danger,'Needs Attention':'#a78bfa'};
charts['chartRFM']=new Chart(ctx,{type:'doughnut',data:{
labels:d.map(r=>r.segment),datasets:[{data:d.map(r=>r.count),
backgroundColor:d.map(r=>colors[r.segment]||C.text3),borderWidth:0,hoverOffset:8}]},
options:{responsive:true,cutout:'60%',plugins:{legend:{position:'right'}}}});}catch(e){}

try{const d=await api('/api/sellers');
const ctx=document.getElementById('chartSellers').getContext('2d');
charts['chartSellers']=new Chart(ctx,{type:'scatter',data:{datasets:[{
label:'Sellers',data:d.map(r=>({x:r.orders,y:r.revenue,r:Math.max(3,r.avg_review*2)})),
backgroundColor:d.map(r=>r.late_rate>0.3?C.danger+'80':C.primary+'80'),
borderColor:d.map(r=>r.late_rate>0.3?C.danger:C.primary),borderWidth:1}]},
options:{responsive:true,plugins:{legend:{display:false},tooltip:{callbacks:{
label:function(c){const s=d[c.dataIndex];return 'Orders:'+s.orders+' Rev:R$'+s.revenue+' Rating:'+s.avg_review;}}}},
scales:{x:{title:{display:true,text:'Orders',color:C.text3},grid:{color:C.border}},
y:{title:{display:true,text:'Revenue (R$)',color:C.text3},grid:{color:C.border}}}}});}catch(e){}

try{const d=await api('/api/cumulative_revenue');
const ctx=document.getElementById('chartCumRev').getContext('2d');
charts['chartCumRev']=new Chart(ctx,{type:'line',data:{
labels:d.map(r=>r.month),datasets:[{label:'Cumulative Revenue',data:d.map(r=>r.cumulative),
borderColor:C.secondary,backgroundColor:makeGrad(ctx,C.grad2,'transparent'),
fill:true,tension:.3,pointRadius:0,borderWidth:2}]},
options:{responsive:true,plugins:{legend:{display:false}},
scales:{y:{grid:{color:C.border},ticks:{callback:v=>'R$'+(v/1e6).toFixed(1)+'M'}},
x:{grid:{display:false},ticks:{maxTicksLimit:8}}}}});}catch(e){}}

// PAGE 3
async function loadAB(){
try{const d=await api('/api/ab_results');
const cont=document.getElementById('abContainer');cont.innerHTML='';
d.forEach(exp=>{
const sig=exp.is_significant;
const ciMin=Math.min(exp.ci_lower,0);const ciMax=Math.max(exp.ci_upper,0);
const range=ciMax-ciMin||1;
const barL=((exp.ci_lower-ciMin)/range*100);
const barW=((exp.ci_upper-exp.ci_lower)/range*100);
const zeroPos=((0-ciMin)/range*100);
const dotPos=((exp.absolute_lift-ciMin)/range*100);
const testDesc=exp.test_type==='chi_square'?
'Chi-Square test for proportions (H₀: p₁ = p₂). The test statistic χ²='+exp.test_statistic+' with p='+exp.p_value.toFixed(6)+'.':
'Welch\'s t-test for means (H₀: μ₁ = μ₂). The test statistic t='+exp.test_statistic+' with p='+exp.p_value.toFixed(6)+'.';
const verdict=sig?'We reject H₀ — the treatment effect is statistically significant at α=0.05. The '+exp.relative_lift_pct+'% lift is real.':
'We fail to reject H₀ — insufficient evidence at α=0.05. The observed lift of '+exp.relative_lift_pct+'% may be due to chance.';

cont.innerHTML+=`<div class="experiment-card">
<h4>${exp.experiment_name} <span class="badge ${sig?'badge-sig':'badge-nosig'}">${sig?'✓ Significant':'✗ Not Significant'}</span></h4>
<div class="exp-stats">
<div class="exp-stat"><div class="label">Control (n=${exp.control_size.toLocaleString()})</div><div class="val">${typeof exp.control_mean==='number'&&exp.control_mean<1?
(exp.control_mean*100).toFixed(2)+'%':exp.control_mean.toLocaleString()}</div></div>
<div class="exp-stat"><div class="label">Treatment (n=${exp.treatment_size.toLocaleString()})</div><div class="val" style="color:${sig?C.success:C.text}">${typeof exp.treatment_mean==='number'&&exp.treatment_mean<1?
(exp.treatment_mean*100).toFixed(2)+'%':exp.treatment_mean.toLocaleString()}</div></div>
<div class="exp-stat"><div class="label">Relative Lift</div><div class="val" style="color:${exp.relative_lift_pct>0?C.success:C.danger}">${exp.relative_lift_pct>0?'+':''}${exp.relative_lift_pct}%</div></div>
<div class="exp-stat"><div class="label">P-Value</div><div class="val" style="color:${sig?C.success:C.warning}">${exp.p_value<0.001?'<0.001':exp.p_value.toFixed(4)}</div></div>
<div class="exp-stat"><div class="label">Power</div><div class="val">${(exp.statistical_power*100).toFixed(1)}%</div></div>
<div class="exp-stat"><div class="label">MDE</div><div class="val">${typeof exp.mde==='number'&&exp.mde<1?(exp.mde*100).toFixed(2)+'%':exp.mde}</div></div>
</div>
<p style="font-size:11px;color:${C.text3};margin-bottom:8px">95% Confidence Interval for the difference:</p>
<div class="ci-viz"><div class="ci-bar" style="left:${barL}%;width:${barW}%"></div>
<div class="ci-zero" style="left:${zeroPos}%"></div>
<div class="ci-dot" style="left:${dotPos}%"></div></div>
<div class="exp-explanation"><strong>Interpretation:</strong> ${testDesc} ${verdict}</div>
</div>`;});

// Power calculator
cont.innerHTML+=`<div class="power-calc"><h4>🔋 Sample Size Calculator</h4>
<p class="subtitle" style="margin-bottom:16px">Estimate required sample size per group to detect a given effect at 80% power.</p>
<div class="slider-row"><label>Baseline Rate</label><input type="range" id="pc-base" min="1" max="50" value="5" oninput="calcPower()"><span class="slider-val" id="pcv-base">5%</span></div>
<div class="slider-row"><label>Min Detectable Lift</label><input type="range" id="pc-lift" min="5" max="100" value="20" oninput="calcPower()"><span class="slider-val" id="pcv-lift">20%</span></div>
<div class="power-result" id="powerResult">—<span>samples per group needed</span></div></div>`;
calcPower();
}catch(e){showError('abContainer','Could not load A/B results');}}

function calcPower(){
const base=parseInt(document.getElementById('pc-base').value)/100;
const lift=parseInt(document.getElementById('pc-lift').value)/100;
document.getElementById('pcv-base').textContent=Math.round(base*100)+'%';
document.getElementById('pcv-lift').textContent=Math.round(lift*100)+'%';
const p2=base*(1+lift);const pp=(base+p2)/2;
const za=1.96;const zb=0.84;
const n=Math.ceil(((za*Math.sqrt(2*pp*(1-pp))+zb*Math.sqrt(base*(1-base)+p2*(1-p2)))**2)/((p2-base)**2));
document.getElementById('powerResult').innerHTML=n.toLocaleString()+'<span>samples per group (α=0.05, β=0.80)</span>';}

// PAGE 4
const sliderDefs=[
{id:'frequency',label:'Purchase Frequency',min:1,max:20,val:3,step:1,icon:'🛒'},
{id:'monetary',label:'Total Spend (R$)',min:10,max:5000,val:350,step:10,icon:'💰'},
{id:'avg_order_value',label:'Avg Order Value',min:10,max:500,val:125,step:5,icon:'📦'},
{id:'avg_installments',label:'Avg Installments',min:1,max:12,val:3,step:1,icon:'💳'},
{id:'payment_type_count',label:'Payment Methods',min:1,max:5,val:1,step:1,icon:'🔄'},
{id:'avg_review_score',label:'Avg Review Score',min:1,max:5,val:4,step:0.1,icon:'⭐'},
{id:'review_count',label:'Reviews Given',min:0,max:20,val:2,step:1,icon:'📝'},
{id:'tenure_days',label:'Tenure (days)',min:0,max:730,val:180,step:1,icon:'📅'},
{id:'avg_days_between_orders',label:'Avg Days Between Orders',min:1,max:365,val:60,step:1,icon:'⏱️'},
{id:'state_encoded',label:'State Code',min:0,max:26,val:12,step:1,icon:'🗺️'}];

async function loadChurn(){
try{const d=await api('/api/churn/model_info');
const m=d.metrics;const cont=document.getElementById('churnMetrics');
const mets=[{icon:'🎯',label:'Accuracy',val:m.accuracy,tip:'Overall correctness'},
{icon:'🔍',label:'Precision',val:m.precision,tip:'True positive rate'},
{icon:'📡',label:'Recall',val:m.recall,tip:'Churner detection rate'},
{icon:'⚖️',label:'F1 Score',val:m.f1,tip:'Precision-Recall balance'},
{icon:'📊',label:'ROC-AUC',val:m.roc_auc,tip:'Ranking quality'}];
cont.innerHTML='';
mets.forEach(mt=>{cont.innerHTML+=`<div class="kpi-card"><div class="kpi-icon">${mt.icon}</div><div class="kpi-label">${mt.label}</div><div class="kpi-value" style="color:${mt.val>=0.8?C.success:mt.val>=0.6?C.warning:C.danger}">${(mt.val*100).toFixed(1)}%</div><div class="kpi-sub">${mt.tip}</div></div>`;});

// Feature importance chart
const fi=d.feature_importance;
const sorted=Object.entries(fi).sort((a,b)=>b[1]-a[1]);
const ctx=document.getElementById('chartFI').getContext('2d');
charts['chartFI']=new Chart(ctx,{type:'bar',data:{
labels:sorted.map(s=>s[0].replace(/_/g,' ')),
datasets:[{data:sorted.map(s=>s[1]),
backgroundColor:sorted.map((_,i)=>`hsl(${240-i*15},70%,${60+i}%)`),
borderRadius:4,borderSkipped:false}]},
options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},
scales:{x:{grid:{color:C.border}},y:{grid:{display:false}}}}});

}catch(e){document.getElementById('churnMetrics').innerHTML='<div class="error-state" style="grid-column:1/-1"><h3>Model not found</h3><p>Run python setup.py first</p></div>';}

try{const d=await api('/api/churn/distribution');
const ctx=document.getElementById('chartDist').getContext('2d');
const colors=d.map(r=>r.tier==='LOW'?C.success:r.tier==='MEDIUM'?C.warning:C.danger);
charts['chartDist']=new Chart(ctx,{type:'bar',data:{
labels:d.map(r=>r.range),datasets:[{label:'Customers',data:d.map(r=>r.count),
backgroundColor:colors,borderRadius:4,borderSkipped:false}]},
options:{responsive:true,plugins:{legend:{display:false}},
scales:{y:{grid:{color:C.border}},x:{grid:{display:false}}}}});}catch(e){}

try{const d=await api('/api/churn/customers');
const tb=document.getElementById('riskBody');tb.innerHTML='';
d.forEach(r=>{
tb.innerHTML+=`<tr><td>${r.customer_rank}</td><td><div class="prob-bar" style="width:80px;display:inline-block;vertical-align:middle;margin-right:6px"><div class="prob-bar-fill" style="width:${r.churn_probability*100}%;background:${r.risk_level==='HIGH'?C.danger:C.warning}"></div></div>${(r.churn_probability*100).toFixed(1)}%</td><td><span class="badge ${r.risk_level==='HIGH'?'badge-canceled':r.risk_level==='MEDIUM'?'badge-processing':'badge-delivered'}">${r.risk_level}</span></td><td>${r.frequency}</td><td>R$ ${r.monetary.toLocaleString()}</td><td>${r.avg_days_between_orders}</td></tr>`;});}catch(e){}

// Build premium prediction feature cards
const sp=document.getElementById('predictSliders');sp.innerHTML='';
sliderDefs.forEach(s=>{
sp.innerHTML+=`<div class="feature-card"><div class="feature-card-header"><span class="feature-card-name"><span class="f-icon">${s.icon}</span>${s.label}</span><span class="feature-card-val" id="sv-${s.id}">${s.val}</span></div><input type="range" id="sl-${s.id}" min="${s.min}" max="${s.max}" value="${s.val}" step="${s.step}" oninput="document.getElementById('sv-${s.id}').textContent=this.value"></div>`;});}

async function doPrediction(){
const btn=document.getElementById('predictBtn');
btn.disabled=true;btn.innerHTML='<span class="btn-spark">⏳</span> Predicting...';
const body={};
sliderDefs.forEach(s=>{body[s.id]=parseFloat(document.getElementById('sl-'+s.id).value);});
try{
const r=await fetch(API+'/api/churn/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
const d=await r.json();
const pct=(d.churn_probability*100).toFixed(1);
const maxDash=534; // circumference of gauge ring
const arc=document.getElementById('gaugeArc');
arc.setAttribute('stroke-dasharray',`${maxDash*d.churn_probability} ${maxDash}`);
const gv=document.getElementById('gaugeVal');
gv.textContent=pct+'%';
gv.style.color=d.risk_level==='HIGH'?C.danger:d.risk_level==='MEDIUM'?C.warning:C.success;
const rb=document.getElementById('riskBadge');
rb.textContent=d.risk_level+' RISK';
rb.className='gauge-risk-badge '+d.risk_level;
}catch(e){document.getElementById('gaugeVal').textContent='ERR';}
btn.disabled=false;btn.innerHTML='<span class="btn-spark">⚡</span> Predict Churn';}

// PAGE 5
async function loadML(){
try{const d=await api('/api/optuna_trials');
const ctx=document.getElementById('chartTrials').getContext('2d');
const best=Math.max(...d.map(t=>t.value||0));
charts['chartTrials']=new Chart(ctx,{type:'scatter',data:{datasets:[
{label:'Trial Score',data:d.map(t=>({x:t.number,y:t.value})),
backgroundColor:d.map(t=>t.value===best?C.success:C.primary+'80'),
pointRadius:d.map(t=>t.value===best?8:4),borderColor:d.map(t=>t.value===best?C.success:C.primary),borderWidth:1},
{label:'Running Max',data:d.reduce((acc,t)=>{const prev=acc.length?acc[acc.length-1].y:0;acc.push({x:t.number,y:Math.max(prev,t.value||0)});return acc;},[]),
type:'line',borderColor:C.secondary,borderDash:[4,4],pointRadius:0,borderWidth:1.5,fill:false}]},
options:{responsive:true,plugins:{legend:{position:'top'}},
scales:{x:{title:{display:true,text:'Trial #',color:C.text3},grid:{color:C.border}},
y:{title:{display:true,text:'ROC-AUC',color:C.text3},grid:{color:C.border}}}}});

// Best params
const bestTrial=d.reduce((a,b)=>(b.value||0)>(a.value||0)?b:a,d[0]);
const pc=document.getElementById('paramsContainer');
pc.innerHTML='<div class="param-card">';
Object.entries(bestTrial.params).forEach(([k,v])=>{
pc.innerHTML+=`<div class="param-row"><span class="key">${k}</span><span class="val">${typeof v==='number'?v.toFixed(6):v}</span></div>`;});
pc.innerHTML+=`</div><div style="margin-top:12px;font-size:12px;color:${C.text3}">Best trial: #${bestTrial.number} — ROC-AUC: ${bestTrial.value.toFixed(6)}</div>`;
}catch(e){showError('paramsContainer','Run setup.py to generate trial history');}}

async function doRetrain(){
const btn=document.getElementById('retrainBtn');
btn.disabled=true;btn.textContent='⏳ Retraining...';
try{await fetch(API+'/api/retrain',{method:'POST'});
document.getElementById('retrainStatus').textContent='✅ Retraining started! Refresh in ~60s to see updated results.';
}catch(e){document.getElementById('retrainStatus').textContent='❌ Failed — is the API running?';}
setTimeout(()=>{btn.disabled=false;btn.textContent='🔄 Retrain Model';},5000);}

// Init
checkAPI().then(()=>{loadPage('overview');});

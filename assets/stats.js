'use strict';
(() => {
  const endpoint = document.currentScript.dataset.endpoint;
  const status = document.querySelector('#stats-status');
  const number = new Intl.NumberFormat('en');
  const parseDate = d3.utcParse('%Y-%m-%d');
  const colors = { views: '#2c6a94', sessions: '#278480' };
  let current = null, days = 7, request = 0;
  function frame(selector, width, height, label) {
    const host = d3.select(selector); host.selectAll('*').remove();
    return host.append('svg').attr('viewBox',`0 0 ${width} ${height}`).attr('role','img').attr('aria-label',label);
  }
  function daily(data) {
    const rows = data.daily.filter(row => row.pageviews !== null).map(row => ({...row,date:parseDate(row.day)}));
    const width = Math.max(250,document.querySelector('#daily-chart').clientWidth), height = 260;
    const svg = frame('#daily-chart',width,height,'Recorded sessions and pageviews. Dates before collection began are excluded.');
    if (!rows.length) { svg.append('text').attr('x',0).attr('y',45).text('Waiting for the first recorded visit.');return; }
    const max = Math.max(1,d3.max(rows,row=>row.pageviews));
    const y = d3.scaleLinear().domain([0,max]).nice().range([height-34,16]);
    svg.append('g').attr('transform','translate(30,0)').call(d3.axisLeft(y).ticks(4).tickFormat(v=>Number.isInteger(v)?number.format(v):'').tickSize(-(width-42))).call(g=>g.select('.domain').remove());
    if (rows.length===1) {
      document.querySelector('#daily-title').textContent='Today in focus';
      const values=[{name:'Sessions',count:rows[0].sessions,color:colors.sessions},{name:'Pageviews',count:rows[0].pageviews,color:colors.views}];
      const x=d3.scaleBand().domain(values.map(row=>row.name)).range([46,width-18]).padding(.52);
      svg.append('g').attr('transform',`translate(0,${height-34})`).call(d3.axisBottom(x).tickSize(0));
      svg.selectAll('rect').data(values).join('rect').attr('x',row=>x(row.name)).attr('y',row=>y(row.count)).attr('width',x.bandwidth()).attr('height',row=>y(0)-y(row.count)).attr('rx',4).attr('fill',row=>row.color).append('title').text(row=>`${row.name}: ${row.count}`);
    } else {
      document.querySelector('#daily-title').textContent='Daily activity';
      const x=d3.scaleUtc().domain(d3.extent(rows,row=>row.date)).range([30,width-12]);
      const step=Math.max(1,Math.ceil(rows.length/(width<450?3:6)));
      const dates=rows.filter((_,i)=>i%step===0||i===rows.length-1).map(row=>row.date);
      svg.append('g').attr('transform',`translate(0,${height-34})`).call(d3.axisBottom(x).tickValues(dates).tickFormat(d3.utcFormat('%b %d')).tickSizeOuter(0));
      for (const [key,color] of [['pageviews',colors.views],['sessions',colors.sessions]]) {
        svg.append('path').datum(rows).attr('d',d3.line().x(row=>x(row.date)).y(row=>y(row[key]))).attr('fill','none').attr('stroke',color).attr('stroke-width',2);
        svg.append('g').selectAll('circle').data(rows).join('circle').attr('cx',row=>x(row.date)).attr('cy',row=>y(row[key])).attr('r',3).attr('fill',color).append('title').text(row=>`${row.day}: ${row[key]} ${key}`);
      }
    }
    const first=d3.utcFormat('%b %d')(rows[0].date),last=d3.utcFormat('%b %d')(rows.at(-1).date);
    const average=data.range.sessions?(data.range.pageviews/data.range.sessions).toFixed(1):'0';
    document.querySelector('#daily-note').textContent=`${first===last?first:`${first}–${last}`} · ${average} pageviews per counted session`;
  }
  function hourly(data) {
    const rows=data.hourly.filter(row=>row.pageviews!==null),width=Math.max(250,document.querySelector('#hourly-chart').clientWidth),height=210;
    const svg=frame('#hourly-chart',width,height,'Recorded pageviews today by hour, Korea Standard Time.');
    if (!rows.length) {svg.append('text').attr('x',0).attr('y',40).text('No hourly activity yet.');return;}
    const x=d3.scaleBand().domain(rows.map(row=>row.hour)).range([28,width-10]).padding(.4);
    const y=d3.scaleLinear().domain([0,Math.max(1,d3.max(rows,row=>row.pageviews))]).nice().range([height-32,12]);
    svg.append('g').attr('transform',`translate(0,${height-32})`).call(d3.axisBottom(x).tickValues(rows.filter((_,i)=>i%Math.max(1,Math.ceil(rows.length/4))===0).map(row=>row.hour)).tickFormat(h=>`${String(h).padStart(2,'0')}:00`).tickSizeOuter(0));
    svg.append('g').attr('transform','translate(28,0)').call(d3.axisLeft(y).ticks(3).tickFormat(v=>Number.isInteger(v)?number.format(v):'').tickSizeOuter(0));
    svg.selectAll('rect').data(rows).join('rect').attr('x',row=>x(row.hour)+(x.bandwidth()-Math.min(x.bandwidth(),65))/2).attr('width',Math.min(x.bandwidth(),65)).attr('y',row=>y(row.pageviews)).attr('height',row=>y(0)-y(row.pageviews)).attr('rx',3).attr('fill',colors.sessions).append('title').text(row=>`${row.hour}:00 KST: ${row.pageviews} pageviews`);
  }
  function bars(selector,rows,label) {
    const width=Math.max(250,document.querySelector(selector).clientWidth),height=Math.max(120,rows.length*48+8);
    const svg=frame(selector,width,height,label);
    if (!rows.length) {svg.append('text').attr('x',0).attr('y',42).text('No activity recorded yet.');return;}
    const x=d3.scaleLinear().domain([0,Math.max(1,d3.max(rows,row=>row.count))]).range([0,width-40]);
    const group=svg.selectAll('g').data(rows).join('g').attr('transform',(_,i)=>`translate(0,${i*48})`);
    group.append('text').attr('x',0).attr('y',15).text(row=>(row.name||'Direct / internal').slice(0,Math.floor((width-50)/7)));
    group.append('text').attr('x',width-2).attr('y',15).attr('text-anchor','end').text(row=>number.format(row.count));
    group.append('rect').attr('y',27).attr('height',6).attr('rx',3).attr('width',width-40).attr('fill','#edf2f5');
    group.append('rect').attr('y',27).attr('height',6).attr('rx',3).attr('width',row=>x(row.count)).attr('fill',selector==='#devices-chart'?colors.sessions:colors.views);
  }
  function render(data) {
    document.querySelector('#sessions-today').textContent=number.format(data.today.sessions);
    document.querySelector('#views-today').textContent=number.format(data.today.pageviews);
    document.querySelector('#pages-explored').textContent=number.format(data.range.pages);
    daily(data);hourly(data);bars('#devices-chart',data.devices,'Pageviews by viewport class.');bars('#referrers-chart',data.referrers,'Pageviews by referrer hostname.');
    const story=window.sitePulseStory(data,days);
    document.querySelector('#reading-headline').textContent=story.headline;
    document.querySelector('#reading-summary').textContent=story.detail;
    document.querySelector('#reading-share').textContent=story.share===null?'':`${story.share}%`;
    document.querySelector('#reading-share-label').textContent=story.share===null?'':'of this period’s pageviews';
  }
  async function load() {
    const id=++request;status.textContent='Updating…';
    try {
      const response=await fetch(endpoint+`/api/stats?days=${days}`,{credentials:'omit',cache:'no-store'});
      if (!response.ok) throw new Error('Unavailable');
      const data=await response.json();if(id!==request)return;current=data;render(data);
      status.textContent=`Updated ${new Intl.DateTimeFormat('en',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit'}).format(new Date(data.updated_at))} KST`;
    } catch {if(id===request)status.textContent=current?'Showing the last update. Refresh is temporarily unavailable.':'Statistics are temporarily unavailable.';}
  }
  for(const button of document.querySelectorAll('[data-days]'))button.addEventListener('click',()=>{days=Number(button.dataset.days);for(const other of document.querySelectorAll('[data-days]'))other.setAttribute('aria-pressed',String(other===button));load();});
  let resizing=false;window.addEventListener('resize',()=>{if(resizing||!current)return;resizing=true;requestAnimationFrame(()=>{resizing=false;render(current);});});
  load();
})();

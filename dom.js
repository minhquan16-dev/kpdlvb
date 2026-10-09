return (()=>{
const H=window.PTITHelpers,action=arguments[0],expected=arguments[1];
const visible=e=>e.isConnected&&e.getClientRects().length&&!e.closest('[hidden],[aria-hidden="true"]')&&getComputedStyle(e).visibility!=='hidden';
const blocked=/\/(checkpoint|login|recover|two_step_verification)/i.test(location.pathname)||!!document.querySelector('input[type=password],iframe[src*="captcha"]')||[...document.querySelectorAll('[role=alert]')].some(e=>visible(e)&&/temporarily blocked|too many requests|tạm thời bị chặn|xác minh danh tính/i.test(e.innerText));
if(blocked)return {blocked:true};
if(action==='feed'){
 const posts=[],seen=new Set();
 const group=location.pathname.match(/^\/groups\/([^/]+)/)?.[1];
 const area=document.querySelector('[role=main]')||document.body;
 const anchors=[...area.querySelectorAll('a[href]')];let candidates=0,rejected=0;
 for(const a of anchors){if(!visible(a)||a.closest('[role=navigation],[role=complementary]'))continue;
 const p=H.postInfo(a.href);if(!p)continue;candidates++;
 const targetGroup=new URL(p.url).pathname.match(/^\/groups\/([^/]+)/)?.[1];
 if(group&&targetGroup!==group){rejected++;continue;}
 if(seen.has(p.id))continue;seen.add(p.id);posts.push(p);}
 return {posts,diagnostics:{anchors:anchors.length,articles:area.querySelectorAll('[role=article]').length,candidates,rejected}};
}
if(action==='feed_hover'){
 const area=document.querySelector('[role=main]')||document.body;
 return [...area.querySelectorAll('a[href]')].filter(a=>visible(a)&&!H.postInfo(a.href)&&!a.closest('[role=navigation],[role=complementary]')&&(a.querySelector('abbr,time')||/^(?:\d+\s*(?:phút|giờ|ngày|tuần|tháng|năm|m|h|d|w)|vừa xong|just now|yesterday|hôm qua)/i.test(H.clean(a.innerText)))).slice(0,12);
}
if(action==='feed_scroll'){const e=document.scrollingElement,old=e.scrollTop;e.scrollTop+=Math.max(400,e.clientHeight*.7);return {moved:e.scrollTop>old+1};}
const current=H.postInfo(location.href);if(current&&current.id!==expected)return {wrong_source:true};
const identity=root=>{const ids=new Set([...root.querySelectorAll('a[href]')].map(a=>H.postInfo(a.href)?.id).filter(Boolean));return ids;};
const dialogs=[...document.querySelectorAll('[role=dialog]')].filter(visible);
let root=dialogs.find(e=>{const ids=identity(e);return ids.size===1&&ids.has(expected);});
if(!root)root=[...document.querySelectorAll('[role=article]')].find(e=>visible(e)&&!e.parentElement?.closest('[role=article]')&&identity(e).size===1&&identity(e).has(expected));
if(!root&&dialogs.length===1&&current?.id===expected&&!identity(dialogs[0]).size)root=dialogs[0];
if(!root)return {missing_scope:true};
const selector='[role=article],[aria-label^="Bình luận của"],[aria-label^="Comment by"]';
const own=(node,e)=>node.closest(selector)===e;
const comments=[...root.querySelectorAll(selector)].filter(e=>{
 if(!visible(e)||e.querySelector('[data-ad-preview=message],[data-ad-comet-preview=message]'))return false;
 const labeled=/^(Bình luận của|Comment by|Comment from)/i.test(e.getAttribute('aria-label')||'');
 const hasID=[...e.querySelectorAll('a[href]')].some(a=>own(a,e)&&H.commentInfo(a.href).id);
 const nestedLeaf=!e.querySelector('[role=article]')&&!!e.parentElement?.closest('[role=article]');
 return labeled||hasID||nestedLeaf;
});
if(action==='read'){
 const rows=[];for(const e of comments){const links=[...e.querySelectorAll('a[href]')].filter(a=>own(a,e));if(links.some(a=>{const p=H.postInfo(a.href);return p&&p.id!==expected;}))continue;
 const text=[...e.querySelectorAll('[dir=auto]')].filter(p=>own(p,e)&&visible(p)&&!p.closest('a,button,[role=button]')&&!p.querySelector('[dir=auto]')).map(p=>H.clean(p.innerText)).filter(t=>t&&!H.uiOnly(t)&&!H.expandKind(t,true)).filter((t,i,a)=>a.indexOf(t)===i).join('\n');if(!text)continue;
 const info=links.map(a=>H.commentInfo(a.href)).find(x=>x.id)||{id:'',parent:''};const author=H.clean(links[0]?.innerText||'');rows.push({comment_id:info.id||'local_'+H.hash(expected+'|'+author+'|'+text),parent_comment_id:info.parent,text_raw:text,identifier_quality:info.id?'facebook_comment_id':'fallback_dom_text'});}
 return {rows};
}
if(action==='advance'){
 const tried=window.__ptitTried||(window.__ptitTried=new WeakMap());
 const button=[...root.querySelectorAll('button,[role=button]')].find(b=>visible(b)&&!b.matches('[disabled],[aria-disabled=true]')&&(tried.get(b)||0)<2&&H.expandKind(b.innerText,comments.some(c=>c.contains(b))));
 if(button){tried.set(button,(tried.get(button)||0)+1);button.scrollIntoView({block:'nearest'});button.click();return {clicked:true};}
 let targets=[root,...root.querySelectorAll('*')].filter(e=>visible(e)&&e.clientHeight>100&&e.scrollHeight>e.clientHeight+20&&/(auto|scroll)/.test(getComputedStyle(e).overflowY));targets.sort((a,b)=>b.querySelectorAll(selector).length-a.querySelectorAll(selector).length);
 let target=targets[0];if(!target){for(let p=root.parentElement;p&&p!==document.body;p=p.parentElement){if(p.clientHeight>100&&p.scrollHeight>p.clientHeight+20&&/(auto|scroll)/.test(getComputedStyle(p).overflowY)){target=p;break;}}}
 if(!target&&!root.matches('[role=dialog]'))target=document.scrollingElement;
 if(!target)return {missing_scroll:true};const old=target.scrollTop;target.scrollTop+=Math.max(180,target.clientHeight*.65);return {moved:target.scrollTop>old+1};
}
return {};
})();

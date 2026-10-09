(function (root) {
  "use strict";
  const clean = value => String(value || "").normalize("NFC").replace(/[\u200b\u200c\u200d\ufeff]/g, "").replace(/\s+/g, " ").trim();
  const hash = value => { let a=2166136261,b=5381; for (const c of String(value)) {a=Math.imul(a^c.charCodeAt(0),16777619); b=Math.imul(b,33)^c.charCodeAt(0);} return (a>>>0).toString(16)+(b>>>0).toString(16); };
  function postInfo(value) {
    try {
      const u=new URL(value, 'https://www.facebook.com');
      if (u.protocol!=="https:" || !/(^|\.)facebook\.com$/i.test(u.hostname)) return null;
      const match=u.pathname.match(/\/(?:posts|permalink)\/([^/?#]+)/);
      const multi=u.searchParams.get('multi_permalinks');
      const id=match?.[1] || u.searchParams.get("story_fbid") || (multi && /^\d+$/.test(multi)?multi:null);
      if (!id || !/^[\w.-]+$/.test(id)) return null;
      u.hostname="www.facebook.com";u.hash="";
      if(multi&&!match){const group=u.pathname.match(/^\/groups\/([^/]+)/);if(!group)return null;u.pathname='/groups/'+group[1]+'/permalink/'+id+'/';u.search='';}
      else if(match)u.search="";else {const owner=u.searchParams.get("id");u.search="";u.searchParams.set("story_fbid",id);if(owner)u.searchParams.set("id",owner);}
      return {id,url:u.href};
    } catch { return null; }
  }
  function commentInfo(href) {
    try { const u=new URL(href,"https://www.facebook.com");const parent=u.searchParams.get("comment_id")||"";const reply=u.searchParams.get("reply_comment_id")||"";return {id:reply||parent,parent:reply?parent:""}; } catch {return {id:"",parent:""};}
  }
  function expandKind(text, insideComment=false) {
    const t=clean(text);
    if (/^(?:xem (?:thêm |các )?(?:\d+ )?(?:bình luận|phản hồi|câu trả lời)(?: (?:khác|trước|nữa))?|xem (?:tất cả )?\d+ (?:phản hồi|câu trả lời)|view (?:more|previous|all|\d+)(?: \d+)? (?:comments|replies)(?: \(\d+\))?|\d+ (?:phản hồi|câu trả lời|replies|reply))$/i.test(t)) return "comments";
    if (insideComment && /^(?:xem thêm|see more)$/i.test(t)) return "text";
    return null;
  }
  const uiOnly = t => /^(?:thích|like|trả lời|reply|phản hồi|chia sẻ|share|đã chỉnh sửa|edited|xem bản dịch|see translation|tác giả|author|người đóng góp nổi bật|top contributor|fan cứng|top fan|\d+\s*(?:phút|giờ|ngày|tuần|tháng|năm|m|h|d|w)(?: trước| ago)?)$/i.test(clean(t));
  const csvCell=value => {let s=String(value??"");if (/^\s*[=+@-]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};
  const columns=["comment_id","post_id","post_url","parent_comment_id","text_raw","label","annotation_note","collection_method","collected_at","identifier_quality","comment_filter"];
  const csv=rows=>"\ufeff"+columns.map(csvCell).join(",")+"\r\n"+rows.map(r=>columns.map(k=>csvCell(r[k])).join(",")).join("\r\n");
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const helpers={clean,hash,postInfo,commentInfo,expandKind,uiOnly,csv,columns,esc};
  root.PTITHelpers=helpers;
  if (typeof module!=="undefined" && module.exports)module.exports=helpers;
})(typeof globalThis!=="undefined"?globalThis:this);

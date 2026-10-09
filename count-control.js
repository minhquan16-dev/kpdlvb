(() => {
  document.title='PTIT · Quét bài viết';
  document.querySelector('ol li:last-child').textContent='Nhập số bài muốn quét rồi bấm Bắt đầu. Công cụ lấy bài theo thứ tự đang hiển thị, tự mở và cuộn bình luận.';
  const box=document.createElement('div');box.style.margin='18px 0';
  box.innerHTML='<label for="target"><b>Số bài muốn quét</b></label><br><input id="target" type="number" min="1" max="500" step="1" value="20" required style="font:inherit;width:140px;margin:8px 0;padding:10px;border:1px solid #b9cbe3;border-radius:10px"><br><small>Nhập số nguyên từ 1–500. Mặc định 20 bài. Số thực tế có thể ít hơn nếu hết bài nhận diện được.</small>';
  document.querySelector('.actions').before(box);
  const input=document.getElementById('target'),start=document.getElementById('start');
  function sync(){const running=start.classList.contains('on');input.disabled=running;const text=running?'Đang quét…':'Bắt đầu quét';if(start.textContent!==text)start.textContent=text;}
  new MutationObserver(sync).observe(start,{attributes:true,childList:true});sync();
  start.onclick=async()=>{if(!input.reportValidity())return;const target=Number(input.value);if(!Number.isInteger(target)||target<1||target>500)return;
    try{start.disabled=true;const response=await fetch('/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target})});if(!response.ok)throw Error(await response.text());}
    catch(error){document.getElementById('message').textContent=error.message;start.disabled=false;}
  };
})();

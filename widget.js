(function(){
  var NICHE = document.currentScript && document.currentScript.dataset.niche || 'default';

  var css = `
#nl-widget{position:fixed;bottom:24px;right:24px;z-index:9999;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif}
#nl-btn{width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;font-size:26px;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 6px 24px rgba(37,99,235,.5);transition:.2s;border:none;outline:none}
#nl-btn:hover{transform:scale(1.08)}
#nl-box{display:none;position:absolute;bottom:72px;right:0;width:340px;background:#fff;border-radius:18px;box-shadow:0 12px 48px rgba(0,0,0,.18);overflow:hidden;flex-direction:column}
#nl-box.open{display:flex}
#nl-head{background:linear-gradient(135deg,#1e3a8a,#2563eb);padding:16px 18px;display:flex;align-items:center;gap:12px;color:#fff}
#nl-ava{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:17px;flex:0 0 auto}
#nl-info .nl-name{font-weight:700;font-size:15px}
#nl-info .nl-status{font-size:12px;color:rgba(255,255,255,.75);display:flex;align-items:center;gap:5px}
#nl-info .nl-dot{width:7px;height:7px;background:#4ade80;border-radius:50%;display:inline-block}
#nl-close{margin-left:auto;background:none;border:none;color:#fff;font-size:22px;cursor:pointer;opacity:.8;line-height:1}
#nl-close:hover{opacity:1}
#nl-msgs{flex:1;max-height:320px;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:#f8fafc}
.nl-msg{max-width:82%;padding:10px 14px;border-radius:14px;font-size:14px;line-height:1.5}
.nl-msg.bot{background:#fff;border:1px solid #e2e8f0;align-self:flex-start;border-bottom-left-radius:4px}
.nl-msg.user{background:#2563eb;color:#fff;align-self:flex-end;border-bottom-right-radius:4px}
.nl-msg.typing{color:#94a3b8;font-style:italic}
#nl-foot{padding:12px;border-top:1px solid #e2e8f0;display:flex;gap:8px;background:#fff}
#nl-input{flex:1;border:1.5px solid #e2e8f0;border-radius:10px;padding:10px 14px;font-size:14px;outline:none;font-family:inherit;resize:none;line-height:1.4;max-height:80px}
#nl-input:focus{border-color:#2563eb}
#nl-send{background:#2563eb;color:#fff;border:none;border-radius:10px;padding:10px 16px;font-weight:700;cursor:pointer;font-size:15px;transition:.2s}
#nl-send:hover{background:#1d4ed8}
#nl-send:disabled{background:#94a3b8;cursor:default}
@media(max-width:400px){#nl-box{width:calc(100vw - 32px);right:-8px}}
`;

  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var html = `
<div id="nl-widget">
  <div id="nl-box">
    <div id="nl-head">
      <div id="nl-ava">К</div>
      <div id="nl-info">
        <div class="nl-name">Константин</div>
        <div class="nl-status"><span class="nl-dot"></span> онлайн</div>
      </div>
      <button id="nl-close">✕</button>
    </div>
    <div id="nl-msgs"></div>
    <div id="nl-foot">
      <textarea id="nl-input" rows="1" placeholder="Напишите сообщение..."></textarea>
      <button id="nl-send">➤</button>
    </div>
  </div>
  <button id="nl-btn">💬</button>
</div>`;

  document.body.insertAdjacentHTML('beforeend', html);

  var box = document.getElementById('nl-box');
  var btn = document.getElementById('nl-btn');
  var msgs = document.getElementById('nl-msgs');
  var input = document.getElementById('nl-input');
  var send = document.getElementById('nl-send');
  var close = document.getElementById('nl-close');
  var history = [];
  var opened = false;

  function addMsg(text, role) {
    var d = document.createElement('div');
    d.className = 'nl-msg ' + role;
    d.textContent = text;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
    return d;
  }

  function greet() {
    var greetings = {
      dental: 'Здравствуйте! 😊 Я Константин, консультант клиники. Чем могу помочь? Записаться к врачу или узнать цены?',
      clinic: 'Здравствуйте! Я Константин, консультант клиники. Помогу выбрать врача или записаться на приём 😊',
      salon: 'Привет! 💅 Я Константин, консультант салона. Хотите записаться к мастеру или узнать цены?',
      fitness: 'Привет! 💪 Я Константин, консультант клуба. Хотите записаться на пробное занятие?',
      autoservice: 'Добрый день! 🔧 Я Константин. Нужна запись на ТО или узнать цену на услугу?',
      detailing: 'Привет! ✨ Я Константин, консультант детейлинг-центра. Что интересует — полировка, керамика или химчистка?',
      realty: 'Здравствуйте! 🏠 Я Константин, консультант по недвижимости. Помогу с подбором объекта или записью на просмотр.',
      horeca: 'Добрый день! 🍽 Я Константин. Хотите забронировать стол или узнать о мероприятиях?',
      education: 'Привет! 🎓 Я Константин, консультант школы. Хотите записаться на пробный урок или узнать о программах?',
      hr: 'Здравствуйте! 👋 Я Константин, HR-консультант. Расскажите, какая вакансия вас интересует?',
      finance: 'Добрый день! 💰 Я Константин. Помогу с вопросами по страхованию или кредитованию.',
      default: 'Здравствуйте! 😊 Я Константин, консультант NueraLead. Расскажите — какой чат-бот вам нужен?'
    };
    addMsg(greetings[NICHE] || greetings.default, 'bot');
  }

  btn.onclick = function() {
    opened = !opened;
    box.classList.toggle('open', opened);
    btn.textContent = opened ? '✕' : '💬';
    if (opened && msgs.children.length === 0) greet();
    if (opened) setTimeout(function(){ input.focus(); }, 100);
  };

  close.onclick = function() {
    opened = false;
    box.classList.remove('open');
    btn.textContent = '💬';
  };

  async function sendMsg() {
    var text = input.value.trim();
    if (!text || send.disabled) return;
    input.value = '';
    input.style.height = 'auto';
    addMsg(text, 'user');
    history.push({ role: 'user', content: text });
    send.disabled = true;
    var typing = addMsg('печатает...', 'bot typing');
    try {
      var res = await fetch('/.netlify/functions/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history, niche: NICHE })
      });
      var data = await res.json();
      var reply = data.reply || 'Секунду...';
      typing.remove();
      addMsg(reply, 'bot');
      history.push({ role: 'assistant', content: reply });
    } catch(e) {
      typing.remove();
      addMsg('Что-то пошло не так, попробуйте ещё раз 🙏', 'bot');
    }
    send.disabled = false;
    input.focus();
  }

  send.onclick = sendMsg;

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
  });

  input.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 80) + 'px';
  });
})();

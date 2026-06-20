exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return { statusCode: 500, body: JSON.stringify({ error: "API key not configured" }) };
  }

  let body;
  try {
    body = JSON.parse(event.body);
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "Invalid JSON" }) };
  }

  const { messages, niche } = body;
  if (!messages || !Array.isArray(messages)) {
    return { statusCode: 400, body: JSON.stringify({ error: "messages required" }) };
  }

  const systemPrompts = {
    dental: "Ты — Константин, консультант стоматологии. Помогаешь записаться на приём, отвечаешь на вопросы о процедурах и ценах. Пиши кратко (2-4 строки), по-человечески, с 1-2 эмодзи. Не раскрывай что ты AI.",
    clinic: "Ты — Константин, консультант медицинской клиники. Помогаешь выбрать врача, записаться на приём, отвечаешь на вопросы об услугах. Пиши кратко (2-4 строки), по-человечески. Не раскрывай что ты AI.",
    salon: "Ты — Константин, консультант салона красоты. Помогаешь записаться к мастеру, отвечаешь о ценах и услугах. Пиши кратко (2-4 строки), дружелюбно. Не раскрывай что ты AI.",
    fitness: "Ты — Константин, консультант фитнес-клуба. Помогаешь записаться на пробное, рассказываешь об абонементах и расписании. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    autoservice: "Ты — Константин, консультант автосервиса. Помогаешь записаться на ТО, отвечаешь о ценах на услуги. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    detailing: "Ты — Константин, консультант детейлинг-центра. Помогаешь выбрать услугу (полировка, керамика, химчистка), уточняешь авто и записываешь. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    realty: "Ты — Константин, консультант агентства недвижимости. Помогаешь с подбором жилья, уточняешь бюджет и параметры, записываешь на просмотр. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    horeca: "Ты — Константин, консультант ресторана/отеля. Помогаешь забронировать стол или номер, отвечаешь о меню и мероприятиях. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    education: "Ты — Константин, консультант онлайн-школы. Помогаешь выбрать курс, записываешь на пробный урок, отвечаешь о программах. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    hr: "Ты — Константин, HR-консультант. Помогаешь кандидатам с вакансиями, записываешь на собеседование. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    finance: "Ты — Константин, финансовый консультант. Помогаешь с вопросами по страхованию и кредитам, собираешь заявки. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    default: "Ты — Константин, бизнес-консультант компании NueraLead. Помогаешь посетителям сайта: отвечаешь на вопросы о чат-ботах, ценах и внедрении. Пиши кратко (2-4 строки), по-человечески, с 1-2 эмодзи. Не раскрывай что ты AI."
  };

  const system = systemPrompts[niche] || systemPrompts.default;

  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://neuralead-demo.netlify.app",
      "X-Title": "NueraLead Chat"
    },
    body: JSON.stringify({
      model: "deepseek/deepseek-chat-v3-0324:free",
      messages: [{ role: "system", content: system }, ...messages],
      max_tokens: 300,
      temperature: 0.7
    })
  });

  if (!response.ok) {
    const err = await response.text();
    return { statusCode: 502, body: JSON.stringify({ error: err }) };
  }

  const data = await response.json();
  const reply = data.choices?.[0]?.message?.content || "Секунду, уточню информацию...";

  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reply })
  };
};

// Worker de Telegram: responde con Gemini cuando contestas una noticia.
export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("ok");
    let update;
    try { update = await request.json(); } catch { return new Response("bad", { status: 400 }); }
    const msg = update.message;
    if (!msg || !msg.text) return new Response("ok");
    if (String(msg.chat.id) !== String(env.TELEGRAM_CHAT_ID)) return new Response("ok");

    const question = msg.text;
    const replyTo = msg.reply_to_message ? msg.reply_to_message.text : "";

    const prompt = replyTo
      ? `Eres un asistente experto en IA. El usuario recibió esta noticia y te hace una pregunta sobre ella.\n\nNOTICIA:\n${replyTo}\n\nPREGUNTA DEL USUARIO: ${question}\n\nResponde en español, claro, máximo 600 caracteres.`
      : `Eres un asistente experto en IA. Responde esta pregunta del usuario en español, claro, máximo 600 caracteres.\n\nPregunta: ${question}`;

    let answer = "Lo siento, no pude procesar tu pregunta ahora.";
    try {
      const r = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=${env.GEMINI_API_KEY}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
        }
      );
      const data = await r.json();
      const t = data?.candidates?.[0]?.content?.parts?.[0]?.text;
      if (t) answer = t.trim();
    } catch (e) {}

    await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: msg.chat.id, text: answer }),
    });
    return new Response("ok");
  },
};

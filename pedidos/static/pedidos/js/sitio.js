// Página pública de Chester's. Archivo propio (no en línea) para que la política CSP solo permita
// scripts del mismo sitio (spec 018).
document.addEventListener('DOMContentLoaded', () => {
  // "Pedir su pastel": baja suave al configurador y enfoca el primer campo (sin JS, el ancla funciona igual).
  document.querySelectorAll('[data-ir-al-configurador]').forEach((enlace) => {
    enlace.addEventListener('click', (e) => {
      const destino = document.getElementById('configurador');
      if (!destino) return;
      e.preventDefault();
      destino.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setTimeout(() => document.querySelector('#configurador-panel input:not([type=hidden])')?.focus({ preventScroll: true }), 700);
    });
  });

  // Chat con Melloco (spec 005): abrir/cerrar, Esc, y tras cada respuesta bajar al último mensaje.
  const chatPanel = document.getElementById('chat-panel');
  const chatBoton = document.getElementById('chat-abrir');
  if (chatPanel && chatBoton) {
    const chatTexto = chatBoton.querySelector('[data-chat-texto]');
    const chatAbierto = () => !chatPanel.classList.contains('hidden');
    const chatAlFinal = () => {
      const log = document.getElementById('chat-log');
      if (log) log.scrollTop = log.scrollHeight;
      chatPanel.querySelector('#chat-entrada input:not([type=hidden]), #chat-entrada button')?.focus({ preventScroll: true });
    };

    // Botón del chat (spec 009): siempre visible. Mientras el configurador o la Ruleta ocupan el centro
    // de la pantalla queda compacto (solo la carita de Melloco) para no tapar sus campos.
    const zonasConFormulario = new Set();
    const actualizarBotonChat = () => {
      const compacto = !chatAbierto() && zonasConFormulario.size > 0;
      chatTexto.classList.toggle('sr-only', compacto);
      chatBoton.classList.toggle('pr-5', !compacto);
      chatBoton.classList.toggle('pr-2.5', compacto);
    };
    const mostrarChat = (abrir) => {
      chatPanel.classList.toggle('hidden', !abrir);
      chatPanel.classList.toggle('flex', abrir);
      chatBoton.setAttribute('aria-expanded', String(abrir));
      chatTexto.textContent = abrir ? 'Cerrar' : 'Pedir con Melloco';
      actualizarBotonChat();
      if (abrir) chatAlFinal(); else chatBoton.focus();
    };
    chatBoton.addEventListener('click', () => mostrarChat(!chatAbierto()));
    chatPanel.querySelector('[data-chat-cerrar]').addEventListener('click', () => mostrarChat(false));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && chatAbierto()) mostrarChat(false); });
    document.body.addEventListener('htmx:afterSettle', (e) => { if (chatPanel.contains(e.target)) chatAlFinal(); });

    const observador = new IntersectionObserver((entradas) => {
      entradas.forEach((e) => (e.isIntersecting ? zonasConFormulario.add(e.target) : zonasConFormulario.delete(e.target)));
      actualizarBotonChat();
    }, { rootMargin: '-35% 0px -35% 0px' });
    ['configurador', 'ruleta'].forEach((id) => { const zona = document.getElementById(id); if (zona) observador.observe(zona); });
  }

  // Después de cada paso: si el panel quedó fuera de vista, súbelo; y mueve el foco al título.
  document.body.addEventListener('htmx:afterSwap', (e) => {
    const panel = e.detail.target;
    if (!['configurador-panel', 'ruleta-panel'].includes(panel.id)) return;
    if (panel.getBoundingClientRect().top < 64) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const destino = panel.querySelector('[aria-invalid="true"]') || panel.querySelector('[data-foco]');
    destino?.focus({ preventScroll: true });
  });
});

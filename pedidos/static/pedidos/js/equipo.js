// Gestor del equipo. Archivo propio (no en línea) para que la política CSP solo permita scripts
// del mismo sitio (spec 018).

// Confirmar antes de acciones delicadas: <form data-confirmar="¿Seguro…?">.
document.addEventListener('submit', (e) => {
  const form = e.target.closest('form[data-confirmar]');
  if (form && !window.confirm(form.dataset.confirmar)) e.preventDefault();
}, true);

document.addEventListener('DOMContentLoaded', () => {
  // Equipo (spec 014): copiar el mensaje con los datos de acceso.
  const copiar = document.getElementById('copiar-mensaje');
  if (copiar) {
    copiar.addEventListener('click', async () => {
      const area = document.getElementById('mensaje-acceso');
      try { await navigator.clipboard.writeText(area.value); } catch (err) { area.select(); document.execCommand('copy'); }
      document.getElementById('copiado').textContent = 'Copiado. Ahora pégalo en WhatsApp.';
    });
  }
});

// Vista de pedidos (spec 012): se refresca sola cada minuto, salvo si la pestaña no está a la vista,
// si alguien escribe en un campo o si hay una receta abierta (spec 017: no cerrársela al cocinero).
setInterval(() => {
  const vista = document.getElementById('vista');
  if (!vista || !vista.dataset.refrescar || !window.htmx) return;
  if (document.visibilityState !== 'visible') return;
  if (document.activeElement && document.activeElement.matches('input, select, textarea')) return;
  if (vista.querySelector('details[open]')) return;
  window.htmx.ajax('GET', vista.dataset.refrescar, { target: '#vista', swap: 'outerHTML' });
}, 60000);

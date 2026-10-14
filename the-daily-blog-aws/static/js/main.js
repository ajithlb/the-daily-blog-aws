// Small progressive enhancement: allow users to dismiss status messages.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach((message) => {
    message.setAttribute('role', 'status');
    window.setTimeout(() => {
      message.style.transition = 'opacity .35s ease';
      message.style.opacity = '0';
      window.setTimeout(() => message.remove(), 400);
    }, 5000);
  });
});

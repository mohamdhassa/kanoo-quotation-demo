const toggle = document.querySelector('[data-password-toggle]');
const password = document.querySelector('#password');
if (toggle && password) {
  toggle.addEventListener('click', () => {
    const visible = password.type === 'text';
    password.type = visible ? 'password' : 'text';
    toggle.innerHTML = visible ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
  });
}

(() => {
  const statusSelect = document.querySelector('#approved');
  const reasonField = document.querySelector('#refusalReasonField');
  const reasonSelect = document.querySelector('#reason');
  const form = document.querySelector('#quotationForm');

  function updateReasonVisibility() {
    if (!statusSelect || !reasonField || !reasonSelect) return;
    const approved = statusSelect.value === 'Approved';
    reasonField.classList.toggle('is-hidden', approved);
    reasonSelect.required = !approved;
    if (approved) reasonSelect.value = '';
  }

  statusSelect?.addEventListener('change', updateReasonVisibility);
  form?.addEventListener('reset', () => setTimeout(updateReasonVisibility, 0));
  updateReasonVisibility();
})();

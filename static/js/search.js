const searchForm = document.querySelector('#searchForm');
const resultSection = document.querySelector('#resultSection');
const resultVrn = document.querySelector('#resultVrn');
const editForm = document.querySelector('#editForm');
const editApproved = document.querySelector('#editApproved');
const editReasonField = document.querySelector('#editReasonField');
const statusBadge = document.querySelector('#statusBadge');
const toast = document.querySelector('#toast');

function showToast(message){toast.textContent=message;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2500)}
function updateEditState(){
  const approved=editApproved.value==='Approved';
  editReasonField.classList.toggle('is-hidden',approved);
  statusBadge.textContent=approved?'Approved':'Rejected';
  statusBadge.className=`status-badge ${approved?'approved':'rejected'}`;
}
searchForm.addEventListener('submit',(e)=>{e.preventDefault();resultVrn.textContent=document.querySelector('#searchVrn').value.toUpperCase();resultSection.classList.remove('is-hidden');resultSection.scrollIntoView({behavior:'smooth',block:'start'})});
editApproved.addEventListener('change',updateEditState);
editForm.addEventListener('submit',(e)=>{e.preventDefault();showToast('Changes are ready to save. Backend connection comes next.')});
updateEditState();

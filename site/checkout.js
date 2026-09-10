const $=id=>document.getElementById(id);
let activeOrder=null;
const headers=()=>({'content-type':'application/json','authorization':`Bearer ${$('apiKey').value.trim()}`});
const base=()=> $('apiBase').value.trim().replace(/\/$/,'');
const money=cents=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(cents/100);

$('createOrder').addEventListener('click',async()=>{
  $('checkoutStatus').textContent='Starting monthly billing…';
  try{
    const res=await fetch(`${base()}/v1/billing/subscriptions`,{method:'POST',headers:headers(),body:JSON.stringify({plan:$('plan').value,auto_renew:$('autoRenew').checked})});
    const data=await res.json();
    if(!res.ok) throw new Error(data.message||data.error||'Subscription creation failed');
    if(data.approval_url){
      $('checkoutStatus').innerHTML=`Monthly Venmo renewal created. <a class="pay-link" href="${data.approval_url}" rel="noopener">Authorize automatic Venmo billing</a>`;
      return;
    }
    if(data.fallback){
      activeOrder=data.fallback;
      $('venmoPanel').hidden=false;
      $('venmoAmount').textContent=`Pay ${money(data.fallback.amount_cents)}`;
      $('venmoHandle').textContent=data.fallback.venmo_business_label||'Venmo_Business_QR';
      $('paymentNote').textContent=data.fallback.payment_note;
      $('venmoQr').src=data.fallback.venmo_qr_url||'assets/Venmo_Business_QR.jpg';
      $('venmoQr').hidden=false;
      $('checkoutStatus').textContent='Automatic monthly renewal is selected, but recurring Venmo authorization is not configured on this deployment. Complete this month with the QR fallback; future renewals remain action-required until a recurring provider is connected.';
      return;
    }
    $('checkoutStatus').textContent=`Subscription ${data.subscription_id} created.`;
  }catch(e){$('checkoutStatus').textContent=e.message;}
});

$('submitPayment').addEventListener('click',async()=>{
  if(!activeOrder){$('paymentStatus').textContent='Create a billing order first.';return;}
  const tx=$('transactionReference').value.trim();
  if(!tx){$('paymentStatus').textContent='Enter the Venmo transaction reference after payment.';return;}
  $('paymentStatus').textContent='Submitting payment reference…';
  try{
    const res=await fetch(`${base()}/v1/billing/venmo/submit`,{method:'POST',headers:headers(),body:JSON.stringify({order_id:activeOrder.order_id,transaction_reference:tx})});
    const data=await res.json();
    if(!res.ok) throw new Error(data.message||data.error||'Submission failed');
    $('paymentStatus').textContent=`Submitted as ${data.payment_id}. Access activates after verified settlement.`;
  }catch(e){$('paymentStatus').textContent=e.message;}
});

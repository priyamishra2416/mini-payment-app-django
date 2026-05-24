document.addEventListener('DOMContentLoaded', () => {
  const pageLoader = document.getElementById('pageLoader');
  if (pageLoader) {
    window.setTimeout(() => {
      pageLoader.classList.add('is-hidden');
    }, 250);
  }

  document.querySelectorAll('.animated-card, .glass-card, .metric-card').forEach((card, index) => {
    card.style.animation = `fadeUp 450ms ease ${index * 40}ms both`;
  });

  document.querySelectorAll('.ripple').forEach((button) => {
    button.addEventListener('click', (event) => {
      const rect = button.getBoundingClientRect();
      const circle = document.createElement('span');
      const diameter = Math.max(rect.width, rect.height);
      const x = event.clientX - rect.left - diameter / 2;
      const y = event.clientY - rect.top - diameter / 2;
      circle.style.width = circle.style.height = `${diameter}px`;
      circle.style.left = `${x}px`;
      circle.style.top = `${y}px`;
      circle.style.position = 'absolute';
      circle.style.borderRadius = '50%';
      circle.style.background = 'rgba(255,255,255,0.35)';
      circle.style.transform = 'scale(0)';
      circle.style.animation = 'ripple 520ms ease-out';
      circle.style.pointerEvents = 'none';
      button.style.position = 'relative';
      button.style.overflow = 'hidden';
      button.appendChild(circle);
      window.setTimeout(() => circle.remove(), 560);
    });
  });

  document.querySelectorAll('.loading-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const text = button.querySelector('.btn-text');
      const loader = button.querySelector('.btn-loader');
      if (text && loader) {
        text.textContent = 'Processing...';
        loader.classList.remove('d-none');
      }
    });
  });

  document.querySelectorAll('[data-payment-id]').forEach((element) => {
    if (window.QRCode && !element.dataset.rendered) {
      new QRCode(element, {
        text: element.dataset.paymentId,
        width: element.classList.contains('large') ? 250 : 190,
        height: element.classList.contains('large') ? 250 : 190,
        colorDark: '#0b1528',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.M,
      });
      element.dataset.rendered = 'true';
    }
  });

  const receiptCard = document.querySelector('.receipt-card');
  if (receiptCard) {
    setTimeout(() => receiptCard.classList.add('receipt-ready'), 120);
  }

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const submitButton = form.querySelector('.loading-btn');
      if (submitButton) {
        const text = submitButton.querySelector('.btn-text');
        const loader = submitButton.querySelector('.btn-loader');
        if (text && loader) {
          text.textContent = 'Processing...';
          loader.classList.remove('d-none');
          submitButton.disabled = true;
        }
      }
    });
  });
});
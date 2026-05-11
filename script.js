const packages = [
  { id: 1, name: '6 hours Wetase', duration: '6 Hours', price: 500 },
  { id: 2, name: '12 Hours', duration: '12 Hours', price: 700 },
  { id: 3, name: '26 hours', duration: '26 Hours', price: 1000 },
  { id: 4, name: '3 days', duration: '3 Days', price: 2500 },
  { id: 5, name: 'Week', duration: '7 Days', price: 5000 },
  { id: 6, name: '14 Days', duration: '14 Days', price: 8500 },
  { id: 7, name: 'Premium for Tv', duration: '30 Days', price: 15000 },
  { id: 8, name: 'Month', duration: '30 Days', price: 19000 },
];

const packagesList = document.getElementById('packagesList');
const loginBtn = document.getElementById('loginBtn');
const findVoucherBtn = document.getElementById('findVoucherBtn');
const loginMessage = document.getElementById('loginMessage');
const modalOverlay = document.getElementById('modalOverlay');
const modalTitle = document.getElementById('modalTitle');
const modalContent = document.getElementById('modalContent');
const modalCloseBtn = document.getElementById('modalCloseBtn');
const voucherCodeInput = document.getElementById('voucherCode');
const themeToggle = document.getElementById('themeToggle');

let activePackageIndex = 0;
let selectedPackage = null;
const themeKey = 'hotspotTheme';

function applyTheme(theme) {
  document.body.classList.toggle('theme-light', theme === 'light');
  themeToggle.innerHTML = theme === 'light' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
  localStorage.setItem(themeKey, theme);
}

function initTheme() {
  const storedTheme = localStorage.getItem(themeKey);
  const initialTheme = storedTheme || 'dark';
  applyTheme(initialTheme);
}

function toggleTheme() {
  const isLight = document.body.classList.contains('theme-light');
  applyTheme(isLight ? 'dark' : 'light');
}

function formatPrice(amount) {
  return `UGX ${amount.toLocaleString('en-US')}`;
}

function renderPackages() {
  packagesList.innerHTML = '';
  packages.forEach((pkg, index) => {
    const card = document.createElement('div');
    card.className = 'package-card';
    if (index === activePackageIndex) {
      card.classList.add('active');
    }

    const text = document.createElement('div');
    const title = document.createElement('h3');
    title.className = 'package-name';
    title.textContent = pkg.name;
    const subtitle = document.createElement('p');
    subtitle.className = 'package-duration';
    subtitle.textContent = pkg.duration;
    text.append(title, subtitle);

    const meta = document.createElement('div');
    meta.className = 'package-meta';
    const price = document.createElement('span');
    price.className = 'package-price';
    price.textContent = formatPrice(pkg.price);
    const buyBtn = document.createElement('button');
    buyBtn.className = 'buy-btn';
    buyBtn.textContent = 'BUY';
    buyBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      handleBuy(index);
    });
    meta.append(price, buyBtn);

    card.append(text, meta);

    card.addEventListener('click', () => {
      activePackageIndex = index;
      renderPackages();
    });

    packagesList.appendChild(card);
  });
}

function openModal(title, html) {
  modalTitle.textContent = title;
  modalContent.innerHTML = html;
  modalOverlay.classList.remove('hidden');
}

function closeModal() {
  modalOverlay.classList.add('hidden');
}

function showLoginResult(message, success = false) {
  loginMessage.textContent = message;
  loginMessage.style.color = success ? 'var(--accent)' : 'var(--danger)';
}

async function handleLogin() {
  const code = voucherCodeInput.value.trim();
  if (!code) {
    showLoginResult('Please enter your phone number or voucher code.', false);
    return;
  }

  const body = /[A-Za-z]/.test(code)
    ? { voucher_code: code }
    : { phone_number: code };

  try {
    const response = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const result = await response.json();

    if (!response.ok) {
      showLoginResult(result.error || 'Login failed. Try again.', false);
      return;
    }

    if (result.message.includes('Active package')) {
      showLoginResult('You are connected. Enjoy the internet!', true);
    } else {
      showLoginResult('No active package found. Please pay to connect.', false);
      handleBuy(activePackageIndex);
    }
  } catch (error) {
    showLoginResult('Unable to contact the server. Make sure Flask is running.', false);
  }
}

function handleFindVoucher() {
  const html = `
    <p>Enter your transaction ID from your mobile money payment to recover your voucher code.</p>
    <div class="form-group">
      <input id="transactionIdInput" type="text" placeholder="Enter your transaction ID" maxlength="100" />
      <div id="validationMessage" class="validation-message"></div>
    </div>
    <button id="searchVoucherBtn" class="modal-btn-full" disabled>Search Voucher</button>
  `;

  openModal('Find My Voucher', html);

  const input = document.getElementById('transactionIdInput');
  const searchBtn = document.getElementById('searchVoucherBtn');
  const message = document.getElementById('validationMessage');

  function updateValidation() {
    const value = input.value.trim();
    const isValid = value.length >= 6;

    if (value.length === 0) {
      input.style.borderColor = 'rgba(255, 255, 255, 0.08)';
      message.textContent = '';
      searchBtn.disabled = true;
    } else if (!isValid) {
      input.style.borderColor = '#ff5e5e';
      message.textContent = `Transaction ID must be at least 6 characters (${value.length}/6)`;
      message.style.color = '#ff5e5e';
      searchBtn.disabled = true;
    } else {
      input.style.borderColor = '#00c17e';
      message.textContent = '';
      searchBtn.disabled = false;
    }
  }

  input.addEventListener('input', updateValidation);
  input.focus();

  searchBtn.addEventListener('click', searchVoucherByTransaction);
}

async function searchVoucherByTransaction() {
  const input = document.getElementById('transactionIdInput');
  const transaction_id = input.value.trim();

  if (transaction_id.length < 6) {
    openModal('Error', '<p>Transaction ID must be at least 6 characters.</p>');
    return;
  }

  openModal('Searching', `<p>Searching for voucher with transaction ID: ${transaction_id}</p>`);

  try {
    const response = await fetch('/search-voucher', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transaction_id }),
    });
    const result = await response.json();

    if (response.ok) {
      openModal('Connected Successfully', `<p>Voucher found and activated!</p><p>Session ID: ${result.session_id}</p>`);
      showLoginResult('Your voucher is active. You are now connected!', true);
    } else {
      openModal('No Voucher Found', `<p>${result.error}</p>`);
      showLoginResult(result.error, false);
    }
  } catch (error) {
    openModal('Error', '<p>Unable to search for voucher. Please check your server connection.</p>');
    showLoginResult('Server error. Please try again.', false);
  }
}

function handleBuy(index) {
  selectedPackage = packages[index];
  activePackageIndex = index;
  renderPackages();

  const packageDetailsHtml = `
    <div class="package-details">
      <div class="package-detail-row">
        <span class="package-detail-label">Package:</span>
        <span class="package-detail-value">${selectedPackage.name}</span>
      </div>
      <div class="package-detail-row">
        <span class="package-detail-label">Duration:</span>
        <span class="package-detail-value">${selectedPackage.duration}</span>
      </div>
      <div class="package-detail-row">
        <span class="package-detail-label">Price:</span>
        <span class="package-detail-value">${formatPrice(selectedPackage.price)}</span>
      </div>
    </div>
    <div class="form-group">
      <label for="paymentPhone">Phone Number *</label>
      <input id="paymentPhone" type="tel" placeholder="Enter your mobile money number" />
    </div>
    <div class="form-group optional">
      <label for="paymentEmail">Email Address</label>
      <input id="paymentEmail" type="email" placeholder="Enter your email address" />
    </div>
    <button id="confirmPayBtn" class="modal-btn-full">Pay Now</button>
  `;

  openModal(selectedPackage.name, packageDetailsHtml);
  document.getElementById('confirmPayBtn').addEventListener('click', confirmPayment);
}

async function confirmPayment() {
  const phone = document.getElementById('paymentPhone').value.trim();

  if (!phone) {
    openModal('Payment Error', '<p>Please enter a valid phone number before continuing.</p>');
    return;
  }

  openModal('Processing Payment', `<p>Sending payment request to ${phone}. Please enter your PIN when you receive the message.</p>`);

  try {
    const response = await fetch('/pay', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phone, package_id: selectedPackage.id }),
    });
    const result = await response.json();

    if (response.ok) {
      openModal('Connected Successfully', `<p>Your payment is complete and your package is active.</p><p>Session ID: ${result.session_id}</p>`);
      showLoginResult('Connected successfully. You may now use the internet.', true);
    } else {
      openModal('Connected Failed', `<p>Payment failed. Please check your balance or phone number.</p><p>${result.error || 'Try again later.'}</p>`);
      showLoginResult('Payment failed. Check your phone or try another number.', false);
    }
  } catch (error) {
    openModal('Connected Failed', '<p>Unable to process payment. Ensure the server is running.</p>');
    showLoginResult('Payment failed. Server error or network issue.', false);
  }
}

loginBtn.addEventListener('click', handleLogin);
findVoucherBtn.addEventListener('click', handleFindVoucher);
modalCloseBtn.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', (event) => {
  if (event.target === modalOverlay) {
    closeModal();
  }
});

voucherCodeInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    handleLogin();
  }
});

themeToggle.addEventListener('click', toggleTheme);

initTheme();
renderPackages();

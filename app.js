const searchInput = document.querySelector('#search');
const buttons = Array.from(document.querySelectorAll('.filter-button'));
const cards = Array.from(document.querySelectorAll('.dish-card'));
const sections = Array.from(document.querySelectorAll('.menu-section'));
const empty = document.querySelector('#empty-state');
const cartButton = document.querySelector('#cart-button');
const cartButtonCount = document.querySelector('#cart-button-count');
const cartButtonTotal = document.querySelector('#cart-button-total');
const cartDrawer = document.querySelector('#cart-drawer');
const cartBackdrop = document.querySelector('#cart-backdrop');
const cartClose = document.querySelector('#cart-close');
const cartItems = document.querySelector('#cart-items');
const cartEmpty = document.querySelector('#cart-empty');
const cartTotal = document.querySelector('#cart-total');
const cartClear = document.querySelector('#cart-clear');

const CART_STORAGE_KEY = 'montimar-cart-v1';
const menuItems = new Map(
  cards.map((card) => [
    card.dataset.slug,
    {
      slug: card.dataset.slug,
      name: card.dataset.name,
      originalName: card.dataset.originalName,
      price: Number.parseFloat(card.dataset.price) || 0,
    },
  ]),
);

let activeCategory = 'All';
let cart = loadCart();

function formatMoney(value) {
  return `EUR ${value.toFixed(2)}`;
}

function loadCart() {
  try {
    const saved = JSON.parse(localStorage.getItem(CART_STORAGE_KEY) || '{}');
    return Object.fromEntries(
      Object.entries(saved)
        .filter(([slug, quantity]) => menuItems.has(slug) && Number.isInteger(quantity) && quantity > 0)
        .map(([slug, quantity]) => [slug, quantity]),
    );
  } catch {
    return {};
  }
}

function saveCart() {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
}

function getQuantity(slug) {
  return cart[slug] || 0;
}

function setQuantity(slug, quantity) {
  const nextQuantity = Math.max(0, quantity);
  if (!menuItems.has(slug)) return;
  if (nextQuantity === 0) {
    delete cart[slug];
  } else {
    cart[slug] = nextQuantity;
  }
  saveCart();
  renderCart();
}

function increaseItem(slug) {
  setQuantity(slug, getQuantity(slug) + 1);
}

function decreaseItem(slug) {
  setQuantity(slug, getQuantity(slug) - 1);
}

function getCartRows() {
  return Object.entries(cart)
    .map(([slug, quantity]) => {
      const item = menuItems.get(slug);
      return item ? { ...item, quantity, subtotal: item.price * quantity } : null;
    })
    .filter(Boolean);
}

function getCartSummary() {
  return getCartRows().reduce(
    (summary, item) => ({
      count: summary.count + item.quantity,
      total: summary.total + item.subtotal,
    }),
    { count: 0, total: 0 },
  );
}

function itemLabel(count) {
  return `${count} ${count === 1 ? 'item' : 'items'}`;
}

function renderCardControls() {
  cards.forEach((card) => {
    const quantity = getQuantity(card.dataset.slug);
    const addButton = card.querySelector('[data-cart-add]');
    const controls = card.querySelector('[data-cart-controls]');
    const quantityLabel = card.querySelector('[data-cart-quantity]');

    addButton.hidden = quantity > 0;
    controls.hidden = quantity === 0;
    quantityLabel.textContent = quantity;
  });
}

function renderCartItems(rows) {
  cartItems.replaceChildren();
  rows.forEach((item) => {
    const row = document.createElement('article');
    row.className = 'cart-item';
    row.innerHTML = `
      <div>
        <h3></h3>
        <p></p>
      </div>
      <strong></strong>
      <div class="quantity-control">
        <button type="button" data-cart-decrease="${item.slug}" aria-label="Decrease ${item.name}">-</button>
        <span>${item.quantity}</span>
        <button type="button" data-cart-increase="${item.slug}" aria-label="Increase ${item.name}">+</button>
      </div>
    `;
    row.querySelector('h3').textContent = item.name;
    row.querySelector('p').textContent = item.originalName;
    row.querySelector('strong').textContent = formatMoney(item.subtotal);
    cartItems.append(row);
  });
}

function renderCart() {
  const rows = getCartRows();
  const { count, total } = getCartSummary();

  cartButtonCount.textContent = itemLabel(count);
  cartButtonTotal.textContent = formatMoney(total);
  cartTotal.textContent = formatMoney(total);
  cartEmpty.hidden = rows.length !== 0;
  cartItems.hidden = rows.length === 0;
  cartClear.disabled = rows.length === 0;

  renderCardControls();
  renderCartItems(rows);
}

function openCart() {
  cartDrawer.hidden = false;
  cartDrawer.classList.add('open');
  cartDrawer.setAttribute('aria-hidden', 'false');
  cartBackdrop.hidden = false;
  cartClose.focus();
}

function closeCart() {
  cartDrawer.classList.remove('open');
  cartDrawer.setAttribute('aria-hidden', 'true');
  cartDrawer.hidden = true;
  cartBackdrop.hidden = true;
  cartButton.focus();
}

function update() {
  const query = searchInput.value.trim().toLowerCase();
  let visibleCount = 0;

  cards.forEach((card) => {
    const categoryMatches = activeCategory === 'All' || card.dataset.category === activeCategory;
    const searchMatches = !query || card.dataset.search.includes(query);
    const visible = categoryMatches && searchMatches;
    card.hidden = !visible;
    if (visible) visibleCount += 1;
  });

  sections.forEach((section) => {
    const hasVisibleCard = Array.from(section.querySelectorAll('.dish-card')).some((card) => !card.hidden);
    section.hidden = !hasVisibleCard;
  });

  empty.hidden = visibleCount !== 0;
}

buttons.forEach((button) => {
  button.addEventListener('click', () => {
    activeCategory = button.dataset.category;
    buttons.forEach((item) => item.classList.toggle('active', item === button));
    update();
  });
});

searchInput.addEventListener('input', update);
document.addEventListener('click', (event) => {
  const addButton = event.target.closest('[data-cart-add]');
  const increaseButton = event.target.closest('[data-cart-increase]');
  const decreaseButton = event.target.closest('[data-cart-decrease]');

  if (addButton) increaseItem(addButton.dataset.cartAdd);
  if (increaseButton) increaseItem(increaseButton.dataset.cartIncrease);
  if (decreaseButton) decreaseItem(decreaseButton.dataset.cartDecrease);
});

cartButton.addEventListener('click', openCart);
cartClose.addEventListener('click', closeCart);
cartBackdrop.addEventListener('click', closeCart);
cartClear.addEventListener('click', () => {
  cart = {};
  saveCart();
  renderCart();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && cartDrawer.classList.contains('open')) closeCart();
});

update();
renderCart();

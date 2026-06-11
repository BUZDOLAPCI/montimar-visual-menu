const searchInput = document.querySelector('#search');
const buttons = Array.from(document.querySelectorAll('.filter-button'));
const cards = Array.from(document.querySelectorAll('.dish-card'));
const sections = Array.from(document.querySelectorAll('.menu-section'));
const empty = document.querySelector('#empty-state');

let activeCategory = 'All';

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
update();

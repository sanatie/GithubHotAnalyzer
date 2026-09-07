import { ref, watch, computed } from 'vue';

const STORAGE_KEY = 'github-analyzer-cart';

function loadCart() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    return [];
  }
}

const cartItems = ref(loadCart());

watch(cartItems, (val) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(val));
  } catch (e) {
    // localStorage 写入失败时静默忽略
  }
}, { deep: true });

const cartCount = computed(() => cartItems.value.length);

function cartId(item) {
  return `${item.author}/${item.name}`;
}

const cartIdSet = computed(() => new Set(cartItems.value.map(cartId)));

function isInCart(item) {
  return cartIdSet.value.has(cartId(item));
}

function addToCart(item) {
  if (isInCart(item)) {
    return { added: false, message: '该项目已在购物车中' };
  }
  cartItems.value.push({
    name: item.name,
    author: item.author,
    description: item.description || '',
    language: item.language || '',
    stars: item.stars || '',
    github_url: item.github_url || `https://github.com/${item.author}/${item.name}`,
    added_at: Date.now(),
  });
  return { added: true, message: '已加入购物车' };
}

function removeFromCartByAuthorName(author, name) {
  const idx = cartItems.value.findIndex(i => i.author === author && i.name === name);
  if (idx > -1) {
    cartItems.value.splice(idx, 1);
  }
}

function removeFromCartByIndex(idx) {
  if (idx > -1 && idx < cartItems.value.length) {
    cartItems.value.splice(idx, 1);
  }
}

function removeItems(predicate) {
  cartItems.value = cartItems.value.filter(item => !predicate(item));
}

function clearCart() {
  cartItems.value = [];
}

export default function useCart() {
  return {
    cartItems,
    cartCount,
    isInCart,
    addToCart,
    removeFromCartByAuthorName,
    removeFromCartByIndex,
    removeItems,
    clearCart,
  };
}
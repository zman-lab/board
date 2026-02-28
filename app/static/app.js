// Theme toggle
(function () {
  const saved = localStorage.getItem('theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  else if (window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.setAttribute('data-theme', 'dark');
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

// Like handler
function handleLike(btn, postId) {
  const author = prompt('좋아요를 누를 이름을 입력하세요:');
  if (!author || !author.trim()) return;
  const form = btn.closest('form');
  form.querySelector('input[name="author"]').value = author.trim();
  form.submit();
}

// Markdown rendering
document.addEventListener('DOMContentLoaded', function () {
  if (typeof marked === 'undefined') return;
  marked.setOptions({ breaks: true, gfm: true });
  document.querySelectorAll('[data-markdown]').forEach(function (el) {
    var raw = el.getAttribute('data-markdown');
    // Decode HTML entities
    var txt = document.createElement('textarea');
    txt.innerHTML = raw;
    el.innerHTML = marked.parse(txt.value);
  });
});

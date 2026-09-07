<template>
  <div class="tech-stack-tags">
    <span
      v-for="tag in tags"
      :key="tag.name"
      class="tag"
      :style="{ backgroundColor: getTagColor(tag.name).bg, color: getTagColor(tag.name).text }"
    >
      {{ tag.name }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  tags: {
    type: Array,
    default: () => []
  }
});

const colorMap = {
  JavaScript: { bg: '#f7df1e', text: '#000' },
  TypeScript: { bg: '#3178c6', text: '#fff' },
  Python: { bg: '#3572A5', text: '#fff' },
  Java: { bg: '#b07219', text: '#fff' },
  Go: { bg: '#00ADD8', text: '#fff' },
  Rust: { bg: '#dea584', text: '#000' },
  Vue: { bg: '#41b883', text: '#fff' },
  React: { bg: '#61dafb', text: '#000' },
  Angular: { bg: '#dd0031', text: '#fff' },
  Node: { bg: '#339933', text: '#fff' },
  PHP: { bg: '#4F5D95', text: '#fff' },
  Ruby: { bg: '#701516', text: '#fff' },
  Swift: { bg: '#F05138', text: '#fff' },
  Kotlin: { bg: '#A97BFF', text: '#fff' },
  C: { bg: '#555555', text: '#fff' },
  'C++': { bg: '#f34b7d', text: '#fff' },
  'C#': { bg: '#178600', text: '#fff' },
  HTML: { bg: '#e34c26', text: '#fff' },
  CSS: { bg: '#563d7c', text: '#fff' },
  Shell: { bg: '#89e051', text: '#000' },
  Dockerfile: { bg: '#384d54', text: '#fff' },
  Markdown: { bg: '#083fa1', text: '#fff' }
};

function getTagColor(name) {
  return colorMap[name] || { bg: '#909399', text: '#fff' };
}
</script>

<style scoped>
.tech-stack-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
</style>

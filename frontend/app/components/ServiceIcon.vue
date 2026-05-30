<script setup lang="ts">
defineProps<{
  title: string
  icon: string
  large?: boolean
}>()
</script>

<template>
  <button class="flex flex-col items-center">
    <div
      class="flex items-center justify-center rounded-[14px] bg-[#edf3f2]"
      :class="large ? 'h-[54px] w-[54px]' : 'h-[46px] w-[46px]'"
    >
      <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
        <path :d="icon" fill="currentColor" />
      </svg>
    </div>

    <p class="mt-2 max-w-[70px] truncate text-center text-[12px] text-[#273043]">
      {{ title }}
    </p>
  </button>
</template>
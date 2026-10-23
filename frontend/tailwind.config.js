import preset, { content } from 'frappe-ui/tailwind'

// PharmaStock tokens. Warm paper, midnight ink, one apothecary green; amber and red only for warnings.
export default {
  presets: [preset],
  content: [...content, './index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Newsreader Variable"', 'Georgia', 'serif'],
        body: ['"Figtree Variable"', 'system-ui', 'sans-serif'],
        label: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        paper: { DEFAULT: '#F6F5F1', deep: '#EFEDE7' },
        ink: { DEFAULT: '#16181D', soft: '#4B4E56', mute: '#8B8D93', faint: '#B7B8BB' },
        line: { DEFAULT: '#E8E6E0', strong: '#D9D6CE' },
        apo: { DEFAULT: '#235A49', deep: '#173F33', mid: '#4D8B74', soft: '#E5EEE9', mist: '#F1F6F3' },
        warn: { DEFAULT: '#A35F17', soft: '#F8EEDF' },
        alert: { DEFAULT: '#A83A31', soft: '#F8E7E4' },
      },
      boxShadow: {
        card: '0 1px 2px rgba(22,24,29,.04), 0 1px 1px rgba(22,24,29,.02)',
        lift: '0 12px 32px -12px rgba(22,24,29,.18), 0 2px 6px rgba(22,24,29,.04)',
      },
    },
  },
}

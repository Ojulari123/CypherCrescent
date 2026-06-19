import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import { resolve } from 'path'

// Vite's SSR transform (used by vitest in Node) doesn't apply the `define`
// plugin for import.meta.* properties. This plugin does the replacement
// explicitly so the stores' import.meta.client guards evaluate correctly.
const importMetaClientPlugin = {
  name: 'vitest-nuxt-import-meta',
  enforce: 'pre' as const,
  transform(code: string) {
    return code
      .replace(/\bimport\.meta\.client\b/g, 'true')
      .replace(/\bimport\.meta\.server\b/g, 'false')
  },
}

export default defineConfig({
  plugins: [
    importMetaClientPlugin,
    AutoImport({ imports: ['vue'], dts: false }),
    vue(),
  ],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.ts'],
  },
  resolve: {
    alias: {
      '~': resolve(__dirname, '.'),
    },
  },
})

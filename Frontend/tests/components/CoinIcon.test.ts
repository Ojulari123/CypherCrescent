import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CoinIcon from '~/components/CoinIcon.vue'

describe('CoinIcon', () => {
  it('renders an img when image prop is provided', () => {
    const wrapper = mount(CoinIcon, {
      props: { slug: 'bitcoin', symbol: 'BTC', image: 'https://example.com/btc.png', size: 32 },
    })
    expect(wrapper.find('img').exists()).toBe(true)
    expect(wrapper.find('img').attributes('src')).toBe('https://example.com/btc.png')
  })

  it('renders fallback div when no image prop', () => {
    const wrapper = mount(CoinIcon, {
      props: { slug: 'bitcoin', symbol: 'BTC', image: null },
    })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toBe('BTC')
  })

  it('falls back to div after img load error', async () => {
    const wrapper = mount(CoinIcon, {
      props: { slug: 'bitcoin', symbol: 'BTC', image: 'https://example.com/btc.png' },
    })
    expect(wrapper.find('img').exists()).toBe(true)
    await wrapper.find('img').trigger('error')
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('div').exists()).toBe(true)
  })

  it('uses first 3 chars of symbol uppercased for fallback letters', () => {
    const wrapper = mount(CoinIcon, {
      props: { slug: 'shib', symbol: 'shib', image: null },
    })
    expect(wrapper.text()).toBe('SHI')
  })

  it('falls back to slug when symbol is not provided', () => {
    const wrapper = mount(CoinIcon, {
      props: { slug: 'bitcoin', image: null },
    })
    expect(wrapper.text()).toBe('BIT')
  })

  it('applies size to img width and height attributes', () => {
    const wrapper = mount(CoinIcon, {
      props: { slug: 'bitcoin', symbol: 'BTC', image: 'https://example.com/btc.png', size: 48 },
    })
    const img = wrapper.find('img')
    expect(img.attributes('width')).toBe('48')
    expect(img.attributes('height')).toBe('48')
  })

  it('applies size style to fallback div', () => {
    const wrapper = mount(CoinIcon, {
      props: { slug: 'bitcoin', symbol: 'BTC', image: null, size: 40 },
    })
    const div = wrapper.find('div')
    expect(div.attributes('style')).toContain('width: 40px')
    expect(div.attributes('style')).toContain('height: 40px')
  })
})

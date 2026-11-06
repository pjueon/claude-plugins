import { expect, test } from 'claude-code/testing'

import { formatTokens, prettyModel } from '../hooks/register'

const measure = (tokens: number, percent: number) => ({
  context: { tokens, window: 200_000, percent },
  rateLimits: [],
  changed: ['context' as const],
})
const props = {
  hasSurvey: false,
  isWorking: false,
  maxRows: 3,
  bodyColumns: 120,
  scroll: { offset: 0, bodyRows: 1 },
  view: {},
}

test('모델 id를 읽기 쉬운 이름으로 바꾼다', async () => {
  expect(prettyModel('claude-opus-5-5')).toBe('Opus 5.5')
  expect(prettyModel('claude-sonnet-5-5[1m]')).toBe('Sonnet 5.5 (1M)')
  expect(prettyModel('claude-haiku-4-5-20251001')).toBe('Haiku 4.5')
  expect(prettyModel('claude-opus-5-20260101')).toBe('Opus 5')
  expect(prettyModel('Opus 5.5')).toBe('Opus 5.5')
  expect(formatTokens(84_000)).toBe('84k')
  expect(formatTokens(1_000_000)).toBe('1M')
})

test('band에 메인 루프의 effort를 표시하고 서브에이전트 step은 무시한다', async ($, on) => {
  on('session.model', () => ({ value: 'claude-opus-5-5' }))
  on('ui.render', () => ({ type: 'Box', children: [] }))
  on('session.measure', ($, e) => ({ changed: e.changed }))
  on('turn.step', async function* (_, e) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [] } as never
  })
  const step = async (effort: 'high' | 'max', agentId?: string) => {
    for await (const _ of $.turn.step({ turnId: 't', index: 0, model: 'claude-opus-5-5', effort, messageCount: 1, agentId })) void _
  }
  await $.session.measure(measure(84_000, 42))
  const mount = () =>
    $.ui.mount({ plugin: 'model-band', surface: 'terminal', component: 'AbovePrompt', props })

  let ui = await mount()
  expect(await ui.find({ type: 'Text', text: / · (high|max)$/ })).toBeUndefined()
  await ui.unmount()

  await step('high')
  await step('max', 'sub-1')
  ui = await mount()
  expect(await ui.find({ type: 'Text', text: ' · high' })).toBeDefined()
  await ui.unmount()
})

test('band에 모델과 컨텍스트를 표시하고 80% 이상이면 경고 색을 쓴다', async ($, on) => {
  on('session.model', () => ({ value: 'claude-opus-5-5' }))
  on('ui.render', () => ({ type: 'Box', children: [] }))
  on('session.measure', ($, e) => ({ changed: e.changed }))
  for (const surface of ['terminal', 'desktop'] as const) {
    await $.session.measure(measure(84_000, 42))
    let ui = await $.ui.mount({ plugin: 'model-band', surface, component: 'AbovePrompt', props })
    expect(await ui.find({ type: 'Text', text: 'Opus 5.5' })).toBeDefined()
    const ctx = await ui.find({ type: 'Text', text: 'context 42% (84k/200k)' })
    expect(ctx).toBeDefined()
    expect(ctx?.props.color).toBeUndefined()
    await ui.unmount()

    await $.session.measure(measure(170_000, 85))
    ui = await $.ui.mount({ plugin: 'model-band', surface, component: 'AbovePrompt', props })
    expect((await ui.find({ type: 'Text', text: /^context 85%/ }))?.props.color).toBe('warning')
    await ui.unmount()
  }
})

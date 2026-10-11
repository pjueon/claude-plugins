import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Context } from '../types'

const model = atom({ plugin: 'model-band', key: 'model' } as const, null)
const context = atom({ plugin: 'model-band', key: 'context' } as const, null)

const WARN_PERCENT = 80

// claude-opus-5-5[1m] → Opus 5.5 (1M)
export function prettyModel(id: string): string {
  const m = /^claude-([a-z]+)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?(\[1m\])?$/i.exec(id)
  if (!m) return id
  const name = m[1]!.charAt(0).toUpperCase() + m[1]!.slice(1)
  const version = m[3] ? `${m[2]}.${m[3]}` : m[2]
  return `${name} ${version}${m[4] ? ' (1M)' : ''}`
}

export function formatTokens(n: number): string {
  return n >= 1_000_000 ? `${+(n / 1_000_000).toFixed(1)}M` : `${Math.round(n / 1000)}k`
}

async function refreshModel($: EngineInterface) {
  const id = await $.session.model()
  if (id !== (await read($, model))) await update($, model, () => id)
}

async function setContext($: EngineInterface, c: Context) {
  const next: Context = { tokens: c.tokens, window: c.window, percent: c.percent }
  await update($, context, () => next)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await refreshModel($)
    await setContext($, (await $.session.usage()).context)
    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    await setContext($, e.context)
    await refreshModel($)
    return next(e)
  })

  // /model 로 바꾼 뒤 첫 응답 전에도 반영되도록
  on('prompt.submit', async ($, e, next) => {
    void refreshModel($).catch(() => {})
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const id = await read($, model)
    if (e.props.hasSurvey || id === null) return next(e)

    const c = await read($, context)
    const { Box, Text } = $.ui.resolve(e)
    const isWarn = (c?.percent ?? 0) >= WARN_PERCENT
    const ctx =
      c?.percent === undefined
        ? `context –/${formatTokens(c?.window ?? 0)}`
        : `context ${c.percent}% (${formatTokens(c.tokens ?? 0)}/${formatTokens(c.window)})`

    return (
      <Box>
        <Text color="claude" bold>
          {prettyModel(id)}
        </Text>
        <Text dimColor> · </Text>
        <Text color={isWarn ? 'warning' : undefined} dimColor={!isWarn}>
          {ctx}
        </Text>
      </Box>
    )
  })
}

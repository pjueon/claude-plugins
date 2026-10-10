export type Context = { tokens?: number; window: number; percent?: number }

declare module 'claude-code' {
  interface PluginState {
    'model-band': { model: string | null; context: Context | null }
  }
}

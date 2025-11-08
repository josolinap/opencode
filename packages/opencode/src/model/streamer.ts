export async function* normalizeStream<T>(input: Promise<T> | AsyncIterable<T> | T) {
  if ((input as any)?.[Symbol.asyncIterator]) {
    for await (const chunk of input as AsyncIterable<T>) {
      yield chunk
    }
    return
  }
  const v = await (input as Promise<T> | T)
  yield v
}

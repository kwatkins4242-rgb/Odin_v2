memory_bridge.js
    ```js
// replace the stub saveDailySummary with:
async function saveDailySummary(date, summary, keyEvents=[], emotions={}, topics=[]) {
  try {
    await client.post('/summarize', {
      date,
      summary,
      key_events: keyEvents,
      emotions,
      topics
    });
    return true;
  } catch {
    return false;
  }
}
```
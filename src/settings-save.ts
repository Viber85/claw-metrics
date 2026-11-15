type Save = () => Promise<boolean>;

type SliderBatch = {
  save: Save;
  complete: (ok: boolean) => void;
  result: Promise<boolean>;
  timer?: ReturnType<typeof setTimeout>;
};

// Send the latest slider value in each short interval. If the backend is
// busy, keep merging values until the next save actually starts.
export function createSettingsSaveQueue(delay = 120) {
  let tail = Promise.resolve();
  let pending: SliderBatch | undefined;

  function enqueue(save: Save) {
    const result = tail.then(save).catch(() => false);
    tail = result.then(() => {});
    return result;
  }

  function schedule(batch: SliderBatch) {
    if (batch.timer === undefined) return;
    clearTimeout(batch.timer);
    batch.timer = undefined;
    void enqueue(() => {
      if (pending === batch) pending = undefined;
      return batch.save();
    }).then(batch.complete);
  }

  function flush() {
    if (pending) {
      schedule(pending);
      pending = undefined;
    }
    return tail;
  }

  function commit(save: Save, slider = false) {
    if (!slider) {
      void flush();
      return enqueue(save);
    }
    if (pending) {
      pending.save = save;
      return pending.result;
    }
    let complete!: SliderBatch["complete"];
    const result = new Promise<boolean>(resolve => { complete = resolve; });
    const batch: SliderBatch = {save, complete, result};
    pending = batch;
    batch.timer = setTimeout(() => schedule(batch), delay);
    return result;
  }

  return {commit, flush};
}

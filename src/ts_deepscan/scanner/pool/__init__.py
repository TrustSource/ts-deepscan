import sys
import typing as t
import multiprocessing as mp
import multiprocessing.pool
import multiprocessing.queues


def get_context() -> mp.context.DefaultContext:
    """
    Return multiprocessing context based on the OS
    """
    if sys.platform != "win32":
        return mp.get_context('fork')
    else:
        return mp.get_context('spawn')


_ctx = get_context()


class Pool(mp.pool.Pool):
    @staticmethod
    def Process(ctx, *args, **kwargs):
        return PoolProcess(*args, **kwargs)

    def find_worker(self, task: mp.pool.ApplyResult) -> t.Optional[_ctx.Process]:
        return next((w for w in self._pool if w.job == task._job), None)  # noqa


class PoolProcess(_ctx.Process):
    class QueueObserver(mp.queues.SimpleQueue):
        def __init__(self, q: mp.queues.SimpleQueue, job: mp.Value):  # noqa
            self._q = q
            self._job = job

            self._reader = q._reader  # noqa
            self._writer = q._writer  # noqa
            self._rlock = q._rlock  # noqa
            self._wlock = q._wlock  # noqa
            self._poll = q._poll  # noqa

        def get(self):
            if task := self._q.get():
                self._job.value = task[0]

            return task

    def __init__(self, args=(), *_args, **_kwargs):
        self._job = mp.Value('i', -1)
        inqueue = PoolProcess.QueueObserver(args[0], self._job)  # noqa
        super().__init__(args=(inqueue,) + tuple(args[1:]), *_args, **_kwargs)

    @property
    def job(self):
        return self._job.value


_pool: t.Optional[Pool] = None


def get_pool() -> Pool:
    global _pool

    if not _pool:
        _pool = Pool(context=_ctx.get_context())

    return _pool

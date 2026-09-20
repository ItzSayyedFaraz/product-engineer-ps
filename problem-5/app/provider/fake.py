from collections.abc import Callable, Iterator

from app.provider.base import ModelProvider


class FakeModelProvider(ModelProvider):
    def __init__(
        self,
        chunks: list[str],
        on_chunk: Callable[[int, str], None] | None = None,
        fail_at_index: int | None = None,
        failure_message: str = "Fake provider failure",
    ):
        self.chunks = chunks
        self.on_chunk = on_chunk
        self.fail_at_index = fail_at_index
        self.failure_message = failure_message

        self.invocation_count = 0
        self.consumed_chunks = 0

    def stream(
        self,
        user_input: str,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[str]:
        self.invocation_count += 1

        for index, chunk in enumerate(self.chunks):

            if should_stop is not None and should_stop():
                return

            if (
                self.fail_at_index is not None
                and index == self.fail_at_index
            ):
                raise RuntimeError(self.failure_message)

            self.consumed_chunks += 1

            yield chunk

            if self.on_chunk is not None:
                self.on_chunk(index, chunk)
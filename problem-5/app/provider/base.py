from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator


class ModelProvider(ABC):
    @abstractmethod
    def stream(
        self,
        user_input: str,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[str]:
        """
        Stream response chunks.

        should_stop allows the runtime to cooperatively stop
        provider consumption because of cancellation, timeout,
        or another runtime-controlled condition.
        """
        raise NotImplementedError
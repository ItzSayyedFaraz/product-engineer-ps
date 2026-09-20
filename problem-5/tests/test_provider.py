from app.provider.fake import FakeModelProvider


def test_fake_provider_streams_chunks_in_order():
    provider = FakeModelProvider(
        ["Hello", " ", "world", "!"]
    )

    chunks = list(provider.stream("Say hello"))

    assert chunks == [
        "Hello",
        " ",
        "world",
        "!",
    ]


def test_fake_provider_records_invocation():
    provider = FakeModelProvider(
        ["Hello"]
    )

    assert provider.invocation_count == 0

    list(provider.stream("Say hello"))

    assert provider.invocation_count == 1
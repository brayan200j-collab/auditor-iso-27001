from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from auditor.documents.domain.chunking import (
    MAX_CHARS,
    PageText,
    chunk_pages,
    normalize,
)
from tests.support.pdfs import POLICY_PAGES


def test_chunks_keep_page_numbers_and_never_cross_pages() -> None:
    pages = [PageText(number, text) for number, text in enumerate(POLICY_PAGES, start=1)]
    chunks = chunk_pages(pages)
    assert {chunk.page for chunk in chunks} == set(range(1, len(POLICY_PAGES) + 1))
    for chunk in chunks:
        assert chunk.content in normalize(POLICY_PAGES[chunk.page - 1]).replace("\n", " ") or all(
            sentence in POLICY_PAGES[chunk.page - 1].replace("\n", " ")
            for sentence in chunk.content.split(". ")[:1]
        )
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_asset_inventory_is_on_page_three_with_its_section() -> None:
    pages = [PageText(number, text) for number, text in enumerate(POLICY_PAGES, start=1)]
    inventory = [chunk for chunk in chunk_pages(pages) if "inventario de activos" in chunk.content]
    assert inventory
    assert {chunk.page for chunk in inventory} == {3}
    assert inventory[0].section == "5. Gestión de activos"


def test_long_text_is_split_with_overlap_and_bounded_size() -> None:
    sentence = "La empresa realiza copias de respaldo diarias de sus servidores principales. "
    chunks = chunk_pages([PageText(1, sentence * 60)])
    assert len(chunks) > 1
    assert all(len(chunk.content) <= MAX_CHARS for chunk in chunks)
    first_tail = chunks[0].content.split(". ")[-1]
    assert first_tail.strip(". ") in chunks[1].content


def test_empty_pages_produce_no_chunks() -> None:
    assert chunk_pages([PageText(1, "   \n\n "), PageText(2, "")]) == []


@given(
    st.lists(
        st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=3000),
        min_size=1,
        max_size=4,
    )
)
def test_any_text_produces_bounded_page_tagged_chunks(texts: list[str]) -> None:
    pages = [PageText(number, text) for number, text in enumerate(texts, start=1)]
    chunks = chunk_pages(pages)
    words_in = {word for text in texts for word in normalize(text).split()}
    words_out = {word for chunk in chunks for word in chunk.content.split()}
    for chunk in chunks:
        assert 1 <= chunk.page <= len(texts)
        assert chunk.content.strip()
        assert len(chunk.content) <= MAX_CHARS
    assert words_in <= words_out or not words_in

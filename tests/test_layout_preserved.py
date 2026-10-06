import pymupdf
import pytest

from pdfmachinator.document import Document


@pytest.fixture
def pdf(tmp_path):
    p = tmp_path / "in.pdf"
    d = pymupdf.open()
    pg = d.new_page()
    pg.insert_text((72, 100), "Hello vilag, ez egy proba szoveg.", fontsize=14)
    d.save(p)
    d.close()
    return p


def test_incremental_save_preserves_original(pdf):
    old = pdf.read_bytes()
    old_content = pymupdf.open(pdf)[0].read_contents()
    d = Document(str(pdf))
    d.add_text(0, pymupdf.Point(100, 200), ",", (1, 0, 0), (1, 1, 0))
    d.add_note(0, pymupdf.Point(300, 300), "megjegyzés", (1, 0.8, 0))
    d.add_highlight(0, pymupdf.Rect(60, 80, 300, 110), (1, 1, 0))
    d.add_circle(0, pymupdf.Rect(70, 80, 160, 110), (1, 0, 0))
    d.save()
    new = pdf.read_bytes()
    assert new[:len(old)] == old and len(new) > len(old)
    r = pymupdf.open(pdf)
    types = sorted(a.type[1] for a in r[0].annots())
    assert types == ["Circle", "FreeText", "Highlight", "Text"]
    assert r[0].read_contents() == old_content  # az oldaltartalom (tördelés) azonos


def test_undo_and_delete(pdf):
    d = Document(str(pdf))
    d.add_circle(0, pymupdf.Rect(70, 80, 160, 110), (1, 0, 0))
    assert d.undo()
    assert not list(d.page(0).annots())
    a = d.add_circle(0, pymupdf.Rect(70, 80, 160, 110), (1, 0, 0))
    d.delete(0, a)
    assert not list(d.page(0).annots())


def test_save_as_keeps_original_untouched(pdf, tmp_path):
    old = pdf.read_bytes()
    d = Document(str(pdf))
    d.add_circle(0, pymupdf.Rect(70, 80, 160, 110), (1, 0, 0))
    out = tmp_path / "out.pdf"
    d.save(str(out))
    assert pdf.read_bytes() == old
    new = out.read_bytes()
    assert new[:len(old)] == old and len(new) > len(old)
    assert [a.type[1] for a in pymupdf.open(out)[0].annots()] == ["Circle"]
    d.add_circle(0, pymupdf.Rect(10, 10, 40, 40), (0, 0, 1))
    d.save()  # most már az új fájlra ment
    assert len(list(pymupdf.open(out)[0].annots())) == 2
    assert pdf.read_bytes() == old


def test_text_background_can_be_cleared(pdf):
    d = Document(str(pdf))
    a = d.add_text(0, pymupdf.Point(100, 95), ",", (1, 0, 0), (1, 1, 0))

    def px():
        r = pymupdf.Rect(a.rect.x0, a.rect.y1 - 3, a.rect.x0 + 2, a.rect.y1)
        return d.page(0).get_pixmap(clip=r).pixel(0, 0)

    def near(c, ref):
        return all(abs(x - y) < 30 for x, y in zip(c, ref))

    assert near(px(), (255, 255, 0))
    d.set_text_bg(a, None)
    assert near(px(), (255, 255, 255))
    d.set_text_bg(a, (0, 1, 0))
    assert near(px(), (0, 255, 0))


def test_background_alpha_keeps_text_opaque(pdf):
    d = Document(str(pdf))
    a = d.add_text(0, pymupdf.Point(72, 95), "X", (1, 0, 0), (0, 0, 1), 0.5)
    assert d.text_bg_alpha(a) == 0.5
    r = pymupdf.Rect(a.rect.x0, a.rect.y1 - 3, a.rect.x0 + 2, a.rect.y1)
    c = d.page(0).get_pixmap(clip=r).pixel(0, 0)
    assert 100 < c[0] < 160 and c[2] == 255  # áttetsző kék a fehér lapon
    d.save()
    assert abs(Document(str(pdf)).text_bg_alpha(pymupdf.open(pdf)[0].annots().__next__()) - 0.5) < 1e-6

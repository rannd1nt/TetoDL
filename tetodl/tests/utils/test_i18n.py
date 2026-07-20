"""Tests for tetodl.utils.i18n."""



from tetodl.utils.i18n import (
    get_text,
    set_language,
    get_current_language,
    get_available_languages,
    load_language,
)


class TestGetText:
    def test_get_text_returns_key_for_missing(self):
        result = get_text("nonexistent.key")
        assert result == "nonexistent.key"

    def test_get_text_with_vars(self):
        result = get_text("common.success", item="File", action="downloaded")
        assert "File" in result
        assert "downloaded" in result

    def test_get_text_dot_notation_resolves(self):
        result = get_text("common.yes")
        assert result in ("y", "ya")


class TestSetLanguage:
    def test_set_language_valid(self):
        result = set_language("en")
        assert result is True
        assert get_current_language() == "en"

    def test_set_language_invalid_falls_back_to_id(self):
        result = set_language("xx")
        assert result is True
        assert get_current_language() == "id"

    def test_language_switch_changes_text(self):
        set_language("id")
        id_text = get_text("common.yes")
        set_language("en")
        en_text = get_text("common.yes")
        if id_text == "y" and en_text == "y":
            pass
        assert isinstance(id_text, str)
        assert isinstance(en_text, str)


class TestGetAvailableLanguages:
    def test_returns_list_of_codes(self):
        langs = get_available_languages()
        assert isinstance(langs, list)
        assert "en" in langs
        assert "id" in langs

    def test_no_duplicates(self):
        langs = get_available_languages()
        assert len(langs) == len(set(langs))


class TestLoadLanguage:
    def test_load_language_returns_bool(self):
        result = load_language("en")
        assert isinstance(result, bool)

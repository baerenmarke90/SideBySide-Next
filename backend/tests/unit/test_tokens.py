"""Token-Erzeugung und -Ablage."""

from __future__ import annotations

from sidebyside.auth.tokens import generate_token, hash_token, tokens_equal


class TestErzeugung:
    def test_token_sind_eindeutig(self) -> None:
        assert len({generate_token() for _ in range(1000)}) == 1000

    def test_token_ist_lang_genug(self) -> None:
        """32 Zufallsbytes, base64-kodiert - nicht zu erraten."""
        assert len(generate_token()) >= 40

    def test_token_ist_url_tauglich(self) -> None:
        for _ in range(50):
            token = generate_token()
            assert "/" not in token
            assert "+" not in token
            assert "=" not in token


class TestHash:
    def test_ist_stabil(self) -> None:
        token = generate_token()
        assert hash_token(token) == hash_token(token)

    def test_unterscheidet_sich_je_token(self) -> None:
        assert hash_token(generate_token()) != hash_token(generate_token())

    def test_gibt_den_token_nicht_preis(self) -> None:
        token = generate_token()
        assert token not in hash_token(token)

    def test_hat_die_laenge_der_spalte(self) -> None:
        """Die Spalte ist String(64) - ein laengerer Hash wuerde abgeschnitten
        und damit Kollisionen erzeugen."""
        assert len(hash_token(generate_token())) == 64


class TestVergleich:
    def test_erkennt_gleichheit(self) -> None:
        wert = hash_token(generate_token())
        assert tokens_equal(wert, wert)

    def test_erkennt_ungleichheit(self) -> None:
        assert not tokens_equal(hash_token(generate_token()), hash_token(generate_token()))

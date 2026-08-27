"""Netzwerkidentitaet fuer den anonymen Passkey-Abuse-Key."""

from sidebyside.auth.passkey_abuse import network_key


def test_ipv4_bleibt_pro_client_getrennt() -> None:
    assert network_key("198.51.100.10") == "ipv4:198.51.100.10"
    assert network_key("198.51.100.10") != network_key("198.51.100.11")


def test_ipv6_wird_auf_64_bit_netz_normalisiert() -> None:
    assert network_key("2001:db8:1234:5678::1") == network_key("2001:db8:1234:5678::ffff")
    assert network_key("2001:db8:1234:5678::1") != network_key("2001:db8:1234:5679::1")


def test_ipv4_mapped_ipv6_wird_wie_ipv4_behandelt() -> None:
    assert network_key("::ffff:198.51.100.10") == network_key("198.51.100.10")


def test_nicht_ip_peer_bleibt_an_seinen_bezeichner_gebunden() -> None:
    assert network_key("TestClient") == "peer:testclient"

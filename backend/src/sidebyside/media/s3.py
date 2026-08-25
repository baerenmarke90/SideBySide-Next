"""S3-kompatible Medienablage mit AWS Signature Version 4."""

from __future__ import annotations

import hashlib
import hmac
import io
from collections.abc import Buffer, Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import BinaryIO
from urllib.parse import quote, urlsplit

import httpx

from sidebyside.core.clock import now
from sidebyside.media.base import ByteSource, MediaStore, StoredObject
from sidebyside.media.presigned import SignedUpload

_SERVICE = "s3"
_ALGORITHM = "AWS4-HMAC-SHA256"
_REQUEST_TYPE = "aws4_request"
_UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD"
_MAX_PRESIGN_SECONDS = 7 * 24 * 60 * 60
_READ_CHUNK = 64 * 1024


def _aws_quote(value: str, *, keep_slash: bool = False) -> str:
    safe = "-_.~/" if keep_slash else "-_.~"
    return quote(value, safe=safe)


def _canonical_query(parameters: Mapping[str, str]) -> str:
    encoded = [(_aws_quote(key), _aws_quote(value)) for key, value in parameters.items()]
    encoded.sort()
    return "&".join(f"{key}={value}" for key, value in encoded)


def _normalize_header(value: str) -> str:
    return " ".join(value.strip().split())


class _ResponseReader(io.RawIOBase):
    """Binary reader over a streaming httpx response.

    The old adapter returned ``BytesIO(response.content)`` which necessarily
    buffered an entire untrusted object before the attachment limit could run.
    This reader keeps at most the requested bytes plus one provider chunk.

    Test/custom transports may hand httpx an already-buffered response even
    when the client requested ``stream=True``. In that case the bytes are
    already resident before this adapter sees them, so reusing that existing
    buffer does not weaken the real network path, which remains incremental.
    """

    def __init__(self, response: httpx.Response) -> None:
        super().__init__()
        self._response = response
        if response.is_stream_consumed:
            try:
                buffered = response.content
            except httpx.ResponseNotRead as error:
                response.close()
                raise OSError("S3 response body is unavailable.") from error
            self._chunks = iter((buffered,))
        else:
            self._chunks = response.iter_raw(_READ_CHUNK)
        self._buffer = bytearray()

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        if self.closed:
            raise ValueError("I/O operation on closed media stream.")
        if size == 0:
            return b""
        if size < -1:
            raise ValueError("invalid read size")

        if size == -1:
            output = bytearray(self._buffer)
            self._buffer.clear()
            for chunk in self._chunks:
                output.extend(chunk)
            return bytes(output)

        while len(self._buffer) < size:
            try:
                chunk = next(self._chunks)
            except StopIteration:
                break
            self._buffer.extend(chunk)

        result = bytes(self._buffer[:size])
        del self._buffer[:size]
        return result

    def readinto(self, buffer: Buffer, /) -> int:
        """Fill a writable buffer so ``BufferedReader`` can consume this raw stream."""
        target = memoryview(buffer).cast("B")
        chunk = self.read(len(target))
        target[: len(chunk)] = chunk
        return len(chunk)

    def close(self) -> None:
        if not self.closed:
            self._response.close()
        super().close()


class S3MediaStore(MediaStore):
    """Privater S3-Bucket hinter der MediaStore-Schnittstelle.

    Der Adapter verwendet ausschliesslich objektbezogene GET/PUT/HEAD/DELETE-
    Requests. ACL-Operationen gibt es bewusst nicht; die Bucket-Policy bleibt
    Sache des Betriebs und muss Public Access verbieten.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        region: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        session_token: str | None = None,
        client: httpx.Client | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        parsed = urlsplit(endpoint.rstrip("/"))
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("S3 endpoint must be an http(s) origin without credentials or path.")
        if not bucket or "/" in bucket:
            raise ValueError("S3 bucket must be a single non-empty bucket name.")
        if not region or not access_key_id or not secret_access_key:
            raise ValueError("S3 region and credentials are required.")

        self._endpoint = f"{parsed.scheme}://{parsed.netloc}"
        self._host = parsed.netloc.lower()
        self._region = region
        self._bucket = bucket
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._session_token = session_token
        self._client = client or httpx.Client(timeout=30.0, follow_redirects=False)
        self._clock = clock or now

    def _object_path(self, storage_key: str) -> str:
        if (
            not storage_key
            or storage_key.startswith("/")
            or any(part in {"", ".", ".."} for part in storage_key.split("/"))
        ):
            raise ValueError("Invalid storage key.")
        bucket = _aws_quote(self._bucket)
        key = _aws_quote(storage_key, keep_slash=True)
        return f"/{bucket}/{key}"

    def _url(self, storage_key: str) -> str:
        return f"{self._endpoint}{self._object_path(storage_key)}"

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _scope(self, date_stamp: str) -> str:
        return f"{date_stamp}/{self._region}/{_SERVICE}/{_REQUEST_TYPE}"

    def _signing_key(self, date_stamp: str) -> bytes:
        key_date = hmac.new(
            f"AWS4{self._secret_access_key}".encode(), date_stamp.encode(), hashlib.sha256
        ).digest()
        key_region = hmac.new(key_date, self._region.encode(), hashlib.sha256).digest()
        key_service = hmac.new(key_region, _SERVICE.encode(), hashlib.sha256).digest()
        return hmac.new(key_service, _REQUEST_TYPE.encode(), hashlib.sha256).digest()

    def _signature(self, string_to_sign: str, date_stamp: str) -> str:
        return hmac.new(
            self._signing_key(date_stamp), string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

    def _canonical_headers(self, headers: Mapping[str, str]) -> tuple[str, str]:
        normalized = {name.lower(): _normalize_header(value) for name, value in headers.items()}
        names = sorted(normalized)
        canonical = "".join(f"{name}:{normalized[name]}\n" for name in names)
        return canonical, ";".join(names)

    def _presign(
        self,
        method: str,
        storage_key: str,
        expires_in: timedelta,
        signed_headers: Mapping[str, str],
    ) -> str:
        seconds = int(expires_in.total_seconds())
        if expires_in != timedelta(seconds=seconds) or not 1 <= seconds <= _MAX_PRESIGN_SECONDS:
            raise ValueError("Invalid presigned URL lifetime.")

        moment = self._now()
        amz_date = moment.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = moment.strftime("%Y%m%d")
        scope = self._scope(date_stamp)

        headers = {"host": self._host, **signed_headers}
        canonical_headers, header_names = self._canonical_headers(headers)
        query: dict[str, str] = {
            "X-Amz-Algorithm": _ALGORITHM,
            "X-Amz-Credential": f"{self._access_key_id}/{scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(seconds),
            "X-Amz-SignedHeaders": header_names,
        }
        if self._session_token is not None:
            query["X-Amz-Security-Token"] = self._session_token
        canonical_query = _canonical_query(query)
        canonical_request = "\n".join(
            [
                method,
                self._object_path(storage_key),
                canonical_query,
                canonical_headers,
                header_names,
                _UNSIGNED_PAYLOAD,
            ]
        )
        string_to_sign = "\n".join(
            [
                _ALGORITHM,
                amz_date,
                scope,
                hashlib.sha256(canonical_request.encode()).hexdigest(),
            ]
        )
        signature = self._signature(string_to_sign, date_stamp)
        return f"{self._url(storage_key)}?{canonical_query}&X-Amz-Signature={signature}"

    def _request(
        self,
        method: str,
        storage_key: str,
        *,
        content: bytes = b"",
        content_type: str | None = None,
        stream: bool = False,
    ) -> httpx.Response:
        moment = self._now()
        amz_date = moment.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = moment.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(content).hexdigest()

        headers: dict[str, str] = {
            "host": self._host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        if content_type is not None:
            headers["content-type"] = content_type
            headers["cache-control"] = "private, no-store"
        if self._session_token is not None:
            headers["x-amz-security-token"] = self._session_token

        canonical_headers, header_names = self._canonical_headers(headers)
        canonical_request = "\n".join(
            [
                method,
                self._object_path(storage_key),
                "",
                canonical_headers,
                header_names,
                payload_hash,
            ]
        )
        scope = self._scope(date_stamp)
        string_to_sign = "\n".join(
            [
                _ALGORITHM,
                amz_date,
                scope,
                hashlib.sha256(canonical_request.encode()).hexdigest(),
            ]
        )
        signature = self._signature(string_to_sign, date_stamp)
        headers["authorization"] = (
            f"{_ALGORITHM} Credential={self._access_key_id}/{scope}, "
            f"SignedHeaders={header_names}, Signature={signature}"
        )

        try:
            request = self._client.build_request(
                method,
                self._url(storage_key),
                headers=headers,
                content=content,
            )
            return self._client.send(request, stream=stream)
        except httpx.HTTPError:
            # Kein Requestobjekt an den Aufrufer durchreichen: Authorization-
            # Header/Signatur duerfen auch in Fehlerlogs nicht auftauchen.
            raise OSError("S3 request failed.") from None

    @staticmethod
    def _require_success(response: httpx.Response, *, allow_not_found: bool = False) -> bool:
        if 200 <= response.status_code < 300:
            return True
        if allow_not_found and response.status_code == 404:
            response.close()
            return False
        response.close()
        raise OSError(f"S3 request failed with status {response.status_code}.")

    def put(self, storage_key: str, data: ByteSource, content_type: str) -> StoredObject:
        buffer = bytearray()
        while chunk := data.read(_READ_CHUNK):
            buffer.extend(chunk)
        payload = bytes(buffer)
        response = self._request("PUT", storage_key, content=payload, content_type=content_type)
        self._require_success(response)
        response.close()
        return StoredObject(storage_key=storage_key, size=len(payload), content_type=content_type)

    def open(self, storage_key: str) -> BinaryIO:
        response = self._request("GET", storage_key, stream=True)
        self._require_success(response)
        return io.BufferedReader(_ResponseReader(response), buffer_size=_READ_CHUNK)

    def delete(self, storage_key: str) -> None:
        response = self._request("DELETE", storage_key)
        self._require_success(response, allow_not_found=True)
        response.close()

    def exists(self, storage_key: str) -> bool:
        response = self._request("HEAD", storage_key)
        exists = self._require_success(response, allow_not_found=True)
        response.close()
        return exists

    def object_size(self, storage_key: str) -> int | None:
        """Read provider-declared size without downloading the object body."""
        response = self._request("HEAD", storage_key)
        if not self._require_success(response, allow_not_found=True):
            return None
        try:
            value = response.headers.get("content-length")
            if value is None:
                raise OSError("S3 HEAD response is missing Content-Length.")
            try:
                size = int(value)
            except ValueError:
                raise OSError("S3 HEAD response has an invalid Content-Length.") from None
            if size < 0:
                raise OSError("S3 HEAD response has an invalid Content-Length.")
            return size
        finally:
            response.close()

    def create_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in: timedelta,
    ) -> SignedUpload:
        headers = {
            "cache-control": "private, no-store",
            "content-type": content_type,
            "if-none-match": "*",
        }
        return SignedUpload(
            url=self._presign("PUT", storage_key, expires_in, headers),
            required_headers={
                "Cache-Control": "private, no-store",
                "Content-Type": content_type,
                "If-None-Match": "*",
            },
        )

    def create_read_url(self, storage_key: str, expires_in: timedelta) -> str:
        return self._presign("GET", storage_key, expires_in, {})

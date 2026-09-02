package de.sidebyside.next.cache

/** Ciphertext and the GCM IV it was produced with, kept together for decryption. */
data class EncryptedPayload(val ciphertext: ByteArray, val iv: ByteArray)

/**
 * Encrypts/decrypts `OWNER_ONLY` cache payloads with a key this device holds,
 * not one the cache layer manages itself. [ProductReadCache] never sees a key
 * or plaintext-at-rest decision — it only ever calls this boundary.
 */
interface ProtectedPayloadCipher {
    fun encrypt(plaintext: String): EncryptedPayload
    fun decrypt(payload: EncryptedPayload): String
}

package de.sidebyside.next.cache

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

private const val ANDROID_KEYSTORE = "AndroidKeyStore"
private const val TRANSFORMATION = "AES/GCM/NoPadding"
private const val GCM_TAG_LENGTH_BITS = 128
private const val KEY_SIZE_BITS = 256
private const val DEFAULT_KEY_ALIAS = "sidebyside_owner_only_read_cache"

/**
 * The M2-D18 Android decision: `OWNER_ONLY` cache bytes are encrypted with a
 * key protected by Android Keystore, using only the platform's own
 * `javax.crypto`/`android.security.keystore` APIs — no new cryptographic
 * dependency. The key is generated non-exportable and never leaves the
 * Keystore; only Keystore-mediated encrypt/decrypt operations cross this
 * boundary.
 *
 * Not exercised by the JVM unit test suite: Robolectric does not provide the
 * `AndroidKeyStore` provider, so [ProductReadCache]'s owner-only fallback
 * logic is proven there against a fake [ProtectedPayloadCipher] instead, and
 * this class itself only on a real device or emulator.
 */
class AndroidKeystoreProtectedPayloadCipher(
    private val keyAlias: String = DEFAULT_KEY_ALIAS,
) : ProtectedPayloadCipher {
    private fun keyStore(): KeyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }

    private fun secretKey(): SecretKey {
        val store = keyStore()
        (store.getKey(keyAlias, null) as? SecretKey)?.let { return it }

        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(keyAlias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(KEY_SIZE_BITS)
                .build(),
        )
        return generator.generateKey()
    }

    override fun encrypt(plaintext: String): EncryptedPayload {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey())
        val ciphertext = cipher.doFinal(plaintext.toByteArray(Charsets.UTF_8))
        return EncryptedPayload(ciphertext = ciphertext, iv = cipher.iv)
    }

    override fun decrypt(payload: EncryptedPayload): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(GCM_TAG_LENGTH_BITS, payload.iv))
        return String(cipher.doFinal(payload.ciphertext), Charsets.UTF_8)
    }
}

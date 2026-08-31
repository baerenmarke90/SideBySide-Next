package de.sidebyside.next.story

import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

/**
 * Holds Story attachment bytes for as long as they are worth holding.
 *
 * Three contract facts shape this. A `ReadDescriptor` expires, so the cache is
 * keyed by attachment id and never by the URL that happened to serve it. The
 * bytes are a couple's private photographs, so they stay in memory and are
 * never written to storage. And the Space can change under the session, so a
 * generation counter makes every result from the previous Space unusable
 * rather than merely stale.
 *
 * Concurrent requests for the same attachment share one read: a Story showing
 * the same image twice must not fetch it twice.
 *
 * The critical sections are short and non-suspending, so a plain lock is used
 * rather than a `Mutex`. That matters for [reset], which has to take effect at
 * the moment the Space changes — not whenever a coroutine gets around to it.
 */
class StoryImageStore(
    private val scope: CoroutineScope,
    private val budgetBytes: Int = DEFAULT_BUDGET_BYTES,
    private val load: suspend (StoryImageRef) -> ByteArray,
) {
    private val guard = Any()

    /** Insertion-ordered, so the oldest entry is the first to go. */
    private val cached = LinkedHashMap<UUID, ByteArray>()
    private var cachedBytes = 0

    private val inFlight = mutableMapOf<UUID, CompletableDeferred<ByteArray?>>()

    private var generation = 0

    /**
     * Reads one attachment, from memory where possible.
     *
     * Returns `null` when the read failed, so one unreadable image degrades to
     * a placeholder instead of taking the entry — or the Story — down with it.
     */
    suspend fun image(ref: StoryImageRef): ByteArray? {
        val attachmentId = ref.attachmentId
        // The lock covers the cache lookup and the in-flight registration, and
        // is released before waiting: holding it across a read would let one
        // slow image block every other one.
        val pending = synchronized(guard) {
            cached[attachmentId]?.let { return it }
            inFlight[attachmentId] ?: CompletableDeferred<ByteArray?>().also { started ->
                inFlight[attachmentId] = started
                val startedGeneration = generation
                scope.launch { fetch(ref, started, startedGeneration) }
            }
        }
        return pending.await()
    }

    private suspend fun fetch(
        ref: StoryImageRef,
        pending: CompletableDeferred<ByteArray?>,
        startedGeneration: Int,
    ) {
        val bytes = runCatching { load(ref) }.getOrNull()
        val usable = synchronized(guard) {
            inFlight.remove(ref.attachmentId)
            // The Space changed while this was in flight. The bytes belong to a
            // Space the couple has left, so they are dropped, not cached.
            val current = startedGeneration == generation
            if (current && bytes != null) {
                remember(ref.attachmentId, bytes)
            }
            current
        }
        pending.complete(if (usable) bytes else null)
    }

    /** Caller already holds [guard]. */
    private fun remember(attachmentId: UUID, bytes: ByteArray) {
        // An image larger than the whole budget would evict everything and then
        // still not fit; it is served but not kept.
        if (bytes.size > budgetBytes) return

        cached.remove(attachmentId)?.let { cachedBytes -= it.size }
        cached[attachmentId] = bytes
        cachedBytes += bytes.size

        val oldest = cached.keys.iterator()
        while (cachedBytes > budgetBytes && oldest.hasNext()) {
            val key = oldest.next()
            cachedBytes -= cached.getValue(key).size
            oldest.remove()
        }
    }

    /**
     * Forgets everything, and makes any read already in flight resolve to
     * nothing.
     *
     * Called when the session or the Space changes. Without the generation
     * bump, a read started against the previous Space could still complete and
     * leave one couple's photograph in memory while another couple is looking
     * at the screen.
     */
    fun reset() = synchronized(guard) {
        generation += 1
        cached.clear()
        cachedBytes = 0
        inFlight.clear()
    }

    internal fun cachedBytesForTest(): Int = synchronized(guard) { cachedBytes }

    private companion object {
        /**
         * Enough for a screenful of Story images without letting a long scroll
         * grow without bound.
         */
        const val DEFAULT_BUDGET_BYTES = 24 * 1024 * 1024
    }
}

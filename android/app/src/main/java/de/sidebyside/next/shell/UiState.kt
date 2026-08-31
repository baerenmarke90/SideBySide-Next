package de.sidebyside.next.shell

/**
 * The system states every product surface has to be able to show.
 *
 * Declared once so a screen cannot invent its own vocabulary, and so the
 * mapping from a server problem to a state lives in one place rather than in
 * each caller's `catch`.
 */
enum class UiStateKind {
    Loading,
    Empty,
    Error,
    Permission,
    Conflict,
    RateLimit,
    Offline,
}

/**
 * A problem the user can be told about.
 *
 * [retryable] decides whether a retry affordance is offered at all: retrying a
 * permission failure or a conflict just repeats the same answer.
 */
data class UiProblem(
    val kind: UiStateKind,
    val titleRes: Int,
    val bodyRes: Int,
    val retryable: Boolean,
)

package de.sidebyside.next.shell

import de.sidebyside.next.reference.R
import de.sidebyside.next.reference.ReferenceApiException
import java.io.IOException

/**
 * Turns a failure into something the user can act on.
 *
 * The mapping lives here rather than in each caller so the same server answer
 * always produces the same state, and so no raw server text reaches the user:
 * a ProblemDetails `detail` may name resources or internal reasons, and is
 * therefore never displayed.
 */
fun problemFor(throwable: Throwable): UiProblem = when (throwable) {
    // No connection is a state of the device, not an answer from the server.
    is IOException -> UiProblem(
        kind = UiStateKind.Offline,
        titleRes = R.string.state_offline_title,
        bodyRes = R.string.state_offline_body,
        retryable = true,
    )

    is ReferenceApiException -> problemForStatus(throwable.status)

    else -> UiProblem(
        kind = UiStateKind.Error,
        titleRes = R.string.state_unknown_title,
        bodyRes = R.string.state_unknown_body,
        retryable = true,
    )
}

private fun problemForStatus(status: Int?): UiProblem = when (status) {
    401 -> UiProblem(
        kind = UiStateKind.Permission,
        titleRes = R.string.state_session_title,
        bodyRes = R.string.state_session_body,
        retryable = false,
    )

    // 403 and 404 deliberately share a state. Confirming that a resource exists
    // but is forbidden would disclose its existence; the Information
    // Architecture requires unauthorized content not to be confirmed.
    403, 404 -> UiProblem(
        kind = UiStateKind.Permission,
        titleRes = R.string.state_permission_title,
        bodyRes = R.string.state_permission_body,
        retryable = false,
    )

    409, 412 -> UiProblem(
        kind = UiStateKind.Conflict,
        titleRes = R.string.state_conflict_title,
        bodyRes = R.string.state_conflict_body,
        retryable = false,
    )

    422 -> UiProblem(
        kind = UiStateKind.Error,
        titleRes = R.string.state_validation_title,
        bodyRes = R.string.state_validation_body,
        retryable = false,
    )

    429 -> UiProblem(
        kind = UiStateKind.RateLimit,
        titleRes = R.string.state_rate_limit_title,
        bodyRes = R.string.state_rate_limit_body,
        retryable = true,
    )

    in 500..599 -> UiProblem(
        kind = UiStateKind.Error,
        titleRes = R.string.state_server_title,
        bodyRes = R.string.state_server_body,
        retryable = true,
    )

    else -> UiProblem(
        kind = UiStateKind.Error,
        titleRes = R.string.state_unknown_title,
        bodyRes = R.string.state_unknown_body,
        retryable = true,
    )
}

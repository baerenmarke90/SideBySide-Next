package de.sidebyside.next.reference

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import de.sidebyside.next.design.SideBySideTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SideBySideTheme {
                ReferenceFlowRoute()
            }
        }
    }
}

@Composable
private fun ReferenceFlowRoute(referenceViewModel: ReferenceViewModel = viewModel()) {
    val state by referenceViewModel.uiState.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var imageSelectionEpoch by remember { mutableStateOf<Long?>(null) }
    val imagePicker = rememberLauncherForActivityResult(ActivityResultContracts.PickMultipleVisualMedia()) { uris ->
        val selectionEpoch = imageSelectionEpoch
        imageSelectionEpoch = null
        if (uris.isNotEmpty() && selectionEpoch != null) {
            scope.launch {
                val images = mutableListOf<SelectedImage>()
                var firstFailure: Throwable? = null
                uris.forEach { uri ->
                    runCatching { loadSelectedImage(context, uri) }
                        .onSuccess(images::add)
                        .onFailure { throwable ->
                            if (firstFailure == null) firstFailure = throwable
                        }
                }
                if (images.isNotEmpty()) {
                    referenceViewModel.selectImages(images, selectionEpoch)
                }
                firstFailure?.let { throwable ->
                    referenceViewModel.setImageSelectionError(throwable, selectionEpoch)
                }
            }
        }
    }

    ReferenceFlowScreen(
        state = state,
        onLogin = referenceViewModel::signIn,
        onLogout = {
            imageSelectionEpoch = null
            referenceViewModel.logout()
        },
        onPickImage = {
            referenceViewModel.beginImageSelection()?.let { selectionEpoch ->
                imageSelectionEpoch = selectionEpoch
                imagePicker.launch(
                    PickVisualMediaRequest.Builder()
                        .setMediaType(ActivityResultContracts.PickVisualMedia.ImageOnly)
                        .setOrderedSelection(true)
                        .build(),
                )
            }
        },
        onCreateMemory = referenceViewModel::createMemory,
        onRefreshStory = referenceViewModel::refreshStory,
        onRetryImage = referenceViewModel::retryImage,
        onRemoveImage = referenceViewModel::removeImage,
    )
}

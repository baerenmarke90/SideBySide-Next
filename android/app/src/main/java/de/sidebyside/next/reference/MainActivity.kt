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
    val imagePicker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        val selectionEpoch = imageSelectionEpoch
        imageSelectionEpoch = null
        if (uri != null && selectionEpoch != null) {
            scope.launch {
                runCatching { loadSelectedImage(context, uri) }
                    .onSuccess { image -> referenceViewModel.selectImage(image, selectionEpoch) }
                    .onFailure { throwable -> referenceViewModel.setImageError(throwable, selectionEpoch) }
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
                    PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly),
                )
            }
        },
        onCreateMemory = referenceViewModel::createMemory,
        onRefreshStory = referenceViewModel::refreshStory,
    )
}

# Phase 10: Flutter NVR App — Dual-Tab Architecture

**Status:** ✅ Completed  
**Date Completed:** July 20, 2026  
**Target Device:** Android (Samsung SM-S938B, `R5CY23R9DXR`)  
**Prerequisites:** Phase 9 complete (go2rtc configured, multi-class detection active, zones defined, `/api/v1/recordings` and `/api/v1/cameras` endpoints live)

---

## Objective

Evolve the Flutter app from a single-screen AI chat into a full "AI-First NVR" mobile application with a dual-tab architecture: an enhanced Smart AI tab and a new Classic NVR tab with live streaming and recording playback.

---

## Target Architecture

```
main.dart
└── MaterialApp
    └── MainScaffold (ConsumerStatefulWidget)
        ├── BottomNavigationBar (2 tabs)
        │   ├── Tab 0: SmartAIPage (enhanced chat_page.dart)
        │   │   ├── Chat message list (existing)
        │   │   ├── Event gallery with full-screen viewer (new)
        │   │   └── Inline video clip playback (new)
        │   └── Tab 1: ClassicNVRPage (new)
        │       ├── TabBar (2 sub-tabs)
        │       │   ├── LiveViewTab
        │       │   │   └── Camera grid (WebRTC streams)
        │       │   └── PlaybackTab
        │       │       ├── 24-hour timeline (CustomPainter)
        │       │       └── Video player (media_kit)
        │       └── FAB: Fullscreen toggle
        └── Settings (existing, accessible from AppBar)
```

---

## Step 10.1: Add Dependencies

**File:** `frigate_app/pubspec.yaml`

**Add packages:**

```yaml
dependencies:
  # Existing
  flutter_riverpod: ^2.5.1
  dio: ^5.4.0
  flutter_markdown: ^0.7.0

  # New — Live streaming
  flutter_webrtc: ^0.12.0

  # New — VOD playback
  media_kit: ^1.2.0
  media_kit_video: ^1.2.0
  media_kit_libs_android_video: ^1.0.5

  # New — Utilities
  intl: ^0.19.0          # Date/time formatting for timeline
  cached_network_image: ^3.3.0  # Better image caching for event thumbnails
```

**Notes:**
- `flutter_webrtc` provides `RTCPeerConnection` and `RTCVideoRenderer` for WebRTC streams.
- `media_kit` uses libmpv under the hood — the Android video libs package includes prebuilt binaries.
- `cached_network_image` replaces `Image.network` for better caching and loading states.

**Acceptance Criteria:**
- [ ] All new packages added to `pubspec.yaml`
- [ ] `flutter pub get` succeeds without errors
- [ ] `flutter analyze` passes with new dependencies

---

## Step 10.2: Scaffold Dual-Tab Architecture

**Goal:** Refactor `main.dart` and `chat_page.dart` into a `BottomNavigationBar` shell with two top-level tabs.

### 10.2.1: Create `MainScaffold` Widget

**File:** `frigate_app/lib/presentation/pages/main_scaffold.dart`

```dart
class MainScaffold extends ConsumerStatefulWidget {
  const MainScaffold({super.key});

  @override
  ConsumerState<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends ConsumerState<MainScaffold> {
  int _currentIndex = 0;

  final pages = [
    const ChatPage(),
    const ClassicNVRPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.smart_toy_outlined),
            selectedIcon: Icon(Icons.smart_toy),
            label: 'AI',
          ),
          NavigationDestination(
            icon: Icon(Icons.videocam_outlined),
            selectedIcon: Icon(Icons.videocam),
            label: 'NVR',
          ),
        ],
      ),
    );
  }
}
```

### 10.2.2: Update `main.dart`

Replace the home page from `ChatPage` to `MainScaffold`:

```dart
home: const MainScaffold(),
```

### 10.2.3: Create Placeholder `ClassicNVRPage`

**File:** `frigate_app/lib/presentation/pages/classic_nvr_page.dart`

Create a stub widget with a `TabBar` containing "Live" and "Playback" tabs. Fill with placeholder text for now.

**Acceptance Criteria:**
- [ ] `MainScaffold` created with `BottomNavigationBar` (2 tabs: AI, NVR)
- [ ] `main.dart` updated to use `MainScaffold` as home
- [ ] `ClassicNVRPage` stub created with `TabBar` (Live / Playback)
- [ ] Tab switching works without losing state (IndexedStack)
- [ ] Existing chat functionality preserved in Tab 0
- [ ] `flutter analyze` passes

---

## Step 10.3: Enhance Smart AI Tab — Full-Screen Image Gallery

**Goal:** Add a full-screen `PageView` with `InteractiveViewer` for pinch-to-zoom on event snapshots.

### 10.3.1: Create `FullScreenGallery` Widget

**File:** `frigate_app/lib/presentation/widgets/full_screen_gallery.dart`

```dart
class FullScreenGallery extends StatefulWidget {
  final List<String> imageUrls;
  final int initialIndex;

  const FullScreenGallery({
    super.key,
    required this.imageUrls,
    this.initialIndex = 0,
  });

  @override
  State<FullScreenGallery> createState() => _FullScreenGalleryState();
}
```

**Key implementation details:**
- Use `PageView.builder` for swipe between images
- Wrap each page in `InteractiveViewer` with `boundaryMargin: EdgeInsets.all(double.infinity)` for free pan/zoom
- `TransformationController` per page to reset zoom on double-tap
- Black background, app bar with close button and image counter ("3 / 12")
- Hero animation from thumbnail to full-screen

### 10.3.2: Wire Gallery to Event Thumbnails

**File:** `frigate_app/lib/presentation/widgets/chat_bubble.dart`

In `_EventGallery`, wrap each `ClipRRect` image in a `GestureDetector`:

```dart
GestureDetector(
  onTap: () {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => FullScreenGallery(
          imageUrls: rows.map((r) =>
            'http://$serverIp:5000/api/events/${r['id']}/snapshot.jpg'
          ).toList(),
          initialIndex: index,
        ),
      ),
    );
  },
  child: ClipRRect(...)
)
```

**Acceptance Criteria:**
- [ ] `FullScreenGallery` widget created with `PageView` + `InteractiveViewer`
- [ ] Pinch-to-zoom works (min scale 1.0, max scale 4.0)
- [ ] Swipe left/right navigates between event images
- [ ] Double-tap resets zoom
- [ ] Image counter shown in app bar
- [ ] Tapping an event thumbnail in chat opens the gallery at that image
- [ ] Back button / swipe down closes the gallery

---

## Step 10.4: Enhance Smart AI Tab — Inline Video Clip Playback

**Goal:** Add a play button on event cards that have clips (`has_clip == 1`), with inline playback.

### 10.4.1: Create `InlineClipPlayer` Widget

**File:** `frigate_app/lib/presentation/widgets/inline_clip_player.dart`

```dart
class InlineClipPlayer extends StatefulWidget {
  final String clipUrl;  // http://<serverIp>:5000/api/events/<id>/clip.mp4
  final String serverIp;

  const InlineClipPlayer({
    super.key,
    required this.clipUrl,
    required this.serverIp,
  });

  @override
  State<InlineClipPlayer> createState() => _InlineClipPlayerState();
}
```

**Key implementation details:**
- Use `media_kit` `Player` and `VideoController` for playback
- Show a play button overlay on the snapshot image
- On tap, replace the image with a video player (16:9 aspect ratio)
- Auto-play on load, muted by default
- Tap video to show/hide controls (play/pause, mute, fullscreen)
- Fullscreen button opens a `FullScreenGallery`-style video viewer

### 10.4.2: Update Event Gallery to Show Clip Button

**File:** `frigate_app/lib/presentation/widgets/chat_bubble.dart`

In `_EventGallery`, check `has_clip` from the event row and conditionally show a play button overlay:

```dart
final hasClip = row['has_clip'] == 1 || row['has_clip'] == true;
if (hasClip) {
  // Show play icon overlay on the image
  // On tap, navigate to InlineClipPlayer
}
```

**Note:** The `has_clip` field may not be in the current query columns. We need to either:
- (a) Update the LLM prompt to include `has_clip` in default SELECT queries, or
- (b) Make a separate API call to check clip availability, or
- (c) Always show the play button and handle 404 in the error builder

**Recommended:** Option (c) — always show play button, handle 404 gracefully.

**Acceptance Criteria:**
- [ ] `InlineClipPlayer` widget created using `media_kit`
- [ ] Play button overlay shown on event images
- [ ] Tapping play loads and plays the clip from `http://<serverIp>:5000/api/events/<id>/clip.mp4`
- [ ] Video plays muted by default with unmute toggle
- [ ] 404 / missing clip handled gracefully (snackbar: "Clip not available")
- [ ] Video player has play/pause and fullscreen controls

---

## Step 10.5: Build Classic NVR Tab — Live View (WebRTC)

**Goal:** Display a real-time camera grid using WebRTC via go2rtc.

### 10.5.1: Create `LiveStreamProvider`

**File:** `frigate_app/lib/presentation/providers/live_stream_provider.dart`

```dart
final cameraListProvider = FutureProvider<List<CameraInfo>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final response = await apiClient.getCameras();
  return response.map((c) => CameraInfo.fromJson(c)).toList();
});

class WebRTCStreamController {
  final String serverIp;
  final String cameraName;
  RTCPeerConnection? _pc;
  RTCVideoRenderer? _renderer;

  Future<RTCVideoRenderer> startStream() async {
    // 1. Create RTCPeerConnection
    // 2. Add transceiver (video: recvonly, audio: recvonly)
    // 3. Create SDP offer
    // 4. POST offer to http://<serverIp>:8555/ (go2rtc WebRTC endpoint)
    // 5. Set remote description from SDP answer
    // 6. Create renderer and attach to remote stream
    // 7. Return renderer
  }

  void stopStream() {
    // Close peer connection and dispose renderer
  }
}
```

### 10.5.2: Create `LiveViewTab` Widget

**File:** `frigate_app/lib/presentation/pages/live_view_tab.dart`

```dart
class LiveViewTab extends ConsumerStatefulWidget {
  const LiveViewTab({super.key});

  @override
  ConsumerState<LiveViewTab> createState() => _LiveViewTabState();
}
```

**Key implementation details:**
- Fetch camera list from `/api/v1/cameras` via `cameraListProvider`
- `GridView.builder` with `SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2)`
- Each cell: `AspectRatio` + `RTCVideoView` (or loading indicator while connecting)
- Single-camera fullscreen: tap a cell → navigate to full-screen `RTCVideoView`
- Auto-dispose stream controllers when tab is not visible (lifecycle management)
- Show camera name overlay and connection status indicator (connecting/connected/error)

### 10.5.3: WebRTC SDP Exchange Protocol

The go2rtc WebRTC endpoint expects a POST with SDP offer:

```
POST http://<serverIp>:8555/
Content-Type: application/sdp

<SDP offer body>
```

Response: `200 OK` with `Content-Type: application/sdp` containing the SDP answer.

**Alternative (if port 8555 is blocked):** Use the Frigate proxied endpoint:
```
POST http://<serverIp>:5000/api/webrtc?camera=cam1
Content-Type: application/json

{"sdp": "<base64-encoded-SDP-offer>", "type": "offer"}
```

**Acceptance Criteria:**
- [ ] `WebRTCStreamController` class created with `startStream()` / `stopStream()`
- [ ] SDP offer created and POSTed to go2rtc endpoint
- [ ] SDP answer received and set as remote description
- [ ] `RTCVideoRenderer` displays live video stream
- [ ] `LiveViewTab` shows camera grid (2 columns)
- [ ] Tapping a camera cell opens full-screen live view
- [ ] Streams are properly disposed when navigating away (no memory leaks)
- [ ] Connection status indicator shows connecting → connected
- [ ] Error handling for connection failures (retry button)

---

## Step 10.6: Build Classic NVR Tab — VOD Playback

**Goal:** Timeline-based browsing and playback of 24/7 recorded footage.

### 10.6.1: Create `RecordingListProvider`

**File:** `frigate_app/lib/presentation/providers/recording_provider.dart`

```dart
final recordingListProvider =
    FutureProvider.family<List<RecordingSegment>, RecordingQuery>((ref, query) async {
  final apiClient = ref.watch(apiClientProvider);
  return apiClient.getRecordings(
    camera: query.camera,
    date: query.date,
    hour: query.hour,
  );
});
```

### 10.6.2: Create `TimelineWidget`

**File:** `frigate_app/lib/presentation/widgets/timeline_widget.dart`

```dart
class TimelineWidget extends StatefulWidget {
  final String camera;
  final String date;  // YYYY-MM-DD
  final Function(RecordingSegment) onSegmentSelected;

  const TimelineWidget({
    super.key,
    required this.camera,
    required this.date,
    required this.onSegmentSelected,
  });
}
```

**Key implementation details:**
- `CustomPainter` draws a horizontal 24-hour bar (0:00 to 24:00)
- Color-coded segments:
  - Blue: continuous recording (motion or always-on)
  - Orange: segments with detected objects (`objects > 0`)
  - Gray: gaps (no recording)
- Current time indicator (red vertical line)
- Hour markers (0, 6, 12, 18, 24) with labels
- Tap on a segment → call `onSegmentSelected(segment)` → starts playback
- Draggable scrubber to seek to a specific time
- Horizontal scroll for precision (or pinch to zoom on the timeline)

### 10.6.3: Create `PlaybackTab` Widget

**File:** `frigate_app/lib/presentation/pages/playback_tab.dart`

```dart
class PlaybackTab extends ConsumerStatefulWidget {
  const PlaybackTab({super.key});

  @override
  ConsumerState<PlaybackTab> createState() => _PlaybackTabState();
}
```

**Key implementation details:**
- Top: Camera selector dropdown (from `cameraListProvider`)
- Middle: `media_kit` video player (`Video` widget from `media_kit_video`)
- Bottom: `TimelineWidget` for the selected date
- Date picker: `showDatePicker` to select the recording date
- Segment chaining:
  - When current segment finishes, automatically fetch and play the next segment
  - Use `Player.stream.completed` listener to trigger next segment
  - Build a playlist from the recording list for the selected hour
- Playback URL: `http://<serverIp>:5000${segment.path}` (path from API response)

### 10.6.4: Segment Chaining Logic

```dart
void _playSegment(int index) {
  if (index >= _segments.length) {
    // Move to next hour's segments
    _loadHour(_currentHour + 1);
    return;
  }

  final segment = _segments[index];
  final url = 'http://$serverIp:5000${segment.path}';
  _player.open(Media(url));

  _player.stream.completed.listen((completed) {
    if (completed) {
      _playSegment(index + 1);  // Auto-advance to next segment
    }
  });
}
```

**Acceptance Criteria:**
- [ ] `recordingListProvider` fetches segments from `/api/v1/recordings`
- [ ] `TimelineWidget` renders 24-hour bar with color-coded segments
- [ ] Tapping a timeline segment starts playback of that recording
- [ ] `media_kit` player displays video from `http://<serverIp>:5000/recordings/...`
- [ ] Segment chaining: when one 10s segment ends, the next plays automatically
- [ ] Date picker allows selecting different recording dates
- [ ] Camera selector allows switching between cameras
- [ ] Playback controls: play/pause, seek, speed control
- [ ] Timeline shows current playback position

---

## Step 10.7: Polish and Integration

**Goal:** Final integration, error handling, and UX polish.

### 10.7.1: Error Handling
- WebRTC connection failure → show retry button with error message
- VOD segment 404 → skip to next segment, show brief toast
- API endpoint unreachable → show offline banner with retry
- Camera list empty → show "No cameras configured" message

### 10.7.2: Performance
- Use `AutomaticDisposeProvider` for stream controllers to free resources
- Limit live grid to 4 simultaneous WebRTC connections
- Pre-fetch next segment URL during current playback for seamless chaining
- Use `cached_network_image` for event thumbnails with placeholder and error widgets

### 10.7.3: UX Polish
- Smooth tab transitions (no flicker on switch)
- Loading states for all async operations (skeletons or spinners)
- Dark theme consistency across all new screens
- Persian localization for new labels (زنده, پخش, دوربین, خط زمان)
- Haptic feedback on timeline segment tap

**Acceptance Criteria:**
- [ ] All error states handled with user-friendly messages
- [ ] No memory leaks when switching tabs (streams disposed properly)
- [ ] Dark theme applied to all new widgets
- [ ] Persian labels for all new UI elements
- [ ] `flutter analyze` passes with zero issues
- [ ] App runs on device `R5CY23R9DXR` without crashes

---

## Summary Checklist

| Step | Description | Type | Status |
|------|-------------|------|--------|
| 10.1 | Add dependencies (flutter_webrtc, media_kit, etc.) | pubspec.yaml | [x] |
| 10.2 | Scaffold dual-tab architecture (BottomNavigationBar) | Dart code | [x] |
| 10.3 | Full-screen image gallery (PageView + InteractiveViewer) | Dart code | [x] |
| 10.4 | Inline video clip playback (media_kit) | Dart code | [x] |
| 10.5 | Live View tab — WebRTC streaming (flutter_webrtc) | Dart code | [x] |
| 10.6 | VOD Playback tab — timeline + segment chaining (media_kit) | Dart code | [x] |
| 10.7 | Polish, error handling, Persian localization | Dart code | [x] |

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/playback_params.dart';

class NavigationState {
  final int mainTabIndex;
  final int nvrSubTabIndex;
  final PlaybackParams? playbackParams;

  NavigationState({
    this.mainTabIndex = 0,
    this.nvrSubTabIndex = 0,
    this.playbackParams,
  });

  NavigationState copyWith({
    int? mainTabIndex,
    int? nvrSubTabIndex,
    PlaybackParams? playbackParams,
  }) {
    return NavigationState(
      mainTabIndex: mainTabIndex ?? this.mainTabIndex,
      nvrSubTabIndex: nvrSubTabIndex ?? this.nvrSubTabIndex,
      playbackParams: playbackParams ?? this.playbackParams,
    );
  }
}

class NavigationNotifier extends Notifier<NavigationState> {
  @override
  NavigationState build() {
    return NavigationState();
  }

  void navigateToPlayback(PlaybackParams params) {
    state = NavigationState(
      mainTabIndex: 1,
      nvrSubTabIndex: 1,
      playbackParams: params,
    );
  }

  void setMainTab(int index) {
    state = state.copyWith(mainTabIndex: index);
  }

  void setNvrSubTab(int index) {
    state = state.copyWith(nvrSubTabIndex: index);
  }

  void clearPlaybackParams() {
    state = state.copyWith(playbackParams: null);
  }
}

final navigationProvider =
    NotifierProvider<NavigationNotifier, NavigationState>(NavigationNotifier.new);
